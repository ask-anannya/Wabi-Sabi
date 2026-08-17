from llm.grounding import grounding_checker
from services.youcam_client import SkinMetric


class _FakeLLMResponse:
    def __init__(self, text: str):
        self.text = text


class _FakeChatModel:
    def __init__(self, text: str):
        self._text = text

    def generate_content(self, _prompt):
        return _FakeLLMResponse(self._text)


def test_malformed_json_from_grounding_llm_falls_back_safely(monkeypatch):
    monkeypatch.setattr(grounding_checker.llm, "chat_model", _FakeChatModel("not valid json {{{"))
    metrics = [SkinMetric(name="moisture", raw_score=60, normalised=0.6, band="moderate", band_distance=0.1)]

    result = grounding_checker.llm_check(metrics, "Your skin looks a bit dry.")

    assert result.error != ""
    assert result.grounding_score == 0.0
    assert not result.passed
