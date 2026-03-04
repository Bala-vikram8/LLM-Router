from enum import Enum
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid


class ModelTier(str, Enum):
    TIER_1 = "tier_1"
    TIER_2 = "tier_2"
    TIER_3 = "tier_3"


class ComplexityLevel(str, Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class QueryDomain(str, Enum):
    FACTUAL = "factual"
    REASONING = "reasoning"
    CODING = "coding"
    CREATIVE = "creative"
    ANALYSIS = "analysis"
    CONVERSATIONAL = "conversational"


class RoutingDecision(BaseModel):
    decision_id: str = ""
    timestamp: str = ""
    query: str
    complexity: ComplexityLevel
    domain: QueryDomain
    complexity_score: float
    selected_tier: ModelTier
    selected_model: str
    reasoning: str
    estimated_cost_usd: float
    tokens_estimated: int

    def model_post_init(self, __context):
        if not self.decision_id:
            self.decision_id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()


class QueryFeedback(BaseModel):
    feedback_id: str = ""
    decision_id: str
    timestamp: str = ""
    response_quality: float
    user_satisfied: Optional[bool] = None
    required_followup: bool = False
    response_length: int = 0
    latency_ms: float = 0
    actual_cost_usd: float = 0
    notes: Optional[str] = None

    def model_post_init(self, __context):
        if not self.feedback_id:
            self.feedback_id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()


class RouterStats(BaseModel):
    total_queries: int = 0
    tier_distribution: Dict[str, int] = {}
    total_cost_usd: float = 0
    estimated_savings_usd: float = 0
    avg_quality_score: float = 0
    queries_by_domain: Dict[str, int] = {}
    cost_trend: List[Dict[str, Any]] = []


class ModelConfig(BaseModel):
    model_id: str
    tier: ModelTier
    cost_per_1k_input_tokens: float
    cost_per_1k_output_tokens: float
    max_tokens: int
    avg_latency_ms: float
    provider: str
