import os
from llm import LLM
from models.hallucination import HallucinationResult
from utils.json import safe_json_loads

class HallucinationDetector:
    def __init__(self):
        print("Initializing hallucination detector...")
        self.llm = LLM(model_name=os.getenv("JUDGE_MODEL"), prompt_path="prompts/hallucination_detection.prompt")
        print("Hallucination detector initialized.")

    def detection_required(self, ai_response: str, prefilter_function)-> bool:
        if not ai_response or ai_response.strip() == "":
            return False
        presRes = prefilter_function(ai_response)
        return presRes.should_evaluate
    
    def detect_hallucination(self, inputs, response: str) -> HallucinationResult:
        prompt = f"Input: {inputs}\nResponse: {response}\nEvaluate the response for hallucination."
        try:
         llm_response = self.llm.chat_model.generate_content( prompt)
         print(f"LLM raw response for hallucination detection: {llm_response.text}")

         res_dict = safe_json_loads(llm_response.text)
         hallucination_score = float(res_dict.get("hallucination_score", 0.0))
         reason = res_dict.get("reason", "")
         category = res_dict.get("category", "")
        
         return HallucinationResult(
            hallucination_score=hallucination_score,
            reason=reason,
            category=category
         )
        
        except Exception as e:
            print(f"Error during hallucination detection: {e}")
            return HallucinationResult(
                error=str(e),
            )
        
if os.getenv("JUDGE_MODEL"):
    hallucination_detector = HallucinationDetector()
else:
    raise EnvironmentError("All LLM environment variables for Hallucination detection must be set.")