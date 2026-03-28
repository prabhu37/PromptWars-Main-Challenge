import os
import json
import logging
from typing import List, Optional, Union, Any, Dict
from pydantic import BaseModel, Field, ValidationError
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image

# ----------------------------------------------------------------------------
# LOGGING CONFIGURATION
# ----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------------
# ENVIRONMENT SETUP
# ----------------------------------------------------------------------------
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY not found in environment variables.")
    raise ValueError("GEMINI_API_KEY not found in .env file")

genai.configure(api_key=GEMINI_API_KEY)


# ----------------------------------------------------------------------------
# DATA MODELS (Pydantic)
# ----------------------------------------------------------------------------
class Entity(BaseModel):
    name: str = Field(..., description="Name of the entity found.")
    type: str = Field(..., description="The category of the entity.")
    value: Any = Field(
        ..., description="The value or additional info associated with the entity."
    )


class Verification(BaseModel):
    status: str = Field(..., description="Status (Verified | Incomplete | Ambiguous).")
    notes: str = Field(
        ..., description="Supporting reasoning for the verification status."
    )


class InsightResponse(BaseModel):
    category: str = Field(
        ...,
        description="Primary domain (Medical | Traffic | Weather | News | General).",
    )
    summary: str = Field(..., description="High-level summary of the input.")
    entities: List[Entity] = Field(
        default_factory=list, description="Extracted entities."
    )
    verification: Verification = Field(..., description="Integrity assessment.")
    insights: List[str] = Field(
        default_factory=list, description="Actionable insights."
    )
    confidence_score: float = Field(
        ..., ge=0, le=1, description="Confidence level (0-1)."
    )


# ----------------------------------------------------------------------------
# CORE EXECUTION LOGIC
# ----------------------------------------------------------------------------
def get_directive(path: str) -> str:
    """Reads the instruction set from a markdown file."""
    try:
        with open(path, "r") as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Directive file not found at {path}")
        raise


def analyze_input(
    data: Union[str, Image.Image, Any],
    input_type: str,
    directive_path: str = "directives/data_structuring.md",
    model_id: str = "gemini-flash-latest",
) -> Dict[str, Any]:
    """
    Orchestrates the Gemini API call using the defined directive and validates output.

    Args:
        data: The input data (string for text, PIL Image for image, or File object for audio).
        input_type: 'text', 'image', or 'audio'.
        directive_path: Path to the markdown directive.
        model_id: The Gemini model identifier to use.

    Returns:
        Dict containing the structured analysis or an error object.
    """
    logger.info(f"Starting analysis for input type: {input_type} using {model_id}")

    try:
        directive = get_directive(directive_path)
    except Exception as e:
        return {"error": f"Failed to load directive: {str(e)}", "status": "Failed"}

    # Selection logic for the model
    model = genai.GenerativeModel(
        model_name=model_id,
        generation_config={"response_mime_type": "application/json"},
    )

    prompt_parts = [
        directive,
        f"\n\nInput type confirmed as: {input_type.upper()}\n",
        "Process the following input and return ONLY the structured JSON object as specified in the directive above.",
    ]

    # Map the data to the prompt
    if input_type == "text":
        prompt_parts.append(f"\nRAW INPUT DATA:\n{data}")
    else:
        # Handle images and audio files (Gemini processes these directly)
        prompt_parts.append(data)

    try:
        response = model.generate_content(prompt_parts)
        text_response = response.text.strip()

        # Parse and validate with Pydantic
        raw_json = json.loads(text_response)
        validated_data = InsightResponse(**raw_json)

        logger.info(f"Successfully processed and validated {input_type} analysis.")
        return validated_data.model_dump()

    except ValidationError as ve:
        logger.error(f"Schema Validation Error: {ve.json()}")
        return {
            "error": "The AI response did not match the required schema.",
            "details": ve.errors(),
            "status": "Failed",
            "confidence_score": 0.0,
        }
    except Exception as e:
        logger.exception("Unexpected error during Gemini analysis.")
        return {"error": str(e), "status": "Failed", "confidence_score": 0.0}


if __name__ == "__main__":
    # Internal test block for deterministic checking
    test_text = "Accident on Main St. and 5th Ave. Ambulance arriving. Traffic backed up for 2 miles."
    result = analyze_input(test_text, "text")
    print(json.dumps(result, indent=2))
