from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from router.engine import LLMRouter
from feedback.store import FeedbackStore
from feedback.retrainer import FeedbackRetrainer
from router.classifier import ComplexityClassifier

app = FastAPI(
    title="LLM Router Dashboard",
    description="Cost-quality optimized LLM routing with feedback loop",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

router = LLMRouter()
store = FeedbackStore()
classifier = ComplexityClassifier()
retrainer = FeedbackRetrainer(store, classifier)


class RouteRequest(BaseModel):
    query: str


class FeedbackRequest(BaseModel):
    decision_id: str
    response_quality: float
    user_satisfied: bool = None
    required_followup: bool = False
    notes: str = None


@app.get("/")
def root():
    return {"service": "LLM Router", "status": "running", "version": "1.0.0"}


@app.post("/route")
def route_query(request: RouteRequest):
    decision = router.route(request.query)
    store.log_decision(decision)
    return decision.model_dump()


@app.post("/feedback")
def submit_feedback(request: FeedbackRequest):
    from router.models import QueryFeedback
    feedback = QueryFeedback(
        decision_id=request.decision_id,
        response_quality=request.response_quality,
        user_satisfied=request.user_satisfied,
        required_followup=request.required_followup,
        notes=request.notes,
    )
    store.log_feedback(feedback)
    return {"status": "logged", "feedback_id": feedback.feedback_id}


@app.get("/decisions")
def get_decisions(limit: int = 50):
    return {"decisions": store.get_all_decisions(limit=limit)}


@app.get("/stats/cost")
def cost_stats():
    return store.get_cost_summary()


@app.get("/stats/quality")
def quality_stats():
    return store.get_feedback_stats()


@app.post("/retrain")
def trigger_retrain():
    result = retrainer.analyze_and_retrain()
    return result


@app.get("/report")
def full_report():
    return retrainer.get_retraining_report()


@app.get("/health")
def health():
    return {"status": "healthy"}
