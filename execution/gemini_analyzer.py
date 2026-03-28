import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image
import io

# Load environment variables
load_dotenv()

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")

genai.configure(api_key=api_key)

def get_directive(path):
    with open(path, 'r') as f:
        return f.read()

def analyze_input(data, input_type, directive_path="directives/data_structuring.md"):
    """
    Orchestrates the Gemini API call using the defined directive.
    
    Args:
        data: The input data (string for text/audio transcript, or PIL Image, or binary for audio)
        input_type: 'text', 'image', or 'audio'
        directive_path: Path to the markdown directive
    """
    directive = get_directive(directive_path)
    
    # Selection logic for the model
    # Switching to gemini-2.0-flash as gemini-1.5-flash was reporting 404
    model = genai.GenerativeModel('gemini-2.0-flash',
                                 generation_config={"response_mime_type": "application/json"})
    
    prompt_parts = [
        directive,
        f"\n\nInput type confirmed as: {input_type.upper()}\n",
        "Process the following input and return ONLY the structured JSON object as specified in the directive above."
    ]

    if input_type == 'text':
        prompt_parts.append(f"\nRAW INPUT DATA:\n{data}")
    elif input_type == 'image':
        prompt_parts.append(data) # PIL image object
    elif input_type == 'audio':
        # Assuming data is a file path or bytes to be uploaded
        # For simplicity in this script, we expect data as processed bytes/path
        # but let's assume we pass the Gemini File API object or similar
        prompt_parts.append(data)
    
    try:
        response = model.generate_content(prompt_parts)
        # Parse the JSON response
        structured_data = json.loads(response.text)
        return structured_data
    except Exception as e:
        return {
            "error": str(e),
            "status": "Failed",
            "confidence_score": 0.0
        }

if __name__ == "__main__":
    # Test block
    test_text = "Accident on Main St. and 5th Ave. Ambulance arriving. Traffic backed up for 2 miles."
    print(json.dumps(analyze_input(test_text, 'text'), indent=2))
