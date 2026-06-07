import json
from types import SimpleNamespace

from examples.live_openai_demo import run_live_openai_demo


class FakeCompletions:
    def create(self, **kwargs):
        arguments = json.dumps(
            {
                "action": "read_file",
                "target": "README.md",
            }
        )

        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content=None,
                        tool_calls=[
                            SimpleNamespace(
                                id="call_live_demo",
                                type="function",
                                function=SimpleNamespace(
                                    name="file_read",
                                    arguments=arguments,
                                ),
                            )
                        ],
                    )
                )
            ]
        )


class FakeClient:
    def __init__(self):
        self.chat = SimpleNamespace(completions=FakeCompletions())


def test_optional_live_openai_demo_skips_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    result = run_live_openai_demo()

    assert result["skipped"] is True
    assert result["reason"] == "OPENAI_API_KEY is not set."


def test_optional_live_openai_demo_handles_injected_client(tmp_path):
    result = run_live_openai_demo(
        client=FakeClient(),
        model="fake-model",
        audit_log_path=str(tmp_path / "live_openai_audit.jsonl"),
    )

    assert result["skipped"] is False
    assert result["tool_called"] is True
    assert result["model"] == "fake-model"
    assert result["result"]["tool_call_id"] == "call_live_demo"
    assert result["result"]["allowed"] is True
    assert result["result"]["executed"] is True
    assert (tmp_path / "live_openai_audit.jsonl").exists()
