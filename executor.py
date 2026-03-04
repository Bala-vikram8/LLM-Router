import time
import anthropic
from router.engine import LLMRouter
from router.models import RoutingDecision, QueryFeedback
from feedback.store import FeedbackStore
from config import ANTHROPIC_API_KEY


class RouterExecutor:
    def __init__(self):
        self.router = LLMRouter()
        self.store = FeedbackStore()
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    def execute(self, query: str, system_prompt: str = "") -> dict:
        decision = self.router.route(query)
        self.store.log_decision(decision)

        print(f"\n[ROUTER] Query: {query[:60]}...")
        print(f"[ROUTER] Complexity: {decision.complexity.value} (score: {decision.complexity_score})")
        print(f"[ROUTER] Domain: {decision.domain.value}")
        print(f"[ROUTER] Selected model: {decision.selected_model}")
        print(f"[ROUTER] Estimated cost: ${decision.estimated_cost_usd:.6f}")

        start = time.time()
        try:
            messages = [{"role": "user", "content": query}]
            kwargs = {
                "model": decision.selected_model,
                "max_tokens": 1024,
                "messages": messages,
            }
            if system_prompt:
                kwargs["system"] = system_prompt

            response = self.client.messages.create(**kwargs)
            latency_ms = (time.time() - start) * 1000
            output_text = response.content[0].text
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens

            from router.model_registry import MODEL_REGISTRY
            config = MODEL_REGISTRY.get(decision.selected_model)
            actual_cost = 0.0
            if config:
                actual_cost = (
                    (input_tokens / 1000) * config.cost_per_1k_input_tokens +
                    (output_tokens / 1000) * config.cost_per_1k_output_tokens
                )

            quality = self._auto_quality_score(query, output_text)
            feedback = QueryFeedback(
                decision_id=decision.decision_id,
                response_quality=quality,
                required_followup=False,
                response_length=len(output_text.split()),
                latency_ms=latency_ms,
                actual_cost_usd=actual_cost,
            )
            self.store.log_feedback(feedback)

            print(f"[ROUTER] Latency: {latency_ms:.0f}ms | Actual cost: ${actual_cost:.6f} | Quality: {quality:.2f}")

            return {
                "decision": decision.model_dump(),
                "response": output_text,
                "latency_ms": latency_ms,
                "actual_cost_usd": actual_cost,
                "quality_score": quality,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            }

        except Exception as e:
            latency_ms = (time.time() - start) * 1000
            print(f"[ROUTER ERROR] {str(e)}")
            return {
                "decision": decision.model_dump(),
                "error": str(e),
                "latency_ms": latency_ms,
            }

    def _auto_quality_score(self, query: str, response: str) -> float:
        score = 0.5
        word_count = len(response.split())

        if word_count < 5:
            score -= 0.3
        elif word_count > 20:
            score += 0.2

        uncertainty_phrases = [
            "i don't know", "i'm not sure", "i cannot", "i do not have",
            "i'm unable", "as an ai", "i apologize"
        ]
        if any(phrase in response.lower() for phrase in uncertainty_phrases):
            score -= 0.15

        query_keywords = set(query.lower().split())
        response_lower = response.lower()
        overlap = sum(1 for kw in query_keywords if kw in response_lower and len(kw) > 3)
        if len(query_keywords) > 0:
            score += min(0.3, overlap / len(query_keywords) * 0.5)

        return round(max(0.0, min(1.0, score)), 3)

    def execute_batch(self, queries: list[str], system_prompt: str = "") -> list[dict]:
        return [self.execute(q, system_prompt) for q in queries]

    def get_savings_report(self, decisions_limit: int = 100) -> dict:
        decisions_data = self.store.get_all_decisions(limit=decisions_limit)
        from router.models import RoutingDecision
        decisions = []
        for d in decisions_data:
            try:
                from router.models import ComplexityLevel, QueryDomain, ModelTier
                decisions.append(RoutingDecision(
                    decision_id=d["decision_id"],
                    timestamp=d["timestamp"],
                    query=d["query"],
                    complexity=ComplexityLevel(d["complexity"]),
                    domain=QueryDomain(d["domain"]),
                    complexity_score=d["complexity_score"],
                    selected_tier=ModelTier(d["selected_tier"]),
                    selected_model=d["selected_model"],
                    reasoning=d["reasoning"],
                    estimated_cost_usd=d["estimated_cost_usd"],
                    tokens_estimated=d["tokens_estimated"],
                ))
            except Exception:
                continue
        return self.router.calculate_savings(decisions)
