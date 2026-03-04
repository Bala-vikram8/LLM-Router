# LLM Router

A cost-quality optimized LLM routing system with a continuous feedback loop. Routes every query to the cheapest model that can handle it well, and learns from quality signals over time to improve routing decisions.

## The Problem

Every company using LLMs is sending every query to the same expensive model regardless of complexity. A simple factual question costs the same as a deep technical analysis. At scale this wastes 60 to 80 percent of your LLM budget.

Existing solutions like RouteLLM use static rules that never update. When your query distribution changes, routing quality silently degrades.

## What This Builds

A three component system that solves this at production scale.

**Component 1: Complexity Classifier**
Scores every incoming query across reasoning depth, domain specificity, and output sensitivity. Produces a complexity score from 0 to 1 in under 10ms without calling any LLM.

**Component 2: Routing Engine**
Maps complexity scores and domains to model tiers. Applies domain-specific floor rules so coding and analysis queries never get sent to underpowered models. High-stakes keywords like medical diagnosis or compliance review force Tier 3 regardless of complexity score.

**Component 3: Feedback Loop**
Collects quality signals after every response. When a pattern of low quality responses is detected for a specific complexity and domain combination, the routing threshold is automatically adjusted upward. Routing gets smarter over time.

---

## Model Tiers

| Tier | Model | Input Cost/1K | Use Case |
|---|---|---|---|
| Tier 1 | claude-haiku-4-5 | $0.00025 | Simple factual, conversational |
| Tier 2 | claude-sonnet-4 | $0.003 | Moderate reasoning, coding |
| Tier 3 | claude-opus-4 | $0.015 | Complex analysis, high stakes |

---

## Setup

**Prerequisites**
- Python 3.11+
- Anthropic API key

**Installation**

```bash
git clone https://github.com/yourusername/llm-router
cd llm-router
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Add your Anthropic API key to `.env`.

---

## Running the Project

**Demo mode (no API calls, just routing decisions)**
```bash
python main.py demo
```
Routes 10 sample queries across all complexity levels. Shows tier assignment, model selection, and cost savings vs routing everything to Tier 3.

**Execute a single query (calls real API)**
```bash
python main.py execute --query "Explain transformer attention mechanisms"
```

**Batch execution (calls real API)**
```bash
python main.py batch
```

**View cost and quality report**
```bash
python main.py report
```

**Trigger feedback retraining**
```bash
python main.py retrain
```

**Start the monitoring dashboard**
```bash
python main.py dashboard
```
Open http://localhost:8000/docs for the full API.

---

## Dashboard API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | /route | Route a query and get routing decision |
| POST | /feedback | Submit quality feedback for a decision |
| GET | /decisions | All recent routing decisions |
| GET | /stats/cost | Cost breakdown by tier |
| GET | /stats/quality | Quality scores by tier |
| POST | /retrain | Trigger feedback retraining |
| GET | /report | Full cost and quality report |

---

## Using the Router in Your Own Code

```python
from router.engine import LLMRouter
from feedback.store import FeedbackStore

router = LLMRouter()
store = FeedbackStore()

decision = router.route("Explain the implications of transformer architecture on LLM scaling")
store.log_decision(decision)

print(f"Model: {decision.selected_model}")
print(f"Tier: {decision.selected_tier.value}")
print(f"Estimated cost: ${decision.estimated_cost_usd:.6f}")
print(f"Reasoning: {decision.reasoning}")
```

---

## The Feedback Loop in Detail

After each response the system collects quality signals automatically. Response length, uncertainty phrases, keyword overlap, and optional user ratings all contribute to a quality score.

When a specific complexity and domain combination consistently produces low quality scores across 5 or more samples, the retrainer upgrades the routing threshold for that pattern. A query that was being routed to Tier 1 might get promoted to Tier 2 after the system learns that pattern needs more model capability.

This is what separates this from a keyword classifier. The routing table is not static. It evolves with your actual traffic.

---

## Why This Matters

At 100,000 queries per day with a typical distribution of simple to complex queries, smart routing saves approximately 65 to 75 percent of LLM costs compared to routing everything to a powerful model. The feedback loop ensures quality does not degrade as savings increase.

---

## Tech Stack

- Python 3.11
- Anthropic Claude API
- FastAPI
- Pydantic v2
- SQLite
- Uvicorn

---

## Contributing

Priority areas: LLM-based complexity judge to replace heuristic classifier, multi-provider support for OpenAI and Gemini models, streaming response support, Prometheus metrics integration.
