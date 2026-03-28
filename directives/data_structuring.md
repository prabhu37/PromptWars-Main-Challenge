# Directive: Unstructured Data Structuring & Insight Extraction

## Goal
Transform messy, unstructured real-world inputs (text snippets, images, audio transcripts, sensor data) into a verified, structured JSON format with actionable insights.

## Input Types
- **Text**: Messy notes, news feeds, chat logs, medical records.
- **Images**: Photos of documents, scenes, traffic conditions, medical scans.
- **Audio**: Voice memos, emergency calls, recorded updates.

## Processing Steps
1. **Identify Category**: Determine if the input is Medical, Traffic, Weather, News, or General.
2. **Extract Entities**: Pull out names, locations, dates, values, and critical status markers.
3. **Verify Integrity**: Cross-reference internal consistency. Flag ambiguities or missing critical data.
4. **Synthesize Insights**: Provide 3-5 high-level actionable takeaways.
5. **Assign Confidence**: Rate the extraction confidence from 0.0 to 1.0.

## Output Format (JSON)
The execution tool MUST return a JSON object adhering to this schema:

```json
{
  "category": "String (Medical | Traffic | Weather | News | General)",
  "summary": "String (Brief one-sentence overview)",
  "entities": [
    {
      "name": "String",
      "type": "String",
      "value": "Any"
    }
  ],
  "verification": {
    "status": "String (Verified | Incomplete | Ambiguous)",
    "notes": "String"
  },
  "insights": [
    "String (Actionable insight 1)",
    "String (Actionable insight 2)"
  ],
  "confidence_score": "Float (0.0 - 1.0)"
}
```

## Constraints
- Do not hallucinate data that isn't present.
- If an image is provided, describe the visual evidence for the insights.
- If audio is provided, mention specific keywords heard.
