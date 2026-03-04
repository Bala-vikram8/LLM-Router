from feedback.store import FeedbackStore
from router.models import ModelTier, ComplexityLevel, QueryDomain
from router.classifier import ComplexityClassifier
from typing import List


TIER_UP = {
    ModelTier.TIER_1: ModelTier.TIER_2,
    ModelTier.TIER_2: ModelTier.TIER_3,
    ModelTier.TIER_3: ModelTier.TIER_3,
}


class FeedbackRetrainer:
    def __init__(self, store: FeedbackStore, classifier: ComplexityClassifier):
        self.store = store
        self.classifier = classifier
        self.retrain_threshold = 5
        self.quality_threshold = 0.5

    def analyze_and_retrain(self) -> dict:
        low_quality = self.store.get_low_quality_decisions(
            quality_threshold=self.quality_threshold
        )

        if not low_quality:
            return {"status": "no_action", "reason": "No low quality decisions found"}

        pattern_counts: dict[tuple, list] = {}
        for decision in low_quality:
            key = (decision["complexity"], decision["domain"], decision["selected_tier"])
            if key not in pattern_counts:
                pattern_counts[key] = []
            pattern_counts[key].append(decision["response_quality"])

        adjustments = []
        for (complexity, domain, tier), qualities in pattern_counts.items():
            if len(qualities) >= self.retrain_threshold:
                avg_quality = sum(qualities) / len(qualities)
                current_tier = ModelTier(tier)
                new_tier = TIER_UP[current_tier]

                if new_tier != current_tier:
                    adjustments.append({
                        "complexity": complexity,
                        "domain": domain,
                        "old_tier": tier,
                        "new_tier": new_tier.value,
                        "sample_count": len(qualities),
                        "avg_quality": round(avg_quality, 3),
                    })
                    self.classifier.update_override(
                        pattern=f"{complexity}:{domain}",
                        tier=new_tier,
                    )

        return {
            "status": "retrained" if adjustments else "no_changes",
            "adjustments": adjustments,
            "low_quality_samples_analyzed": len(low_quality),
        }

    def get_retraining_report(self) -> dict:
        stats = self.store.get_feedback_stats()
        cost = self.store.get_cost_summary()

        tier_quality = stats.get("quality_by_tier", {})
        recommendations = []

        for tier, data in tier_quality.items():
            if data["avg_quality"] < 0.6 and data["count"] >= 3:
                recommendations.append(
                    f"Tier {tier} has low avg quality ({data['avg_quality']:.2f}) "
                    f"across {data['count']} queries. Consider upgrading threshold."
                )

        return {
            "feedback_stats": stats,
            "cost_summary": cost,
            "recommendations": recommendations,
        }
