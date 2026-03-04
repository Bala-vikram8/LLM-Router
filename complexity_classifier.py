import re
from typing import Tuple
from router.models import ComplexityScore, QueryDomain, ModelTier


TIER_THRESHOLDS = {
    ModelTier.TIER_1: (0.0, 0.30),
    ModelTier.TIER_2: (0.30, 0.60),
    ModelTier.TIER_3: (0.60, 1.0),
}

DOMAIN_KEYWORDS = {
    QueryDomain.CODE: [
        "code", "function", "debug", "implement", "algorithm", "class",
        "api", "sql", "python", "javascript", "typescript", "error", "bug",
        "refactor", "optimize", "test", "deploy", "docker", "kubernetes"
    ],
    QueryDomain.MEDICAL: [
        "diagnosis", "treatment", "symptom", "medication", "disease",
        "clinical", "patient", "therapy", "dosage", "medical", "health",
        "condition", "surgery", "prescription", "drug", "cancer", "chronic"
    ],
    QueryDomain.LEGAL: [
        "law", "legal", "contract", "liability", "regulation", "compliance",
        "statute", "clause", "jurisdiction", "court", "attorney", "rights",
        "patent", "trademark", "lawsuit", "settlement", "arbitration"
    ],
    QueryDomain.FINANCIAL: [
        "investment", "portfolio", "stock", "revenue", "financial", "market",
        "trading", "asset", "valuation", "risk", "return", "hedge",
        "derivative", "equity", "debt", "credit", "accounting", "tax"
    ],
    QueryDomain.TECHNICAL: [
        "system", "architecture", "infrastructure", "network", "database",
        "security", "performance", "scalability", "distributed", "cloud",
        "microservice", "pipeline", "data", "model", "machine learning"
    ],
    QueryDomain.CREATIVE: [
        "write", "story", "poem", "creative", "essay", "blog", "article",
        "narrative", "character", "plot", "fiction", "describe", "imagine"
    ],
}

COMPLEXITY_INDICATORS = {
    "high": [
        "analyze", "evaluate", "compare", "critique", "design", "architect",
        "explain why", "pros and cons", "tradeoffs", "recommend", "strategy",
        "comprehensive", "detailed", "step by step", "implement", "optimize",
        "multi-step", "complex", "advanced", "expert", "architectural",
        "in-depth", "thoroughly", "end to end", "production", "enterprise"
    ],
    "medium": [
        "summarize", "explain", "describe", "how does", "what is the difference",
        "list", "provide examples", "overview", "understand", "difference between",
        "compare", "contrast", "with examples", "how to", "why does",
        "key concepts", "main points", "brief overview", "what are"
    ],
    "low": [
        "what is", "define", "who is", "when did", "translate", "convert",
        "format", "fix typo", "correct grammar", "simple", "quick"
    ],
}

SENSITIVITY_KEYWORDS = [
    "medical", "legal", "financial", "diagnosis", "treatment", "invest",
    "compliance", "lawsuit", "medication", "surgery", "contract", "liability",
    "prescription", "clinical", "drug", "risk assessment", "patient"
]


class ComplexityClassifier:
    def __init__(self, learned_weights: dict = None):
        self.weights = learned_weights or {
            "reasoning": 0.4,
            "domain": 0.35,
            "sensitivity": 0.25,
        }

    def classify(self, query: str) -> ComplexityScore:
        query_lower = query.lower()
        word_count = len(query.split())

        reasoning_score = self._score_reasoning(query_lower, word_count)
        domain, domain_score = self._score_domain(query_lower)
        sensitivity_score = self._score_sensitivity(query_lower, domain)

        overall = (
            reasoning_score * self.weights["reasoning"]
            + domain_score * self.weights["domain"]
            + sensitivity_score * self.weights["sensitivity"]
        )
        overall = min(1.0, max(0.0, overall))

        confidence = self._estimate_confidence(query_lower, word_count)

        return ComplexityScore(
            reasoning_depth=round(reasoning_score, 3),
            domain_specificity=round(domain_score, 3),
            output_sensitivity=round(sensitivity_score, 3),
            overall=round(overall, 3),
            domain=domain,
            confidence=round(confidence, 3),
        )

    def _score_reasoning(self, query_lower: str, word_count: int) -> float:
        score = 0.0

        high_matches = sum(1 for kw in COMPLEXITY_INDICATORS["high"] if kw in query_lower)
        medium_matches = sum(1 for kw in COMPLEXITY_INDICATORS["medium"] if kw in query_lower)
        low_matches = sum(1 for kw in COMPLEXITY_INDICATORS["low"] if kw in query_lower)

        score += min(0.6, high_matches * 0.15)
        score += min(0.3, medium_matches * 0.08)
        score -= min(0.3, low_matches * 0.1)

        if word_count > 100:
            score += 0.2
        elif word_count > 50:
            score += 0.1
        elif word_count < 10:
            score -= 0.1

        question_marks = query_lower.count("?")
        if question_marks > 2:
            score += 0.15

        return min(1.0, max(0.0, score))

    def _score_domain(self, query_lower: str) -> Tuple[QueryDomain, float]:
        domain_scores = {}
        for domain, keywords in DOMAIN_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in query_lower)
            domain_scores[domain] = matches

        if not any(domain_scores.values()):
            return QueryDomain.GENERAL, 0.2

        best_domain = max(domain_scores, key=domain_scores.get)
        best_score = domain_scores[best_domain]

        specificity = {
            QueryDomain.MEDICAL: 0.9,
            QueryDomain.LEGAL: 0.85,
            QueryDomain.FINANCIAL: 0.8,
            QueryDomain.CODE: 0.7,
            QueryDomain.TECHNICAL: 0.65,
            QueryDomain.CREATIVE: 0.3,
            QueryDomain.GENERAL: 0.2,
        }

        base = specificity.get(best_domain, 0.3)
        score = min(1.0, base + (best_score - 1) * 0.05)
        return best_domain, score

    def _score_sensitivity(self, query_lower: str, domain: QueryDomain) -> float:
        score = 0.0
        matches = sum(1 for kw in SENSITIVITY_KEYWORDS if kw in query_lower)
        score += min(0.6, matches * 0.15)

        high_sensitivity_domains = {QueryDomain.MEDICAL, QueryDomain.LEGAL, QueryDomain.FINANCIAL}
        if domain in high_sensitivity_domains:
            score += 0.3

        return min(1.0, max(0.0, score))

    def _estimate_confidence(self, query_lower: str, word_count: str) -> float:
        total_matches = sum(
            1 for indicators in COMPLEXITY_INDICATORS.values()
            for kw in indicators if kw in query_lower
        )
        base_confidence = min(0.95, 0.5 + total_matches * 0.05)
        return base_confidence

    def get_tier(self, score: ComplexityScore) -> ModelTier:
        for tier, (low, high) in TIER_THRESHOLDS.items():
            if low <= score.overall < high:
                return tier
        return ModelTier.TIER_3

    def update_weights(self, new_weights: dict):
        self.weights.update(new_weights)
