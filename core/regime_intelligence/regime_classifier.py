"""Regime Classifier — classifies market regime from descriptions or metrics."""
import threading


class RegimeClassifier:
    REGIME_RULES = {
        "crisis": ["crash", "crisis", "collapse", "circuit breaker"],
        "volatile": ["volatile", "high volatility", "vix spike"],
        "bull": ["bull", "uptrend", "rally", "new high"],
        "bear": ["bear", "downtrend", "selloff", "decline"],
        "sideways": ["sideways", "range", "consolidation", "flat"],
    }

    def __init__(self):
        self._lock = threading.RLock()

    def classify_from_description(self, description: str) -> str:
        with self._lock:
            desc_lower = description.lower()
            for regime, keywords in self.REGIME_RULES.items():
                if any(kw in desc_lower for kw in keywords):
                    return regime.upper()
            return "SIDEWAYS"

    def classify_from_metrics(self, volatility: float = None, trend_strength: float = None,
                               drawdown: float = None) -> str:
        with self._lock:
            if volatility is not None and drawdown is not None:
                if volatility > 0.03 and drawdown > 0.10:
                    return "CRISIS"
            if volatility is not None and volatility > 0.02:
                return "VOLATILE"
            if trend_strength is not None:
                if trend_strength > 0.6:
                    return "BULL"
                if trend_strength < -0.4:
                    return "BEAR"
            return "SIDEWAYS"

    def current_classification(self) -> dict:
        from core.regime_intelligence.regime_history import regime_history
        return regime_history.current_regime()


regime_classifier = RegimeClassifier()
