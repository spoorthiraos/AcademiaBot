import ollama
from typing import List, Dict, Any

# Predefined use cases
USECASES = [
    "general", 
    "placement_related", 
    "semester_related", 
    "technical_support", 
    "department_specific", 
    "student_clubs_and_events"
]

def classify_use_case(question: str) -> str:
    """
    Classify a user question into a predefined use case category.
    
    Args:
        question: The user's question as a string
        
    Returns:
        The classified use case as a string
    """
    try:
        # Prepare the prompt for classification
        prompt = f"""
        Classify the following question into exactly one of these categories:
        - general: For general questions about the institution or academic life
        - placement_related: For questions about job placements, internships, or career services
        - semester_related: For questions about courses, schedules, exams, or academic calendar
        - technical_support: For questions about IT services, systems, or technical issues
        - department_specific: For questions related to specific academic departments
        - student_clubs_and_events: For questions about student organizations or campus events
        
        Question: "{question}"
        
        Respond with ONLY the category name, nothing else.
        """
        
        # Call Ollama for classification
        response = ollama.chat(model='llama3.2', messages=[
            {"role": "system", "content": "You are a helpful classifier assistant. Classify questions into predefined categories. Only respond with the category name, nothing else."},
            {"role": "user", "content": prompt}
        ])
        
        # Extract the classification result
        result = response['message']['content'].strip().lower()
        
        # Map to valid use case
        for use_case in USECASES:
            if use_case in result:
                return use_case
        
        # Default to general if no match is found
        return "general"
        
    except Exception as e:
        print(f"Error in classification: {e}")
        return "general"  # Default to general on error