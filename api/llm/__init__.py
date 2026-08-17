import os
from utils.file import return_file_contents
from google import genai
from google.genai import types


class _ChatModel:
    """Adapter so callers can keep doing `self.chat_model.generate_content(x).text`
    regardless of which Google SDK/auth backend sits underneath."""

    def __init__(self, client: genai.Client, model_name: str, system_instruction: str):
        self._client = client
        self._model_name = model_name
        self._config = types.GenerateContentConfig(system_instruction=system_instruction)

    def generate_content(self, prompt):
        return self._client.models.generate_content(
            model=self._model_name,
            contents=str(prompt),
            config=self._config,
        )


class LLM:
    agent = None
    def __init__(self, model_name: str,prompt_path: str = "prompts_v1/wabi-sabi.prompt"):
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        system_prompt = return_file_contents(prompt_path)

        self.chat_model = _ChatModel(client, model_name, system_prompt)

    def chat(self, payload: dict) -> dict:
        response = self.chat_model.generate_content(str(payload))
        return response

    def vertex_chat(self, payload: dict):
        response = self.chat_model.generate_content(str(payload))
        return response

if os.getenv("GEMINI_API_KEY") and os.getenv("LLM_MODEL") and os.getenv("SYSTEM_PROMPT_PATH"):
    print("Initializing Wabi-Sabi LLM...")
    wabi_sabi_llm = LLM(model_name=os.getenv("LLM_MODEL"),prompt_path=os.getenv("SYSTEM_PROMPT_PATH"))
    print("Wabi-Sabi LLM initialized.")
    print("Initializing Wabi-Sabi Scan LLM...")
    wabi_sabi_scan_llm = LLM(model_name=os.getenv("LLM_MODEL"),prompt_path="prompts/wabi_sabi_scan.prompt")
    print("Wabi-Sabi Scan LLM initialized.")
else:
    raise EnvironmentError("GEMINI_API_KEY, LLM_MODEL and SYSTEM_PROMPT_PATH must be set.")
