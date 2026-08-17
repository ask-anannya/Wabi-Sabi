import json
from models.user import User

def contains_any(text: str, terms: set[str]) -> bool:
    text = text.lower()
    return any(term in text for term in terms)


def is_profile_partial(profile: User) -> bool:
    if profile.Concerns is None or len(profile.Concerns) == 0 or profile.Age is None or profile.SkinType is None:
        return True
    return False


def extract_ingredients(text: str, ingredients: set[str]) -> list[str]:
    text = text.lower()
    return [i for i in ingredients if i in text]

def extract_profile_in_routine(text: str) -> dict:
    try:
     textRes = json.loads(text)
     if textRes.get("type","") == "routine" and "profile" in textRes:
        return textRes["profile"]

    except Exception as e:
        print(f"Error extracting profile: {e}")
        return {}