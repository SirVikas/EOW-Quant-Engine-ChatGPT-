"""
FTD-AIL-001: LLM Adapter — pluggable interface.
Only calls real LLM if ANTHROPIC_API_KEY env var is set.
Rule-based analyzer is the primary engine.
"""
from __future__ import annotations
import os
from typing import Any


class LLMAdapter:
    """Adapter interface for LLM-assisted analysis. No-op unless API key configured."""

    def is_available(self) -> bool:
        return bool(os.getenv("ANTHROPIC_API_KEY"))

    def analyze_finding(self, finding_dict: dict[str, Any]) -> str | None:
        """Returns enriched recommendation text or None if LLM not available."""
        if not self.is_available():
            return None
        try:
            import anthropic
            client = anthropic.Anthropic()
            prompt = (
                f"You are a quantitative trading system analyst. "
                f"Analyze this finding and provide a concise recommendation (2-3 sentences):\n\n"
                f"Title: {finding_dict.get('title')}\n"
                f"Severity: {finding_dict.get('severity')}\n"
                f"Evidence: {finding_dict.get('evidence')}\n"
                f"Initial recommendation: {finding_dict.get('recommendation')}"
            )
            msg = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=256,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text if msg.content else None
        except Exception:
            return None


llm_adapter = LLMAdapter()
