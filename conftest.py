"""
Root conftest.py — registers the IMRAF Verifier Auto-Recording Plugin.

FTD-EGI-001 Component 2: every pytest run automatically creates a VERIFIER
record in institutional memory without any manual action.
"""
from core.governance.auto_recording.pytest_imraf_plugin import IMRAFVerifierPlugin


def pytest_configure(config):
    config.pluginmanager.register(IMRAFVerifierPlugin(), "imraf_verifier_plugin")
