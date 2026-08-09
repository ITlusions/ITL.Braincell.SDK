"""Smoke test: verify the SDK can be imported."""
from itl_braincell_sdk.core import config  # noqa: F401


def test_settings_class_exists() -> None:
    assert hasattr(config, "Settings")
