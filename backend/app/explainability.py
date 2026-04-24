"""
Explainability Engine for Advanced AI Analyzer

Generates human-readable explanations for classification decisions.
Shows:
- Why each model voted the way it did
- How much each model contributed to the final decision
- Where models disagree
- Confidence and uncertainty bounds
- Recommended actions
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class SignalContribution:
    """Represents one signal contributing to classification."""

    signal_name: str  # e.g., "Keyword match", "ML model"
    evidence: List[str] | str  # What evidence triggered this signal
    weight: float  # 0-1, how much this signal contributed
    confidence: float  # 0-1, how confident is this signal
    reasoning: Optional[str] = None  # Why this signal fired


@dataclass
class Contradiction:
    """Represents disagreement between models."""

    model_a: str  # First model name
    prediction_a: str  # What it predicted
    confidence_a: float
    model_b: str  # Second model name
    prediction_b: str  # What it predicted
    confidence_b: float
    explanation: str  # Why this contradiction matters


@dataclass
class Explanation:
    """Complete explainability information for a classification."""

    summary: str  # One-sentence summary
    confidence_story: str  # Narrative about confidence
    contributing_signals: List[SignalContribution]  # What drove the decision
    contradictions: List[Contradiction]  # Where models disagree
    confidence_level: str  # HIGH, MEDIUM, LOW
    recommendation: str  # What to do with this classification
    concerns: List[str]  # Any concerns (e.g., weak semantic agreement)
    model_disagreement: float  # 0-1, entropy of model votes
    explainability_score: float  # 0-1, how explainable is this decision


class ExplainabilityEngine:
    """
    Generates detailed, actionable explanations for SOC operators.

    Answers: Why did the system classify this as X?
    """

    def __init__(self):
        self.severity_levels = {
            "critical": "immediate action required",
            "high": "escalate within 1 hour",
            "medium": "handle within business hours",
            "low": "document and track",
        }

    def generate_explanation(
        self,
        incident_type: str,
        ensemble_result: Dict[str, Any],
        raw_text: str,
        confidence_score,  # ConfidenceScore object
    ) -> Explanation:
        """
        Generate comprehensive explanation for classification decision.

        Args:
            incident_type: Final classified incident type
            ensemble_result: Results from ensemble classifier
            raw_text: Original alert/incident description
            confidence_score: ConfidenceScore object with uncertainty

        Returns:
            Explanation with detailed reasoning
        """
        try:
            # Extract voter predictions
            voters = ensemble_result.get("voter_predictions", {})

            # Generate summary
            summary = self._generate_summary(incident_type, confidence_score)

            # Generate confidence narrative
            confidence_story = self._generate_confidence_narrative(
                incident_type, voters, confidence_score
            )

            # Extract contributing signals
            signals = self._extract_signals(voters, raw_text, ensemble_result)

            # Find contradictions
            contradictions = self._find_contradictions(voters, incident_type)

            # Assess concerns
            concerns = self._assess_concerns(
                confidence_score, contradictions, voters
            )

            # Determine confidence level
            confidence_level = self._assess_confidence_level(confidence_score)

            # Generate recommendation
            recommendation = self._generate_recommendation(
                incident_type, confidence_level, contradictions
            )

            # Calculate explainability score (how well can we explain this?)
            explainability_score = self._calculate_explainability(
                signals, confidence_score, contradictions
            )

            logger.info(
                f"Generated explanation for {incident_type} "
                f"(confidence: {confidence_level}, "
                f"explainability: {explainability_score:.2f})"
            )

            return Explanation(
                summary=summary,
                confidence_story=confidence_story,
                contributing_signals=signals,
                contradictions=contradictions,
                confidence_level=confidence_level,
                recommendation=recommendation,
                concerns=concerns,
                model_disagreement=confidence_score.entropy,
                explainability_score=explainability_score,
            )

        except Exception as e:
            logger.error(f"Error generating explanation: {str(e)}")
            return self._create_fallback_explanation(incident_type)

    def _generate_summary(self, incident_type: str, confidence_score) -> str:
        """Generate one-sentence summary."""
        conf_pct = int(confidence_score.point_estimate * 100)
        return f"{conf_pct}% confidence: {incident_type.replace('_', ' ').title()}"

    def _generate_confidence_narrative(
        self, incident_type: str, voters: Dict, confidence_score
    ) -> str:
        """Generate narrative explanation of confidence."""
        total_models = len(voters)
        strong_agreements = sum(
            1 for v in voters.values() if v.get("confidence", 0) > 0.80
        )

        agreement_text = (
            f"{strong_agreements}/{total_models} models strongly agree"
            if strong_agreements > total_models // 2
            else f"models show mixed confidence (std: {np.std([v.get('confidence', 0.5) for v in voters.values()]):.2f})"
        )

        credible_low = int(confidence_score.credible_interval_low * 100)
        credible_high = int(confidence_score.credible_interval_high * 100)

        return (
            f"{agreement_text}. "
            f"95% credible interval: {credible_low}%-{credible_high}%. "
            f"Model disagreement entropy: {confidence_score.entropy:.2f}"
        )

    def _extract_signals(
        self, voters: Dict, raw_text: str, ensemble_result: Dict
    ) -> List[SignalContribution]:
        """Extract individual signals that drove the classification."""
        signals = []

        # Signal 1: Keyword matches
        if "keyword" in voters:
            keywords = voters["keyword"].get("keywords_matched", [])
            signals.append(
                SignalContribution(
                    signal_name="Keyword Pattern Matching",
                    evidence=keywords if keywords else ["Keyword rule matched"],
                    weight=0.25,  # Default weight from ensemble
                    confidence=voters["keyword"].get("confidence", 0.5),
                    reasoning="Fast, lightweight classifier matching known patterns",
                )
            )

        # Signal 2: ML model (TF-IDF + Random Forest)
        if "ml" in voters:
            signals.append(
                SignalContribution(
                    signal_name="Machine Learning Model (TF-IDF + Random Forest)",
                    evidence=["Trained on historical incident data"],
                    weight=0.40,  # Default weight from ensemble
                    confidence=voters["ml"].get("confidence", 0.5),
                    reasoning="Statistical patterns from historical data",
                )
            )

        # Signal 3: Semantic analysis
        if "semantic" in voters:
            semantic_distance = voters["semantic"].get("distance", None)
            evidence = (
                [f"Semantic similarity: {semantic_distance:.2f}"]
                if semantic_distance
                else ["Semantic NLP analysis"]
            )
            signals.append(
                SignalContribution(
                    signal_name="Semantic & NLP Analysis",
                    evidence=evidence,
                    weight=0.25,  # Default weight from ensemble
                    confidence=voters["semantic"].get("confidence", 0.5),
                    reasoning="Deep language understanding using DistilBERT",
                )
            )

        # Signal 4: Anomaly detection
        if "anomaly" in voters:
            anomaly_score = voters["anomaly"].get("score", 0)
            signals.append(
                SignalContribution(
                    signal_name="Anomaly & Behavioral Detection",
                    evidence=[f"Anomaly score: {anomaly_score:.2f}/100"],
                    weight=0.10,  # Default weight from ensemble
                    confidence=min(anomaly_score / 100, 1.0),
                    reasoning="Detects unusual patterns and zero-day indicators",
                )
            )

        return signals

    def _find_contradictions(
        self, voters: Dict, predicted_type: str
    ) -> List[Contradiction]:
        """Find where different models disagree."""
        contradictions = []

        voter_types = {
            name: data.get("type", "UNKNOWN") for name, data in voters.items()
        }

        # Check all pairs of voters for disagreement
        names = list(voters.keys())
        for i, name_a in enumerate(names):
            for name_b in names[i + 1 :]:
                type_a = voter_types[name_a]
                type_b = voter_types[name_b]

                # Only report if they predicted different types
                if type_a != type_b:
                    contradictions.append(
                        Contradiction(
                            model_a=name_a,
                            prediction_a=type_a.replace("_", " ").title(),
                            confidence_a=voters[name_a].get("confidence", 0.5),
                            model_b=name_b,
                            prediction_b=type_b.replace("_", " ").title(),
                            confidence_b=voters[name_b].get("confidence", 0.5),
                            explanation=f"{name_a} predicted {type_a}, "
                            f"but {name_b} predicted {type_b}. "
                            f"Ensemble chose {predicted_type} via voting.",
                        )
                    )

        return contradictions

    def _assess_concerns(
        self, confidence_score, contradictions: List, voters: Dict
    ) -> List[str]:
        """Identify any concerns about this classification."""
        concerns = []

        # Low confidence
        if confidence_score.point_estimate < 0.70:
            concerns.append(
                f"Confidence below 70% ({confidence_score.point_estimate*100:.0f}%) - "
                "recommend analyst review"
            )

        # High uncertainty
        if confidence_score.uncertainty > 0.25:
            concerns.append(
                f"High uncertainty (credible interval width: {confidence_score.uncertainty*100:.0f}%) - "
                "multiple interpretations possible"
            )

        # Model disagreement
        if confidence_score.model_agreement == "CONTRADICTORY":
            concerns.append(
                "Strong disagreement between models - consider escalation"
            )

        # Some models weak
        weak_models = [
            name
            for name, data in voters.items()
            if data.get("confidence", 0) < 0.60
        ]
        if weak_models:
            concerns.append(f"Weak signal from {', '.join(weak_models)}")

        return concerns

    def _assess_confidence_level(self, confidence_score) -> str:
        """Convert confidence score to user-friendly level."""
        if confidence_score.point_estimate > 0.80 and confidence_score.entropy < 0.2:
            return "HIGH"
        elif confidence_score.point_estimate > 0.60 and confidence_score.entropy < 0.35:
            return "MEDIUM"
        else:
            return "LOW"

    def _generate_recommendation(
        self, incident_type: str, confidence_level: str, contradictions: List
    ) -> str:
        """Generate recommended action."""
        if confidence_level == "HIGH":
            return (
                f"High confidence classification. "
                f"Proceed with {incident_type.replace('_', ' ').title()} playbook."
            )
        elif confidence_level == "MEDIUM":
            return (
                f"Medium confidence. Review analyst recommendations before execution. "
                f"Monitor for false positive indicators."
            )
        else:
            return (
                f"Low confidence - recommend manual analyst review. "
                f"Models show disagreement; escalate to SOC lead."
            )

    def _calculate_explainability(
        self, signals: List[SignalContribution], confidence_score, contradictions: List
    ) -> float:
        """
        Calculate how explainable this decision is (0-1).

        Factors:
        - How many signals contributed (more = better)
        - How confident are those signals
        - Lack of contradictions (disagreement = less explainable)
        """
        signal_score = min(len(signals) / 4.0, 1.0)  # More signals = more explainable
        confidence_score_val = confidence_score.point_estimate
        contradiction_penalty = min(len(contradictions) * 0.1, 0.3)

        explainability = (
            signal_score * 0.4 + confidence_score_val * 0.4 + 0.2
        ) - contradiction_penalty

        return float(np.clip(explainability, 0, 1))

    def _create_fallback_explanation(self, incident_type: str) -> Explanation:
        """Create a minimal explanation when full generation fails."""
        return Explanation(
            summary=f"Classified as {incident_type.replace('_', ' ').title()}",
            confidence_story="Unable to generate detailed confidence narrative",
            contributing_signals=[],
            contradictions=[],
            confidence_level="UNKNOWN",
            recommendation="Unable to generate recommendation - escalate to analyst",
            concerns=["Classification engine error - manual review required"],
            model_disagreement=1.0,
            explainability_score=0.0,
        )


def format_explanation_for_display(explanation: Explanation) -> str:
    """Format explanation for display to SOC operators."""
    lines = [
        f"\n{'='*60}",
        f"CLASSIFICATION EXPLANATION",
        f"{'='*60}",
        f"\nSummary: {explanation.summary}",
        f"Confidence Level: {explanation.confidence_level}",
        f"\n{explanation.confidence_story}",
        f"\nContributing Signals:",
    ]

    for signal in explanation.contributing_signals:
        lines.append(
            f"  • {signal.signal_name}: {signal.confidence*100:.0f}% confidence"
        )
        if isinstance(signal.evidence, list):
            for e in signal.evidence:
                lines.append(f"    - {e}")
        else:
            lines.append(f"    - {signal.evidence}")

    if explanation.contradictions:
        lines.append(f"\nModel Disagreements:")
        for c in explanation.contradictions:
            lines.append(f"  • {c.explanation}")

    if explanation.concerns:
        lines.append(f"\nConcerns:")
        for concern in explanation.concerns:
            lines.append(f"  ⚠ {concern}")

    lines.append(f"\nRecommended Action:")
    lines.append(f"  {explanation.recommendation}")
    lines.append(f"{'='*60}\n")

    return "\n".join(lines)


# Import numpy for calculations
import numpy as np
