"""
Anomaly Detector for Advanced AI Analyzer

Detects unusual incidents that don't match known patterns.
Uses:
- Statistical outlier detection (Isolation Forest)
- Behavioral pattern matching
- Asset-specific baselines
- Zero-day attack pattern detection
"""

import logging
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from sklearn.ensemble import IsolationForest
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class AnomalyResult:
    """Result from anomaly detection."""

    anomaly_score: float  # 0-100, higher = more anomalous
    anomaly_type: str  # "behavioral", "statistical", "temporal", "contextual"
    explanation: str  # Human-readable explanation
    contributing_factors: List[Dict[str, Any]]  # What made it anomalous
    is_zero_day_indicator: bool  # Likely zero-day attack?
    recommended_escalation: bool  # Should escalate to senior analyst?


class AnomalyDetector:
    """
    Multi-method anomaly scoring for detecting unknown/novel attack patterns.
    """

    def __init__(self):
        """Initialize anomaly detector."""
        self.isolation_forest = IsolationForest(
            contamination=0.1, random_state=42, n_estimators=100
        )
        self.trained = False
        self.asset_baselines = {}  # Per-asset behavioral baselines
        self.alert_history = []  # Historical alerts for pattern detection
        self.max_history = 1000  # Keep last 1000 alerts

    def train_on_historical_data(self, historical_incidents: List[Dict]) -> None:
        """
        Train isolation forest on historical incident data.

        Args:
            historical_incidents: List of past incident dicts
        """
        if not historical_incidents or len(historical_incidents) < 10:
            logger.warning("Insufficient historical data for training")
            return

        try:
            # Extract features from historical data
            features = self._extract_feature_vectors(historical_incidents)

            if features.shape[0] > 0:
                self.isolation_forest.fit(features)
                self.trained = True
                logger.info(f"Trained isolation forest on {features.shape[0]} incidents")
            else:
                logger.warning("Could not extract features from historical data")

        except Exception as e:
            logger.error(f"Error training isolation forest: {str(e)}")

    def detect_anomaly(
        self,
        description: str,
        event_type: str = "",
        asset_id: Optional[int] = None,
        metrics: Optional[Dict[str, float]] = None,
    ) -> AnomalyResult:
        """
        Detect if an incident is anomalous (novel/zero-day pattern).

        Args:
            description: Incident description text
            event_type: Type of event
            asset_id: ID of affected asset (for baseline comparison)
            metrics: System metrics (CPU, memory, connections, failed_logins, etc.)

        Returns:
            AnomalyResult with anomaly score and details
        """
        try:
            anomaly_scores = {}
            factors = []

            # Method 1: Statistical outlier detection
            if self.trained:
                stat_score, stat_factors = self._statistical_anomaly(
                    description, event_type
                )
                anomaly_scores["statistical"] = stat_score
                factors.extend(stat_factors)
            else:
                logger.debug("Isolation forest not trained - skipping statistical check")

            # Method 2: Behavioral pattern matching
            behavioral_score, behavioral_factors = self._behavioral_anomaly(
                description, asset_id
            )
            anomaly_scores["behavioral"] = behavioral_score
            factors.extend(behavioral_factors)

            # Method 3: System metrics anomaly
            if metrics:
                metrics_score, metrics_factors = self._metrics_anomaly(
                    metrics, asset_id
                )
                anomaly_scores["metrics"] = metrics_score
                factors.extend(metrics_factors)

            # Method 4: Temporal pattern detection
            temporal_score, temporal_factors = self._temporal_anomaly(description)
            anomaly_scores["temporal"] = temporal_score
            factors.extend(temporal_factors)

            # Aggregate scores (weighted average)
            weights = {
                "statistical": 0.3,
                "behavioral": 0.3,
                "metrics": 0.2,
                "temporal": 0.2,
            }
            avg_score = sum(
                anomaly_scores.get(method, 0) * weight
                for method, weight in weights.items()
            ) / sum(
                weight for method, weight in weights.items() if method in anomaly_scores
            )

            # Determine anomaly type (which method contributed most)
            primary_method = (
                max(anomaly_scores.items(), key=lambda x: x[1])[0]
                if anomaly_scores
                else "unknown"
            )

            # Is this a zero-day indicator?
            is_zero_day = avg_score > 0.7 and primary_method in [
                "statistical",
                "behavioral",
            ]

            logger.debug(
                f"Anomaly detection: score={avg_score:.2f}, "
                f"type={primary_method}, zero_day={is_zero_day}"
            )

            return AnomalyResult(
                anomaly_score=min(avg_score * 100, 100.0),
                anomaly_type=primary_method,
                explanation=self._generate_anomaly_explanation(
                    avg_score, primary_method, factors
                ),
                contributing_factors=factors,
                is_zero_day_indicator=is_zero_day,
                recommended_escalation=avg_score > 0.6,
            )

        except Exception as e:
            logger.error(f"Error in anomaly detection: {str(e)}")
            return AnomalyResult(
                anomaly_score=0.0,
                anomaly_type="error",
                explanation=f"Anomaly detection error: {str(e)}",
                contributing_factors=[],
                is_zero_day_indicator=False,
                recommended_escalation=False,
            )

    def _statistical_anomaly(
        self, description: str, event_type: str
    ) -> Tuple[float, List[Dict]]:
        """
        Detect statistical outliers using isolation forest.

        Returns:
            (anomaly_score 0-1, contributing_factors)
        """
        if not self.trained:
            return 0.0, []

        try:
            # Extract features
            features = self._text_to_features(description, event_type)

            if features is None or len(features) == 0:
                return 0.0, []

            # Get anomaly score from isolation forest
            # Isolation forest returns -1 for outliers, 1 for inliers
            prediction = self.isolation_forest.predict([features])
            anomaly_score = self.isolation_forest.score_samples([features])[0]

            # Convert to 0-1 range (higher = more anomalous)
            normalized_score = max(0, -anomaly_score / 2)  # Heuristic scaling

            factors = (
                [
                    {
                        "factor": "statistical_pattern",
                        "description": "Text pattern does not match historical incidents",
                        "severity": "medium",
                    }
                ]
                if normalized_score > 0.5
                else []
            )

            return normalized_score, factors

        except Exception as e:
            logger.warning(f"Statistical anomaly detection failed: {str(e)}")
            return 0.0, []

    def _behavioral_anomaly(
        self, description: str, asset_id: Optional[int] = None
    ) -> Tuple[float, List[Dict]]:
        """
        Detect behavioral anomalies based on asset baselines.

        Returns:
            (anomaly_score 0-1, contributing_factors)
        """
        factors = []
        score = 0.0

        # Check against asset baseline
        if asset_id and asset_id in self.asset_baselines:
            baseline = self.asset_baselines[asset_id]
            desc_lower = description.lower()

            # Compare to baseline patterns
            baseline_patterns = baseline.get("common_patterns", [])
            matches_baseline = any(p in desc_lower for p in baseline_patterns)

            if not matches_baseline:
                score += 0.3
                factors.append(
                    {
                        "factor": "baseline_deviation",
                        "description": f"Alert pattern not in baseline for asset {asset_id}",
                        "severity": "medium",
                    }
                )

            # Check for known attack vectors
            attack_keywords = baseline.get("attack_keywords", [])
            has_attack_keyword = any(kw in desc_lower for kw in attack_keywords)

            if not has_attack_keyword:
                score += 0.2
                factors.append(
                    {
                        "factor": "unusual_method",
                        "description": "Attack method not commonly seen on this asset",
                        "severity": "low",
                    }
                )

        else:
            # No baseline - can't assess behavioral anomaly well
            logger.debug(f"No behavioral baseline for asset {asset_id}")

        return min(score, 1.0), factors

    def _metrics_anomaly(
        self, metrics: Dict[str, float], asset_id: Optional[int] = None
    ) -> Tuple[float, List[Dict]]:
        """
        Detect anomalies in system metrics (CPU, memory, connections, etc.).

        Args:
            metrics: Dict with keys like: cpu_usage, memory_usage, network_connections,
                     failed_logins, etc. Values should be percentages or counts.

        Returns:
            (anomaly_score 0-1, contributing_factors)
        """
        factors = []
        score = 0.0

        # Get expected baselines (could come from asset profile)
        baselines = {
            "cpu_usage": 40,  # Default: expect ~40% CPU
            "memory_usage": 50,  # Default: expect ~50% memory
            "network_connections": 100,  # Default: expect ~100 connections
            "failed_logins_1h": 5,  # Default: expect <5 failed logins per hour
            "disk_io": 30,  # Default: expect ~30% disk I/O
        }

        # Compare each metric to baseline
        for metric, value in metrics.items():
            if metric in baselines:
                baseline = baselines[metric]
                deviation = abs(value - baseline)
                max_deviation = baseline * 2  # Anything >2x baseline is anomalous

                if deviation > max_deviation:
                    score += 0.15
                    factors.append(
                        {
                            "factor": metric,
                            "baseline": baseline,
                            "current": value,
                            "deviation_pct": (deviation / baseline * 100),
                            "severity": "high" if deviation > max_deviation * 2 else "medium",
                        }
                    )

        return min(score, 1.0), factors

    def _temporal_anomaly(self, description: str) -> Tuple[float, List[Dict]]:
        """
        Detect temporal/time-based anomalies (e.g., activity outside business hours).

        Returns:
            (anomaly_score 0-1, contributing_factors)
        """
        # In a real system, this would check:
        # - After-hours access
        # - Unusual patterns in alert frequency
        # - Rapid escalation
        # For now, return minimal score
        return 0.0, []

    def update_asset_baseline(
        self, asset_id: int, common_patterns: List[str], attack_keywords: List[str]
    ) -> None:
        """
        Update behavioral baseline for an asset.

        Args:
            asset_id: ID of the asset
            common_patterns: Known normal patterns for this asset
            attack_keywords: Attack keywords commonly seen on this asset
        """
        self.asset_baselines[asset_id] = {
            "common_patterns": common_patterns,
            "attack_keywords": attack_keywords,
        }
        logger.debug(f"Updated baseline for asset {asset_id}")

    def _extract_feature_vectors(self, incidents: List[Dict]) -> np.ndarray:
        """
        Extract numerical feature vectors from incident data.

        Returns:
            Array of shape (n_incidents, n_features)
        """
        vectors = []
        for incident in incidents:
            try:
                desc = incident.get("description", "")
                event_type = incident.get("event_type", "")
                features = self._text_to_features(desc, event_type)
                if features is not None:
                    vectors.append(features)
            except Exception as e:
                logger.debug(f"Could not extract features from incident: {str(e)}")

        return np.array(vectors) if vectors else np.array([])

    def _text_to_features(self, description: str, event_type: str) -> Optional[np.ndarray]:
        """
        Convert text to numerical features for isolation forest.

        Features:
        - Text length
        - Word count
        - Unique word count
        - Presence of common words
        - Character diversity
        """
        try:
            combined_text = (description + " " + event_type).lower()
            words = combined_text.split()

            features = [
                len(combined_text),  # Text length
                len(words),  # Word count
                len(set(words)),  # Unique words
                combined_text.count("error"),  # Error mentions
                combined_text.count("failed"),  # Failed mentions
                combined_text.count("denied"),  # Access denied
                combined_text.count("unauthorized"),  # Unauthorized
                combined_text.count("suspicious"),  # Suspicious keywords
                len([c for c in combined_text if c.isdigit()]),  # Digit count
                len(set(combined_text)),  # Character diversity
            ]

            return np.array(features, dtype=float)

        except Exception as e:
            logger.warning(f"Error converting text to features: {str(e)}")
            return None

    def _generate_anomaly_explanation(
        self, score: float, anomaly_type: str, factors: List[Dict]
    ) -> str:
        """Generate human-readable explanation of anomaly."""
        if score < 0.3:
            base = "Normal incident pattern detected."
        elif score < 0.6:
            base = "Mildly anomalous pattern detected."
        else:
            base = "Significantly anomalous pattern detected - possible novel attack."

        # Add method-specific explanation
        method_explanations = {
            "statistical": "Pattern does not match historical incidents (statistical outlier).",
            "behavioral": "Behavior deviates from asset baseline (unusual for this system).",
            "metrics": "System metrics show abnormal deviation.",
            "temporal": "Temporal pattern is unusual.",
        }

        method_text = method_explanations.get(
            anomaly_type, "Pattern analysis indicates anomaly."
        )

        # Add factor details
        factor_text = ""
        if factors:
            factor_text = " Contributing factors: " + "; ".join(
                f["description"] for f in factors[:3]
            )

        return base + " " + method_text + factor_text
