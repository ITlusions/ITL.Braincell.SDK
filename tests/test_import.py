"""Smoke test: verify the SDK core config can be imported and Settings exists."""
from itl_braincell_sdk.core import config


def test_settings_class_exists() -> None:
    assert hasattr(config, "Settings")
