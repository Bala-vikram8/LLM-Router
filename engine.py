from router.models import (
    RoutingDecision, ComplexityLevel, ModelTier, QueryDomain
)
from router.classifier import ComplexityClassifier
from router.model_registry import MODEL_REGISTRY, TIER_TO_MODEL


COMPLEXITY_TO_TIER: dict[ComplexityLevel, ModelTier] = {
    ComplexityLevel.SIMPLE: ModelTier.TIER_1,
    ComplexityLevel.MODERATE: ModelTier.TIER_2,
    ComplexityLevel.COMPLEX: ModelTier.TIER_3,
}

DOMAIN_TIER_FLOOR: dict[QueryDomain, ModelTier] = {
    QueryDomain.CODING: ModelTier.TIER_2,
    QueryDomain.ANALYSIS: ModelTier.TIER_2,
    QueryDomain.REASONING: ModelTier.TIER_1,
    QueryDomain.FACTUAL: ModelTier.TIER_1,
    QueryDomain.CONVERSATIONAL: ModelTier.TIER_1,
    QueryDomain.CREATIVE: ModelTier.TIER_1,
}

TIER_ORDER = [ModelTier.TIER_1, ModelTier.TIER_2, ModelTier.TIER_3]


def _max_tier(a: ModelTier, b: ModelTier) -> ModelTier:
    return TIER_ORDER[max(TIER_ORDER.index(a), TIER_ORDER.index(b))]


def _estimate_tokens(query: str) -> int:
    return max(100, int(len(query.split()) * 1.3) + 200)


def _estimate_cost(model_id: str, tokens: int) -> float:
    config = MODEL_REGISTRY.get(model_id)
    if not config:
        return 0.0
    input_cost = (tokens / 1000) * config.cost_per_1k_input_tokens
    output_cost = (tokens / 1000) * config.cost_per_1k_output_tokens
    return round(input_cost + output_cost, 6)


def _build_reasoning(
    complexity: ComplexityLevel,
    domain: QueryDomain,
    score: float,
    tier: ModelTier,
    forced: bool,
) -> str:
    if forced:
        return (
            f"Forced to TIER_3 due to high-stakes domain keyword detected. "
            f"Domain: {domain.value}, Score: {score}"
        )
    return (
        f"Complexity score {score:.2f} → {complexity.value}. "
        f"Domain: {domain.value}. "
        f"Domain floor applied: {DOMAIN_TIER_FLOOR.get(domain, ModelTier.TIER_1).value}. "
        f"Final tier: {tier.value}."
    )


class LLMRouter:
    def __init__(self):
        self.classifier = ComplexityClassifier()

    def route(self, query: str) -> RoutingDecision:
        forced_tier = self.classifier.get_forced_tier(query)

        if forced_tier:
            complexity = ComplexityLevel.COMPLEX
            domain = QueryDomain.ANALYSIS
            score = 1.0
            tier = forced_tier
            forced = True
        else:
            complexity, domain, score = self.classifier.classify(query)
            base_tier = COMPLEXITY_TO_TIER[complexity]
            domain_floor = DOMAIN_TIER_FLOOR.get(domain, ModelTier.TIER_1)
            tier = _max_tier(base_tier, domain_floor)
            forced = False

        model_id = TIER_TO_MODEL[tier]
        tokens = _estimate_tokens(query)
        cost = _estimate_cost(model_id, tokens)
        reasoning = _build_reasoning(complexity, domain, score, tier, forced)

        return RoutingDecision(
            query=query,
            complexity=complexity,
            domain=domain,
            complexity_score=score,
            selected_tier=tier,
            selected_model=model_id,
            reasoning=reasoning,
            estimated_cost_usd=cost,
            tokens_estimated=tokens,
        )

    def route_batch(self, queries: list[str]) -> list[RoutingDecision]:
        return [self.route(q) for q in queries]

    def what_if_all_tier3(self, queries: list[str]) -> float:
        tier3_model = TIER_TO_MODEL[ModelTier.TIER_3]
        total = 0.0
        for q in queries:
            tokens = _estimate_tokens(q)
            total += _estimate_cost(tier3_model, tokens)
        return round(total, 6)

    def calculate_savings(self, decisions: list[RoutingDecision]) -> dict:
        actual_cost = sum(d.estimated_cost_usd for d in decisions)
        baseline_cost = self.what_if_all_tier3([d.query for d in decisions])
        savings = baseline_cost - actual_cost
        pct = (savings / baseline_cost * 100) if baseline_cost > 0 else 0
        return {
            "actual_cost_usd": round(actual_cost, 6),
            "baseline_cost_usd": round(baseline_cost, 6),
            "savings_usd": round(savings, 6),
            "savings_pct": round(pct, 1),
        }
