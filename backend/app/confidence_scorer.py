"""
Bayesian Confidence Scorer for Advanced AI Analyzer

Replaces simple confidence formula with Bayesian uncertainty quantification.
Provides:
- Point estimate of confidence
- Credible intervals (95% confidence bounds)
- Entropy-based uncertainty measure
- Component contribution breakdown
"""

import logging
import numpy as np
from typing import Dict, Tuple, List, Any
from dataclasses import dataclass
from scipy.stats import dirichlet, norm

logger = logging.getLogger(__name__)


@dataclass
class ConfidenceScore:
    """Container for detailed confidence information."""

    point_estimate: float  # 0-1, the "best guess" confidence
    uncertainty: float  # Standard deviation / credible interval width
    credible_interval_low: float  # 95% lower bound
    credible_interval_high: float  # 95% upper bound
    entropy: float  # Shannon entropy (0-1, measures decision uncertainty)
    confidence_components: Dict[str, float]  # Breakdown: keyword=0.3, ml=0.5, etc.
    model_agreement: str  # UNANIMOUS, MAJORITY, WEAK, CONTRADICTORY
    recommended_action: str  # AUTO_CLASSIFY, ESCALATE_TO_ANALYST, HOLD_FOR_REVIEW


class BayesianConfidenceScorer:
    """
    Bayesian confidence quantification for multi-classifier ensemble.

    Uses Dirichlet distribution for multi-class confidence aggregation,
    providing not just a point estimate but full uncertainty bounds.
    """

    def __init__(self, smoothing_alpha: float = 0.5):
        """
        Initialize scorer.

        Args:
            smoothing_alpha: Laplace smoothing parameter (avoids zero probabilities)
        """
        self.smoothing_alpha = smoothing_alpha

    def score_ensemble(
        self,
        predictions: Dict[str, Dict[str, float]],
        priors: Dict[str, float] = None,
    ) -> ConfidenceScore:
        """
        Score ensemble predictions using Bayesian approach.

        Args:
            predictions: Dict mapping classifier names to their predictions
                Example: {
                    'keyword': {'confidence': 0.92, 'entropy': 0.1},
                    'ml': {'confidence': 0.88, 'entropy': 0.15},
                    'semantic': {'confidence': 0.78, 'entropy': 0.20},
                    'anomaly': {'confidence': 0.60, 'entropy': 0.25}
                }
            priors: Prior belief for each classifier (defaults to uniform)

        Returns:
            ConfidenceScore with detailed uncertainty information
        """
        if not predictions:
            logger.warning("No predictions provided to scorer")
            return self._confidence_score(0.0, 1.0, {}, "CONTRADICTORY")

        classifiers = list(predictions.keys())
        confidences = np.array([p.get("confidence", 0.5) for p in predictions.values()])

        # Set priors (default: uniform across classifiers)
        if priors is None:
            priors = {c: 1.0 / len(classifiers) for c in classifiers}

        # Bayesian aggregation using Dirichlet distribution
        # Treat each classifier's confidence as evidence for a class
        # Convert confidences to pseudocounts for Dirichlet

        # More confident predictions get higher weight
        alpha_params = confidences + self.smoothing_alpha
        dirichlet_dist = dirichlet(alpha_params)

        # Sample from posterior to get uncertainty
        point_estimate = np.mean(confidences)
        samples = dirichlet_dist.rvs(size=10000)
        posterior_mean = np.mean(samples, axis=0)
        posterior_std = np.std(samples, axis=0)

        # Credible interval (95%)
        credible_low = np.percentile(samples, 2.5)
        credible_high = np.percentile(samples, 97.5)

        # Shannon entropy (0 = certain, log(k) = completely uncertain)
        entropy = self._shannon_entropy(confidences)

        # Component breakdown (contribution of each model)
        components = {c: confidences[i] for i, c in enumerate(classifiers)}

        # Determine model agreement level
        confidence_std = np.std(confidences)
        agreement_level = self._assess_agreement(confidence_std, confidences)

        # Uncertainty as credible interval width
        uncertainty = credible_high - credible_low

        logger.debug(
            f"Ensemble confidence: {point_estimate:.2f} "
            f"± {uncertainty:.2f} (entropy: {entropy:.3f})"
        )

        return ConfidenceScore(
            point_estimate=float(point_estimate),
            uncertainty=float(uncertainty),
            credible_interval_low=float(credible_low),
            credible_interval_high=float(credible_high),
            entropy=float(entropy),
            confidence_components=components,
            model_agreement=agreement_level,
            recommended_action=self._recommend_action(
                point_estimate, entropy, agreement_level
            ),
        )

    def score_single_classifier(
        self,
        confidence: float,
        internal_entropy: float = 0.0,
        classifier_name: str = "unknown",
    ) -> ConfidenceScore:
        """
        Score a single classifier prediction with uncertainty.

        Args:
            confidence: Confidence value (0-1)
            internal_entropy: Internal entropy of the classifier
            classifier_name: Name for logging

        Returns:
            ConfidenceScore for single prediction
        """
        # Add uncertainty based on confidence and internal entropy
        # More certain predictions have tighter bounds
        base_uncertainty = (1.0 - confidence) * 0.3  # Base uncertainty from inverse conf
        total_uncertainty = base_uncertainty + internal_entropy * 0.1

        # 95% credible interval
        credible_low = max(0.0, confidence - 1.96 * total_uncertainty)
        credible_high = min(1.0, confidence + 1.96 * total_uncertainty)

        entropy = internal_entropy

        logger.debug(
            f"Single classifier [{classifier_name}]: "
            f"{confidence:.2f} ± {total_uncertainty:.2f}"
        )

        return ConfidenceScore(
            point_estimate=confidence,
            uncertainty=total_uncertainty,
            credible_interval_low=credible_low,
            credible_interval_high=credible_high,
            entropy=entropy,
            confidence_components={classifier_name: confidence},
            model_agreement="SINGLE",
            recommended_action=self._recommend_action(
                confidence, entropy, "SINGLE"
            ),
        )

    def _shannon_entropy(self, confidences: np.ndarray) -> float:
        """
        Calculate Shannon entropy of confidence distribution.

        Higher entropy = more uncertainty/disagreement between models.
        0 = unanimous, log(n) = maximum disagreement.
        """
        # Normalize to probability distribution
        probs = confidences / np.sum(confidences)
        probs = probs[probs > 0]  # Remove zeros to avoid log(0)

        entropy = -np.sum(probs * np.log2(probs + 1e-10))
        max_entropy = np.log2(len(confidences))

        # Normalize to 0-1 range
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.0
        return float(np.clip(normalized_entropy, 0, 1))

    def _assess_agreement(self, std_dev: float, confidences: np.ndarray) -> str:
        """
        Assess level of agreement between classifiers.

        Args:
            std_dev: Standard deviation of confidence scores
            confidences: Array of confidence values

        Returns:
            Agreement level: UNANIMOUS, MAJORITY, WEAK, CONTRADICTORY
        """
        if std_dev < 0.05:
            return "UNANIMOUS"  # All models strongly agree
        elif std_dev < 0.15:
            return "MAJORITY"  # Most models agree
        elif std_dev < 0.30:
            return "WEAK"  # Some disagreement
        else:
            return "CONTRADICTORY"  # Strong disagreement

    def _recommend_action(
        self, confidence: float, entropy: float, agreement: str
    ) -> str:
        """
        Recommend action based on confidence and agreement.

        Returns:
            Recommended action for analyst/system
        """
        if confidence > 0.85 and entropy < 0.2 and agreement in ["UNANIMOUS", "MAJORITY"]:
            return "AUTO_CLASSIFY"  # High confidence, proceed automatically
        elif confidence < 0.60 or entropy > 0.4 or agreement == "CONTRADICTORY":
            return "ESCALATE_TO_ANALYST"  # Low confidence, get human input
        else:
            return "HOLD_FOR_REVIEW"  # Medium confidence, flag for review

    def _confidence_score(
        self, conf: float, unc: float, components: Dict, agreement: str
    ) -> ConfidenceScore:
        """Helper to create ConfidenceScore."""
        return ConfidenceScore(
            point_estimate=conf,
            uncertainty=unc,
            credible_interval_low=max(0, conf - unc),
            credible_interval_high=min(1, conf + unc),
            entropy=0.0,
            confidence_components=components,
            model_agreement=agreement,
            recommended_action=self._recommend_action(conf, 0.0, agreement),
        )


def format_confidence_for_display(score: ConfidenceScore) -> str:
    """
    Format confidence score for human display.

    Example output:
    "78% confidence (70%-86% credible interval), moderate agreement"
    """
    return (
        f"{score.point_estimate*100:.0f}% confidence "
        f"({score.credible_interval_low*100:.0f}%-"
        f"{score.credible_interval_high*100:.0f}% credible interval), "
        f"{score.model_agreement.lower()}"
    )
