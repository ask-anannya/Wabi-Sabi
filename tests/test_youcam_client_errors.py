import asyncio

import pytest

from services import youcam_client as yc


class _FakeResponse:
    def __init__(self, json_data):
        self._json_data = json_data

    def raise_for_status(self):
        pass

    def json(self):
        return self._json_data


class _FakeClient:
    def __init__(self, responses):
        self._responses = list(responses)

    async def get(self, *_args, **_kwargs):
        response = self._responses[0] if len(self._responses) == 1 else self._responses.pop(0)
        return _FakeResponse(response)


def test_task_failure_raises_runtime_error():
    client = _FakeClient([{"status": 200, "data": {"task_status": "error", "error": "boom"}}])
    with pytest.raises(RuntimeError):
        asyncio.run(yc._poll_task(client, "task-1", timeout_s=5.0))


def test_task_that_never_completes_times_out(monkeypatch):
    monkeypatch.setattr(yc.time, "sleep", lambda _seconds: None)
    client = _FakeClient([{"status": 200, "data": {"task_status": "running"}}] * 1000)
    with pytest.raises(TimeoutError):
        asyncio.run(yc._poll_task(client, "task-2", timeout_s=0.05))
