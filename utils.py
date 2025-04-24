import os
import pypdf
import pandas as pd
import chromadb
from chromadb.config import Settings
import json
import uuid
from typing import List, Dict, Any, Optional
from better_profanity import profanity
import logging
# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Create the chroma directory if it doesn't exist
os.makedirs('chroma', exist_ok=True)

# Initialize ChromaDB client with persistence
chroma_client = chromadb.PersistentClient(path="./chroma")

profanity.load_censor_words()

def is_clean_text(text):
    clean = not profanity.contains_profanity(text)
    if not clean:
        logger.warning("\n\nProfanity detected in the text.\n\n")
    return clean

# Ensure collections exist
def ensure_collection_exists(collection_name: str):
    """Ensure the collection exists in ChromaDB."""
    try:
        collection = chroma_client.get_collection(name=collection_name)
        logger.info(f"\n\nCollection '{collection_name}' already exists.\n\n")
        return collection
    except Exception as e:
        logger.info(f"\n\nCollection '{collection_name}' does not exist. Creating it now.\n\n")
        return chroma_client.create_collection(name=collection_name)

# Initialize all required collections
def initialize_collections():
    """Initialize all required collections for the chatbot."""
    collections = [
        "general_docs", 
        "placement_docs", 
        "semester_docs", 
        "technical_support_docs", 
        "department_docs", 
        "student_clubs_docs",
        "user_files"
    ]
    
    for collection in collections:
        ensure_collection_exists(collection)

# Call this function to ensure collections exist
initialize_collections()

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file."""
    text = ""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        logger.info(f"\n\nText extracted from PDF: {file_path}\n\n")

    except Exception as e:
        logger.error(f"\n\nError extracting text from PDF {file_path}: {e}\n\n")
    return text

def extract_text_from_txt(file_path: str) -> str:
    """Extract text from a TXT file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
        logger.info(f"\n\nText extracted from TXT: {file_path}\n\n")

    except Exception as e:
        logger.error(f"\n\nError extracting text from TXT {file_path}: {e}\n\n")
        return ""

def extract_text_from_excel(file_path: str) -> str:
    """Extract text from an Excel file."""
    try:
        dfs = pd.read_excel(file_path, sheet_name=None)
        text = ""
        for sheet_name, df in dfs.items():
            text += f"Sheet: {sheet_name}\n"
            text += df.to_string(index=False) + "\n\n"
        logger.info(f"\n\nText extracted from Excel: {file_path}\n\n")
        return text
    except Exception as e:
        logger.error(f"\n\nError extracting text from Excel {file_path}: {e}\n\n")
        return ""

def extract_text_from_file(file_path: str) -> str:
    """Extract text from a file based on its extension."""
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext == '.txt':
        return extract_text_from_txt(file_path)
    elif ext in ['.xlsx', '.xls']:
        return extract_text_from_excel(file_path)
    else:
        logger.warning(f"\n\nUnsupported file type: {file_path}\n\n")
        return ""

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Split text into chunks with overlap."""
    chunks = []
    if not text:
        logger.warning("\n\nEmpty text passed for chunking.\n\n")
        return chunks
    
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = min(start + chunk_size, text_length)
        if end < text_length and end - start < chunk_size:
            end = text_length
            
        chunk = text[start:end]
        chunks.append(chunk)
        
        if end == text_length:
            break
            
        # Move the start position for the next chunk, considering overlap
        start = end - overlap
    logger.info(f"\n\nText chunked into {len(chunks)} parts.\n\n")
    return chunks

def create_embeddings(text_chunks: List[str], metadata_list: List[Dict], collection_name: str) -> bool:
    """Create embeddings from text chunks and add to ChromaDB collection."""
    if not text_chunks:
        logger.warning(f"\n\nNo text chunks to create embeddings for collection {collection_name}.\n\n")
        return False
    
    collection = ensure_collection_exists(collection_name)
    
    # Generate unique IDs for each chunk
    ids = [str(uuid.uuid4()) for _ in range(len(text_chunks))]
    
    # Add documents to collection
    collection.add(
        documents=text_chunks,
        metadatas=metadata_list,
        ids=ids
    )
    logger.info(f"\n\nEmbeddings created and added to collection '{collection_name}' with {len(text_chunks)} chunks.\n\n")
    return True

def get_relevant_context(question: str, collection_name: str, n_results: int = 3) -> str:
    """Get relevant context for a question from a ChromaDB collection."""
    collection = ensure_collection_exists(collection_name)
    
    # Query the collection
    results = collection.query(
        query_texts=[question],
        n_results=n_results
    )
    
    # Combine the documents into a single context string
    context = ""
    if results and 'documents' in results and results['documents']:
        for doc in results['documents'][0]:
            context += doc + "\n\n"
    
    return context

def save_upload_file(file_path: str, collection_name: str) -> bool:
    """Process an uploaded file and save it to ChromaDB."""
    try:
        # Extract text from file
        text = extract_text_from_file(file_path)
        if not text:
            return False
        
        # Split text into chunks
        chunks = chunk_text(text)
        
        # Create metadata for each chunk
        file_name = os.path.basename(file_path)
        metadata_list = [{'source': file_name, 'chunk': i} for i in range(len(chunks))]
        
        # Create embeddings and add to collection
        return create_embeddings(chunks, metadata_list, collection_name)
    
    except Exception as e:
        logger.error(f"\n\nError processing file: {e}\n\n")
        return False