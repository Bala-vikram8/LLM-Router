import asyncio
import argparse
import json
import uvicorn
from router.engine import LLMRouter
from feedback.store import FeedbackStore
from feedback.retrainer import FeedbackRetrainer
from router.classifier import ComplexityClassifier


DEMO_QUERIES = [
    "What is the capital of France?",
    "Who wrote Hamlet?",
    "How many days are in a leap year?",
    "Explain how transformers work in machine learning",
    "Write a Python function to parse JSON from a REST API response",
    "Compare the macroeconomic implications of quantitative easing vs interest rate policy",
    "Analyze the trade-offs between microservices and monolithic architecture for a fintech startup",
    "What is 2 + 2?",
    "Debug this Python code: def fib(n): return fib(n-1) + fib(n-2)",
    "Write a comprehensive research report on the impact of AI on global labor markets",
]


def run_demo():
    router = LLMRouter()
    store = FeedbackStore()

    print("\n" + "="*70)
    print("LLM ROUTER: Routing Demo (No API calls)")
    print("="*70)

    decisions = router.route_batch(DEMO_QUERIES)
    for d in decisions:
        store.log_decision(d)

    print(f"\n{'Query':<55} {'Tier':<8} {'Model':<35} {'Cost'}")
    print("-"*110)
    for d in decisions:
        model_short = d.selected_model.split("-")[1] if "-" in d.selected_model else d.selected_model
        print(f"{d.query[:54]:<55} {d.selected_tier.value:<8} {d.selected_model:<35} ${d.estimated_cost_usd:.6f}")

    savings = router.calculate_savings(decisions)
    print(f"\n{'='*70}")
    print(f"SAVINGS REPORT")
    print(f"{'='*70}")
    print(f"Actual cost (smart routing):  ${savings['actual_cost_usd']:.6f}")
    print(f"Baseline cost (all Tier 3):   ${savings['baseline_cost_usd']:.6f}")
    print(f"Savings:                      ${savings['savings_usd']:.6f} ({savings['savings_pct']}%)")


def run_execute(query: str):
    from executor import RouterExecutor
    executor = RouterExecutor()
    result = executor.execute(query)
    print("\n" + "="*70)
    print("RESPONSE")
    print("="*70)
    if "response" in result:
        print(result["response"])
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")


def run_batch():
    from executor import RouterExecutor
    executor = RouterExecutor()
    print("\n" + "="*70)
    print("LLM ROUTER: Batch Execution")
    print("="*70)
    results = executor.execute_batch(DEMO_QUERIES[:5])
    for r in results:
        if "response" in r:
            print(f"\nQ: {r['decision']['query'][:60]}")
            print(f"Model: {r['decision']['selected_model']} | Cost: ${r['actual_cost_usd']:.6f} | Quality: {r['quality_score']}")
            print(f"A: {r['response'][:100]}...")
    savings = executor.get_savings_report()
    print(f"\nTotal savings vs all-Tier3: {savings['savings_pct']}%")


def show_report():
    store = FeedbackStore()
    classifier = ComplexityClassifier()
    retrainer = FeedbackRetrainer(store, classifier)
    report = retrainer.get_retraining_report()
    print("\n" + "="*70)
    print("ROUTER REPORT")
    print("="*70)
    print(json.dumps(report, indent=2))


def run_retrain():
    store = FeedbackStore()
    classifier = ComplexityClassifier()
    retrainer = FeedbackRetrainer(store, classifier)
    result = retrainer.analyze_and_retrain()
    print("\n" + "="*70)
    print("RETRAINING RESULT")
    print("="*70)
    print(json.dumps(result, indent=2))


def start_dashboard():
    print("\nStarting dashboard at http://localhost:8000")
    print("API docs at http://localhost:8000/docs")
    uvicorn.run("dashboard.api:app", host="0.0.0.0", port=8000, reload=True)


def main():
    parser = argparse.ArgumentParser(description="LLM Router CLI")
    parser.add_argument(
        "mode",
        choices=["demo", "execute", "batch", "report", "retrain", "dashboard"],
        help=(
            "demo: route queries without API calls | "
            "execute: route and run a single query | "
            "batch: route and run batch queries | "
            "report: show cost and quality report | "
            "retrain: trigger feedback retraining | "
            "dashboard: start monitoring API"
        ),
    )
    parser.add_argument("--query", type=str, help="Query for execute mode")
    args = parser.parse_args()

    if args.mode == "demo":
        run_demo()
    elif args.mode == "execute":
        query = args.query or "Explain the difference between supervised and unsupervised learning"
        run_execute(query)
    elif args.mode == "batch":
        run_batch()
    elif args.mode == "report":
        show_report()
    elif args.mode == "retrain":
        run_retrain()
    elif args.mode == "dashboard":
        start_dashboard()


if __name__ == "__main__":
    main()
