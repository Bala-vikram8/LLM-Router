from router.models import ModelConfig, ModelTier

MODEL_REGISTRY: dict[str, ModelConfig] = {
    "claude-haiku-4-5-20251001": ModelConfig(
        model_id="claude-haiku-4-5-20251001",
        tier=ModelTier.TIER_1,
        cost_per_1k_input_tokens=0.00025,
        cost_per_1k_output_tokens=0.00125,
        max_tokens=8192,
        avg_latency_ms=400,
        provider="anthropic",
    ),
    "claude-sonnet-4-20250514": ModelConfig(
        model_id="claude-sonnet-4-20250514",
        tier=ModelTier.TIER_2,
        cost_per_1k_input_tokens=0.003,
        cost_per_1k_output_tokens=0.015,
        max_tokens=8192,
        avg_latency_ms=1200,
        provider="anthropic",
    ),
    "claude-opus-4-20250514": ModelConfig(
        model_id="claude-opus-4-20250514",
        tier=ModelTier.TIER_3,
        cost_per_1k_input_tokens=0.015,
        cost_per_1k_output_tokens=0.075,
        max_tokens=8192,
        avg_latency_ms=3000,
        provider="anthropic",
    ),
}

TIER_TO_MODEL: dict[ModelTier, str] = {
    ModelTier.TIER_1: "claude-haiku-4-5-20251001",
    ModelTier.TIER_2: "claude-sonnet-4-20250514",
    ModelTier.TIER_3: "claude-opus-4-20250514",
}

ALWAYS_TIER_3_PHRASES = [
    "legal advice",
    "medical diagnosis",
    "financial planning",
    "security vulnerability",
    "audit report",
    "compliance review",
    "clinical trial",
    "drug interaction",
    "regulatory filing",
]
