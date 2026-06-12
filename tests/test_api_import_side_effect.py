import importlib


def test_api_module_import_does_not_load_default_policy(monkeypatch) -> None:
    import rygnal.api as api_module
    import rygnal.policy_engine as policy_engine_module

    def fail_if_called():
        raise AssertionError("load_default_policy_engine must not run at import time")

    with monkeypatch.context() as patch_context:
        patch_context.setattr(
            policy_engine_module,
            "load_default_policy_engine",
            fail_if_called,
        )

        reloaded_api = importlib.reload(api_module)

        assert hasattr(reloaded_api, "create_app")
        assert not hasattr(reloaded_api, "app")

    importlib.reload(api_module)


def test_create_app_still_loads_default_policy_when_called(monkeypatch) -> None:
    import rygnal.api as api_module

    called = {"value": False}

    class FakePolicyEngine:
        def evaluate(self, request, risk_assessment=None):
            raise AssertionError("not needed for app construction test")

    def fake_load_default_policy_engine():
        called["value"] = True
        return FakePolicyEngine()

    monkeypatch.setattr(
        api_module,
        "load_default_policy_engine",
        fake_load_default_policy_engine,
    )

    app = api_module.create_app()

    assert called["value"] is True
    assert app.title == "Rygnal Core Local API"
