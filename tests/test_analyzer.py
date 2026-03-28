import pytest
import json
from unittest.mock import MagicMock, patch
from execution.gemini_analyzer import (
    analyze_input,
    InsightResponse,
    Entity,
    Verification,
)


# ----------------------------------------------------------------------------
# SCHEMA VALIDATION TESTS
# ----------------------------------------------------------------------------
def test_insight_response_schema():
    """Verify the Pydantic model correctly validates valid and invalid data."""
    valid_data = {
        "category": "Traffic",
        "summary": "Vehicle accident on Main St.",
        "entities": [{"name": "Main St.", "type": "Location", "value": "Primary"}],
        "verification": {"status": "Verified", "notes": "Consistent with local feeds."},
        "insights": ["Avoid Main St. for 2 hours."],
        "confidence_score": 0.95,
    }

    response = InsightResponse(**valid_data)
    assert response.category == "Traffic"
    assert response.confidence_score == 0.95
    assert len(response.entities) == 1


def test_invalid_schema():
    """Ensure Pydantic catches missing required fields."""
    invalid_short_data = {"category": "News"}
    with pytest.raises(Exception):
        InsightResponse(**invalid_short_data)


# ----------------------------------------------------------------------------
# MOCKED EXECUTION TESTS
# ----------------------------------------------------------------------------
@patch("google.generativeai.GenerativeModel")
def test_analyze_input_success(mock_model_class):
    """Test successful API interaction and validation via mocking."""
    # Setup the mock model and response
    mock_model_instance = MagicMock()
    mock_model_class.return_value = mock_model_instance

    mock_response = MagicMock()
    mock_response.text = json.dumps(
        {
            "category": "General",
            "summary": "Mock test summary.",
            "entities": [],
            "verification": {"status": "Verified", "notes": "Mock data is consistent."},
            "insights": ["Insight 1"],
            "confidence_score": 1.0,
        }
    )
    mock_model_instance.generate_content.return_value = mock_response

    # Execute the analyzer logic
    result = analyze_input("Some messy raw data", "text")

    # Assertions
    assert "error" not in result
    assert result["category"] == "General"
    assert result["insights"][0] == "Insight 1"
    assert mock_model_instance.generate_content.called


@patch("google.generativeai.GenerativeModel")
def test_analyze_input_api_error(mock_model_class):
    """Ensure the system handles API-level exceptions gracefully."""
    # Setup mock to raise an exception
    mock_model_instance = MagicMock()
    mock_model_class.return_value = mock_model_instance
    mock_model_instance.generate_content.side_effect = Exception("API Quota Exceeded")

    result = analyze_input("Test data", "text")

    assert result["status"] == "Failed"
    assert "API Quota Exceeded" in result["error"]
