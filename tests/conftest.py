"""
Test bootstrap. The app's modules read config at import time (fail-fast
env-var pattern, e.g. api/llm/__init__.py, api/datadog_agent/__init__.py) and
resolve prompt files relative to cwd (matching the Docker WORKDIR /app at
runtime — see api/Dockerfile). Both are set up here, before any test module
imports app code, so tests don't need a real Gemini API key or a live
Datadog agent: genai.Client()/GenerateContentConfig() and DogStatsd's UDP
socket don't make network calls until an actual generate_content()/send
happens.
"""

import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TESTS_DIR)
API_DIR = os.path.join(REPO_ROOT, "api")

os.chdir(API_DIR)
sys.path.insert(0, API_DIR)

os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")
os.environ.setdefault("LLM_MODEL", "gemini-1.5-flash")
os.environ.setdefault("SYSTEM_PROMPT_PATH", os.path.join(API_DIR, "prompts", "wabi-sabi_v2.prompt"))
os.environ.setdefault("JUDGE_MODEL", "gemini-1.5-flash")
os.environ.setdefault("GROUNDING_MODEL", "gemini-1.5-flash")
os.environ.setdefault("DD_AGENT_HOST", "localhost")
os.environ.setdefault("DD_PORT", "8125")
os.environ.setdefault("YOUCAM_MOCK_MODE", "true")
os.environ.setdefault("YOUCAM_API_BASE", "https://example.invalid")
os.environ.setdefault("TRUST_WEIGHTS", "0.4,0.4,0.2")
os.environ.setdefault("SCAN_DB_PATH", os.path.join(TESTS_DIR, "test_scan_history.db"))
os.environ.setdefault("CORS_ALLOW_ORIGINS", "*")
