import json
import re

def safe_json_loads(llm_output: str):
    if not llm_output or not isinstance(llm_output, str):
        raise ValueError("Invalid LLM output")

    # Remove common prefixes
    cleaned = llm_output.strip()

    # Remove ```json fences
    cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"```$", "", cleaned)

    # Remove leading 'json' or 'JSON'
    cleaned = re.sub(r"^\s*json\s*", "", cleaned, flags=re.IGNORECASE)

    # Remove leading slash
    cleaned = cleaned.lstrip("/")

    # Extract first JSON object or array
    match = re.search(r"(\{.*\}|\[.*\])", cleaned, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found")

    json_str = match.group(1)

    return json.loads(json_str)
