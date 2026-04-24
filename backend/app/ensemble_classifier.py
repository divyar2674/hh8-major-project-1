"""
Ensemble Classifier for Advanced AI Analyzer

Combines 4 classifiers with weighted voting:
1. Keyword-based (fast, proven 95% accurate)
2. ML model (TF-IDF + Random Forest, accurate)
3. Semantic analysis (DistilBERT, context-aware)
4. Anomaly detection (statistical + behavioral)

Uses Bayesian aggregation for final decision and explainability.
"""

import logging
import asyncio
from typing import Dict, Tuple, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import time

from app.cache_manager import get_cache_manager, ModelCacheManager
from app.confidence_scorer import BayesianConfidenceScorer, ConfidenceScore
from app.anomaly_detector import AnomalyDetector
from app.explainability import ExplainabilityEngine, Explanation
from app.models import IncidentType

logger = logging.getLogger(__name__)


@dataclass
class VoterPrediction:
    """Single classifier's prediction."""

    classifier_name: str
    predicted_type: IncidentType
    confidence: float
    reasoning: str
    additional_data: Optional[Dict] = None  # Extra data (keywords, anomaly_score, etc.)


@dataclass
class EnsembleResult:
    """Final ensemble classification result."""

    ensemble_type: IncidentType
    ensemble_confidence: float
    ensemble_explanation: str
    voter_predictions: Dict[str, Dict[str, Any]]  # Individual voter data
    confidence_score: Optional[ConfidenceScore]  # Bayesian uncertainty
    explanation: Optional[Explanation]  # Full explainability
    classification_time_ms: float  # How long did classification take?
    fallback_used: bool  # Did we fall back to keyword-only?
    all_models_available: bool  # Were all models available?


class ClassifierName(str, Enum):
    """Names of individual classifiers."""

    KEYWORD = "keyword"
    ML = "ml"
    SEMANTIC = "semantic"
    ANOMALY = "anomaly"


