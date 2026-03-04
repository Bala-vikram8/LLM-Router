# LLM Router

Most teams using LLMs send every single query to the same expensive model.
A simple question like "what is the capital of France" costs the same as a
deep technical analysis. At scale that wastes 60 to 75 percent of your budget.

LLM Router fixes this. It looks at each query, figures out how complex it
actually is, and sends it to the cheapest model that can handle it well.
Simple questions go to fast cheap models. Complex analysis goes to powerful
models. And the system learns from real usage over time so routing decisions
get better the more you use it.

---

## How It Works

Every query goes through three steps.

**Step 1: Classify the query**
The classifier reads the query and scores it on complexity from 0 to 1.
It looks at word count, sentence structure, domain keywords, and reasoning
depth. This takes under 10ms and does not call any LLM.

**Step 2: Pick the right model**
Based on the complexity score and domain, the router picks a model tier.
Simple factual questions go to Tier 1. Coding and moderate reasoning go
to Tier 2. Complex analysis and high stakes tasks go to Tier 3. Certain
keywords like medical diagnosis or compliance review always force Tier 3
regardless of complexity score.

**Step 3: Learn from feedback**
After every response the system collects quality signals automatically.
When a pattern of low quality responses is detected for a specific type
of query, the router automatically adjusts to send that pattern to a
more capable model next time.

---

## Model Tiers

| Tier | Model | Cost per 1K tokens | Best for |
|---|---|---|---|
| Tier 1 | Claude Haiku | $0.00025 | Simple questions, lookups, chat |
| Tier 2 | Claude Sonnet | $0.003 | Coding, reasoning, summaries |
| Tier 3 | Claude Opus | $0.015 | Deep analysis, high stakes tasks |

---

## Setup

You need Python 3.11 or higher and an Anthropic API key.
```bash
git clone https://github.com/yourusername/llm-router
cd llm-router
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Open the `.env` file and add your Anthropic API key.
```
ANTHROPIC_API_KEY=your_key_here
```

---

## Running It

**See routing decisions without making any API calls**
```bash
python main.py demo
```
Routes 10 sample queries from simple to complex. Shows which model each
query gets routed to and the total cost savings compared to sending
everything to Tier 3.

**Run a single real query**
```bash
python main.py execute --query "Explain how transformers work"
```

**Run a batch of real queries**
```bash
python main.py batch
```

**See your cost and quality report**
```bash
python main.py report
```

**Trigger the feedback retrainer**
```bash
python main.py retrain
```

**Start the monitoring dashboard**
```bash
python main.py dashboard
```
Opens at http://localhost:8000. Full API docs at http://localhost:8000/docs.

---

## Dashboard API

| Method | Endpoint | What it does |
|---|---|---|
| POST | /route | Route a query and get the routing decision back |
| POST | /feedback | Submit a quality rating for a completed query |
| GET | /decisions | See all recent routing decisions |
| GET | /stats/cost | Cost breakdown by model tier |
| GET | /stats/quality | Quality scores by model tier |
| POST | /retrain | Trigger the feedback retraining cycle |
| GET | /report | Full cost and quality summary |

---

## Using It in Your Own Code
```python
from router.engine import LLMRouter
from feedback.store import FeedbackStore

router = LLMRouter()
store = FeedbackStore()

decision = router.route("Analyze the trade-offs between microservices and monolithic architecture")
store.log_decision(decision)

print(decision.selected_model)
print(decision.selected_tier.value)
print(f"Estimated cost: ${decision.estimated_cost_usd:.6f}")
print(decision.reasoning)
```

---

## Real World Impact

On a typical workload of 100,000 queries per day with a normal mix of
simple and complex queries, this router saves 60 to 75 percent of LLM
costs compared to sending everything to a powerful model. The feedback
loop makes sure quality stays high as costs go down.

---

## Tech Stack

Python 3.11, Anthropic Claude API, FastAPI, Pydantic v2, SQLite, Uvicorn

---

## Contributing

Good areas to contribute: adding OpenAI and Gemini model support,
building an LLM-based quality judge to replace the heuristic scorer,
adding streaming response support, and Prometheus metrics integration.
