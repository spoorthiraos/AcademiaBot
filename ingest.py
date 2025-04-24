import os
import argparse
from utils import extract_text_from_file, chunk_text, create_embeddings, ensure_collection_exists
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Base data path (Windows absolute path)
BASE_DATA_PATH = r"C:\Users\spoor\Desktop\project-bolt-sb1-n4rrfyud\project\data"

def ingest_documents(directory: str, use_case: str) -> bool:
    """
    Ingest documents from a directory into a ChromaDB collection for a specific use case.
    """
    collection_name = f"{use_case}_docs"
    
    collection = ensure_collection_exists(collection_name)
    success = False

    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)

        if os.path.isdir(file_path):
            continue

        text = extract_text_from_file(file_path)
        if not text:
            logger.warning(f"\n\nSkipping {filename}: Failed to extract text\n\n")
            continue

        chunks = chunk_text(text)
        metadata_list = [{'source': filename, 'chunk': i, 'use_case': use_case} for i in range(len(chunks))]

        if create_embeddings(chunks, metadata_list, collection_name):
            logger.info(f"\n\nIngested {filename} into {collection_name}\n\n")
            success = True
        else:
            logger.error(f"\n\nFailed to ingest {filename}\n\n")

    return success

def main():
    use_cases = [
        "general", 
        "placement_related", 
        "semester_related", 
        "technical_support", 
        "department_specific", 
        "student_clubs_and_events"
    ]

    for use_case in use_cases:
        use_case_dir = os.path.join(BASE_DATA_PATH, use_case)

        if os.path.exists(use_case_dir) and os.path.isdir(use_case_dir):
            logger.info(f"\nIngesting documents for use case: {use_case}\n")
            if ingest_documents(use_case_dir, use_case):
                logger.info(f"\nSuccessfully ingested documents for {use_case}\n")
            else:
                logger.warning(f"\nNo documents ingested for {use_case}\n")
        else:
            logger.error(f"\nDirectory not found for use case: {use_case}\n")

    logger.info("\nDocument ingestion complete\n")

if __name__ == "__main__":
    main()