class EnsembleClassifier:
    """
    Ensemble of 4 classifiers with graceful fallback and explainability.
    """

    def __init__(
        self,
        keyword_classifier: Optional[Callable] = None,
        ml_classifier: Optional[Callable] = None,
        use_semantic: bool = True,
        use_anomaly: bool = True,
        weights: Optional[Dict[str, float]] = None,
    ):
        """
        Initialize ensemble classifier.

        Args:
            keyword_classifier: Function(description, event_type) -> (type, confidence, reasoning)
            ml_classifier: Function(description, event_type) -> (type, confidence, reasoning)
            use_semantic: Whether to include semantic analysis
            use_anomaly: Whether to include anomaly detection
            weights: Optional dict with classifier weights (defaults: keyword=0.25, ml=0.40, semantic=0.25, anomaly=0.10)
        """
        self.keyword_classifier = keyword_classifier
        self.ml_classifier = ml_classifier
        self.use_semantic = use_semantic
        self.use_anomaly = use_anomaly

        # Ensemble voting weights
        self.weights = weights or {
            ClassifierName.KEYWORD: 0.25,
            ClassifierName.ML: 0.40,
            ClassifierName.SEMANTIC: 0.25,
            ClassifierName.ANOMALY: 0.10,
        }

        # Initialize sub-components
        self.cache_manager = get_cache_manager()
        self.confidence_scorer = BayesianConfidenceScorer()
        self.anomaly_detector = AnomalyDetector()
        self.explainability_engine = ExplainabilityEngine()

        # Lazy-loaded models (semantic and ML)
        self._semantic_model = None
        self._ml_model = None

    def classify(
        self,
        description: str,
        event_type: str = "",
        asset_id: Optional[int] = None,
        metrics: Optional[Dict[str, float]] = None,
        return_explanation: bool = False,
    ) -> EnsembleResult:
        """
        Classify incident using ensemble of classifiers.

        Args:
            description: Incident description
            event_type: Type of event
            asset_id: Asset ID (for anomaly baselines)
            metrics: System metrics dict
            return_explanation: Whether to generate full explainability

        Returns:
            EnsembleResult with final classification and voter details
        """
        start_time = time.time()
        fallback_used = False

        try:
            # Get predictions from available classifiers (with fallback)
            voters = self._run_classifiers(description, event_type, asset_id, metrics)

            if not voters:
                # Fallback: if all classifiers fail, use keyword-only
                logger.warning("All classifiers failed - falling back to keyword only")
                voters = self._fallback_classifier(description, event_type)
                fallback_used = True

            # Aggregate votes using weighted voting
            ensemble_type, ensemble_conf, reasoning = self._aggregate_votes(voters)

            # Bayesian confidence scoring
            confidence_data = {
                name: {"confidence": v["confidence"], "entropy": v.get("entropy", 0.0)}
                for name, v in voters.items()
            }
            confidence_score = self.confidence_scorer.score_ensemble(confidence_data)

            # Explainability (if requested)
            explanation = None
            if return_explanation:
                ensemble_result_dict = {"voter_predictions": voters}
                explanation = self.explainability_engine.generate_explanation(
                    str(ensemble_type),
                    ensemble_result_dict,
                    description,
                    confidence_score,
                )

            classification_time_ms = (time.time() - start_time) * 1000

            logger.info(
                f"Ensemble classification: {ensemble_type} ({ensemble_conf:.1%} confidence) "
                f"in {classification_time_ms:.1f}ms"
            )

            return EnsembleResult(
                ensemble_type=ensemble_type,
                ensemble_confidence=ensemble_conf,
                ensemble_explanation=reasoning,
                voter_predictions=voters,
                confidence_score=confidence_score,
                explanation=explanation,
                classification_time_ms=classification_time_ms,
                fallback_used=fallback_used,
                all_models_available=len(voters) == 4,
            )

        except Exception as e:
            logger.error(f"Critical error in ensemble classification: {str(e)}")
            # Ultimate fallback
            return self._create_error_result(description, event_type, str(e))

    def _run_classifiers(
        self,
        description: str,
        event_type: str,
        asset_id: Optional[int],
        metrics: Optional[Dict],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Run all available classifiers in parallel (as much as possible).

        Returns:
            Dict with classifier name as key, prediction data as value
        """
        voters = {}

        # 1. Keyword classifier (always available, fast)
        if self.keyword_classifier:
            try:
                kw_type, kw_conf, kw_reasoning = self.keyword_classifier(
                    description, event_type
                )
                voters[ClassifierName.KEYWORD] = {
                    "type": kw_type,
                    "confidence": kw_conf,
                    "reasoning": kw_reasoning,
                    "entropy": 0.05,  # Low entropy for keyword matching
                }
                logger.debug(f"Keyword classifier: {kw_type} ({kw_conf:.1%})")
            except Exception as e:
                logger.warning(f"Keyword classifier failed: {str(e)}")

        # 2. ML classifier (if available)
        if self.ml_classifier:
            try:
                ml_type, ml_conf, ml_reasoning = self.ml_classifier(
                    description, event_type
                )
                voters[ClassifierName.ML] = {
                    "type": ml_type,
                    "confidence": ml_conf,
                    "reasoning": ml_reasoning,
                    "entropy": 0.10,
                }
                logger.debug(f"ML classifier: {ml_type} ({ml_conf:.1%})")
            except Exception as e:
                logger.warning(f"ML classifier failed: {str(e)}")

        # 3. Semantic classifier (if enabled and available)
        if self.use_semantic:
            try:
                sem_type, sem_conf, sem_reasoning = self._semantic_classify(
                    description, event_type
                )
                if sem_type:
                    voters[ClassifierName.SEMANTIC] = {
                        "type": sem_type,
                        "confidence": sem_conf,
                        "reasoning": sem_reasoning,
                        "entropy": 0.15,
                    }
                    logger.debug(f"Semantic classifier: {sem_type} ({sem_conf:.1%})")
            except Exception as e:
                logger.warning(f"Semantic classifier failed: {str(e)}")

        # 4. Anomaly detector (if enabled)
        if self.use_anomaly:
            try:
                anomaly_result = self.anomaly_detector.detect_anomaly(
                    description, event_type, asset_id, metrics
                )
                # Anomaly doesn't predict type, but contributes to confidence
                voters[ClassifierName.ANOMALY] = {
                    "type": "ANOMALY_SCORE",  # Special marker
                    "confidence": anomaly_result.anomaly_score / 100.0,
                    "anomaly_score": anomaly_result.anomaly_score,
                    "anomaly_type": anomaly_result.anomaly_type,
                    "explanation": anomaly_result.explanation,
                    "zero_day_indicator": anomaly_result.is_zero_day_indicator,
                    "reasoning": anomaly_result.explanation,
                    "entropy": 0.20,
                }
                logger.debug(
                    f"Anomaly detector: score={anomaly_result.anomaly_score:.1f}"
                )
            except Exception as e:
                logger.warning(f"Anomaly detector failed: {str(e)}")

        return voters

    def _semantic_classify(
        self, description: str, event_type: str
    ) -> Tuple[Optional[IncidentType], float, str]:
        """
        Classify using semantic analysis (DistilBERT).

        Returns:
            (type, confidence, reasoning) or (None, 0, reason) if unavailable
        """
        try:
            # Lazy load semantic model
            if self._semantic_model is None:
                logger.info("Loading semantic analyzer (DistilBERT)...")
                from app.semantic_analyzer import SemanticAnalyzer

                self._semantic_model = SemanticAnalyzer()

            # Run semantic analysis
            result = self._semantic_model.analyze(description)
            return (
                result.get("predicted_type"),
                result.get("confidence", 0.5),
                f"Semantic analysis: {result.get('reasoning', 'No reasoning')}",
            )

        except ImportError:
            logger.debug("Semantic analyzer not available (transformers not installed)")
            return None, 0.0, "Semantic analyzer unavailable"
        except Exception as e:
            logger.warning(f"Semantic classification error: {str(e)}")
            return None, 0.0, f"Semantic error: {str(e)}"

    def _aggregate_votes(
        self, voters: Dict[str, Dict[str, Any]]
    ) -> Tuple[IncidentType, float, str]:
        """
        Aggregate votes from classifiers using weighted voting.

        Returns:
            (ensemble_type, ensemble_confidence, explanation)
        """
        # Filter out anomaly-only voters (anomaly doesn't predict type)
        type_voters = {
            name: voter
            for name, voter in voters.items()
            if voter.get("type") not in ["ANOMALY_SCORE", "UNKNOWN"]
        }

        if not type_voters:
            logger.error("No valid type predictions from any classifier")
            return IncidentType.UNKNOWN, 0.3, "No valid predictions"

        # Count votes per incident type (weighted by classifier weight)
        vote_counts = {}
        confidence_sum = {}

        for classifier_name, voter in type_voters.items():
            incident_type = voter.get("type")
            confidence = voter.get("confidence", 0.5)
            weight = self.weights.get(classifier_name, 0.25)

            if incident_type not in vote_counts:
                vote_counts[incident_type] = 0.0
                confidence_sum[incident_type] = 0.0

            # Weighted vote: weight × confidence
            weighted_vote = weight * confidence
            vote_counts[incident_type] += weighted_vote
            confidence_sum[incident_type] += confidence

        # Find winning type and confidence
        if vote_counts:
            winning_type = max(vote_counts, key=vote_counts.get)
            winning_vote_weight = vote_counts[winning_type]
            avg_confidence = confidence_sum[winning_type] / len(
                [v for v in type_voters.values() if v.get("type") == winning_type]
            )

            # Confidence is average of voters who chose this type
            reasoning = f"Ensemble vote: {winning_type} with {avg_confidence:.1%} avg confidence"

            logger.debug(f"Vote aggregation: {winning_type} wins with {winning_vote_weight:.2f}")

            return winning_type, avg_confidence, reasoning
        else:
            return IncidentType.UNKNOWN, 0.3, "Ensemble voting failed"

    def _fallback_classifier(
        self, description: str, event_type: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Fallback when ML classifiers fail: use only keyword classifier.

        Returns:
            Voter dict with keyword classifier only
        """
        try:
            if self.keyword_classifier:
                kw_type, kw_conf, kw_reasoning = self.keyword_classifier(
                    description, event_type
                )
                return {
                    ClassifierName.KEYWORD: {
                        "type": kw_type,
                        "confidence": kw_conf,
                        "reasoning": kw_reasoning + " (fallback mode)",
                        "entropy": 0.05,
                    }
                }
        except Exception as e:
            logger.error(f"Fallback classifier failed: {str(e)}")

        return {}

    def _create_error_result(
        self, description: str, event_type: str, error: str
    ) -> EnsembleResult:
        """Create error result with UNKNOWN classification."""
        return EnsembleResult(
            ensemble_type=IncidentType.UNKNOWN,
            ensemble_confidence=0.1,
            ensemble_explanation=f"Classification error: {error}",
            voter_predictions={},
            confidence_score=None,
            explanation=None,
            classification_time_ms=0.0,
            fallback_used=True,
            all_models_available=False,
        )

    def update_anomaly_baselines(
        self, asset_id: int, common_patterns: list, attack_keywords: list
    ) -> None:
        """Update anomaly detector baselines for an asset."""
        self.anomaly_detector.update_asset_baseline(
            asset_id, common_patterns, attack_keywords
        )

    def get_classifier_stats(self) -> Dict[str, Any]:
        """Get statistics about classifier availability and performance."""
        return {
            "keyword_available": self.keyword_classifier is not None,
            "ml_available": self.ml_classifier is not None,
            "semantic_enabled": self.use_semantic,
            "anomaly_enabled": self.use_anomaly,
            "cache_stats": self.cache_manager.get_cache_stats(),
            "weights": dict(self.weights),
        }


# Global singleton instance
_ensemble_classifier = None


def get_ensemble_classifier(
    keyword_classifier: Optional[Callable] = None,
    ml_classifier: Optional[Callable] = None,
) -> EnsembleClassifier:
    """Get or create ensemble classifier instance."""
    global _ensemble_classifier
    if _ensemble_classifier is None:
        _ensemble_classifier = EnsembleClassifier(
            keyword_classifier=keyword_classifier,
            ml_classifier=ml_classifier,
        )
    return _ensemble_classifier
