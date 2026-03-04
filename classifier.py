import re
from router.models import ComplexityLevel, QueryDomain, ModelTier
from router.model_registry import ALWAYS_TIER_3_PHRASES


SIMPLE_PATTERNS = [
    r"^what is\b",
    r"^who is\b",
    r"^when (was|is|did)\b",
    r"^where is\b",
    r"^how (many|much|old)\b",
    r"^define\b",
    r"^list\b",
    r"^translate\b",
    r"^convert\b",
    r"^spell\b",
    r"^capital of\b",
]

COMPLEX_PATTERNS = [
    r"\banalyze\b",
    r"\bcompare and contrast\b",
    r"\bcritically evaluate\b",
    r"\bdesign a system\b",
    r"\barchitect\b",
    r"\bwrite a (research|detailed|comprehensive)\b",
    r"\bexplain .{50,}",
    r"\bdebug .{30,}",
    r"\brefactor\b",
    r"\boptimize\b",
    r"\bstrategy\b",
    r"\bframework\b",
    r"\bimplications\b",
]

CODING_PATTERNS = [
    r"\bcode\b", r"\bfunction\b", r"\bclass\b", r"\bapi\b",
    r"\bpython\b", r"\bjavascript\b", r"\bsql\b", r"\bbug\b",
    r"\bdebug\b", r"\brefactor\b", r"\bscript\b", r"\balgorithm\b",
]

REASONING_PATTERNS = [
    r"\bwhy\b", r"\bhow does\b", r"\bexplain\b", r"\bcause\b",
    r"\bimpact\b", r"\beffect\b", r"\bimplication\b", r"\bshould\b",
    r"\bif .+ then\b", r"\bpros and cons\b",
]

ANALYSIS_PATTERNS = [
    r"\banalyze\b", r"\bevaluate\b", r"\bassess\b", r"\breview\b",
    r"\bcompare\b", r"\bcontrast\b", r"\bsummarize\b", r"\breport\b",
]

CREATIVE_PATTERNS = [
    r"\bwrite a (story|poem|essay|blog|email|letter)\b",
    r"\bcreate content\b", r"\bdraft\b", r"\bgenerate ideas\b",
    r"\bbrainstorm\b",
]


class ComplexityClassifier:
    def __init__(self):
        self._routing_overrides: dict[str, ModelTier] = {}

    def classify(self, query: str) -> tuple[ComplexityLevel, QueryDomain, float]:
        query_lower = query.lower().strip()

        domain = self._detect_domain(query_lower)
        score = self._compute_score(query_lower, domain)
        complexity = self._score_to_level(score)

        return complexity, domain, round(score, 3)

    def get_forced_tier(self, query: str) -> ModelTier | None:
        query_lower = query.lower()
        for phrase in ALWAYS_TIER_3_PHRASES:
            if phrase in query_lower:
                return ModelTier.TIER_3
        return None

    def _detect_domain(self, query_lower: str) -> QueryDomain:
        scores = {
            QueryDomain.CODING: sum(1 for p in CODING_PATTERNS if re.search(p, query_lower)),
            QueryDomain.REASONING: sum(1 for p in REASONING_PATTERNS if re.search(p, query_lower)),
            QueryDomain.ANALYSIS: sum(1 for p in ANALYSIS_PATTERNS if re.search(p, query_lower)),
            QueryDomain.CREATIVE: sum(1 for p in CREATIVE_PATTERNS if re.search(p, query_lower)),
        }
        best = max(scores, key=scores.get)
        if scores[best] == 0:
            if any(re.search(p, query_lower) for p in SIMPLE_PATTERNS):
                return QueryDomain.FACTUAL
            return QueryDomain.CONVERSATIONAL
        return best

    def _compute_score(self, query_lower: str, domain: QueryDomain) -> float:
        score = 0.0

        word_count = len(query_lower.split())
        if word_count < 10:
            score += 0.1
        elif word_count < 30:
            score += 0.3
        elif word_count < 60:
            score += 0.5
        else:
            score += 0.7

        simple_matches = sum(1 for p in SIMPLE_PATTERNS if re.search(p, query_lower))
        complex_matches = sum(1 for p in COMPLEX_PATTERNS if re.search(p, query_lower))

        score -= simple_matches * 0.15
        score += complex_matches * 0.2

        domain_weights = {
            QueryDomain.FACTUAL: -0.2,
            QueryDomain.CONVERSATIONAL: -0.1,
            QueryDomain.CREATIVE: 0.1,
            QueryDomain.REASONING: 0.2,
            QueryDomain.CODING: 0.25,
            QueryDomain.ANALYSIS: 0.3,
        }
        score += domain_weights.get(domain, 0)

        sentence_count = len(re.split(r'[.!?]+', query_lower))
        if sentence_count > 3:
            score += 0.1

        return max(0.0, min(1.0, score))

    def _score_to_level(self, score: float) -> ComplexityLevel:
        if score < 0.35:
            return ComplexityLevel.SIMPLE
        elif score < 0.65:
            return ComplexityLevel.MODERATE
        else:
            return ComplexityLevel.COMPLEX

    def update_override(self, pattern: str, tier: ModelTier):
        self._routing_overrides[pattern] = tier
