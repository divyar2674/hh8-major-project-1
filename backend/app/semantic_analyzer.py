"""
Semantic Analyzer for Advanced AI Analyzer

Uses DistilBERT (lightweight BERT) for semantic understanding.
Features:
- Text embeddings
- Semantic similarity to incident types
- Entity extraction
- Context-aware classification
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from sklearn.metrics.pairwise import cosine_similarity
import hashlib

logger = logging.getLogger(__name__)


class SemanticAnalyzer:
    """
    NLP-based semantic analysis using DistilBERT embeddings.
    """

    def __init__(self, model_name: str = "distilbert-base-uncased", use_gpu: bool = False):
        """
        Initialize semantic analyzer.

        Args:
            model_name: HuggingFace model name (default: DistilBERT)
            use_gpu: Whether to use GPU (not recommended for CPU-bound systems)
        """
        self.model_name = model_name
        self.use_gpu = use_gpu
        self.model = None
        self.tokenizer = None
        self.device = None
        self._loaded = False

        # Incident type descriptions for semantic matching
        self.incident_descriptors = {
            "BRUTE_FORCE": [
                "multiple failed login attempts",
                "password attack",
                "credential attack",
                "unauthorized access attempts",
                "authentication failure",
                "failed login",
                "login brute force",
            ],
            "MALWARE": [
                "malware detected",
                "malicious software",
                "virus infection",
                "trojan",
                "backdoor",
                "rootkit",
                "worm",
                "spyware",
            ],
            "PHISHING": [
                "phishing email",
                "social engineering",
                "credential harvesting",
                "phishing attack",
                "fake login page",
                "malicious link",
            ],
            "DATA_EXFILTRATION": [
                "data leak",
                "data breach",
                "unauthorized data transfer",
                "bulk download",
                "sensitive data transfer",
                "data theft",
            ],
            "PRIVILEGE_ESCALATION": [
                "privilege escalation",
                "elevated privileges",
                "admin rights",
                "sudo access",
                "unauthorized elevation",
                "privilege abuse",
            ],
            "RANSOMWARE": [
                "ransomware attack",
                "encrypted files",
                "ransom demand",
                "encryption attack",
                "files locked",
                "ransom note",
            ],
            "DOS_DDOS": [
                "ddos attack",
                "denial of service",
                "bandwidth exhaustion",
                "flood attack",
                "service disruption",
                "traffic spike",
            ],
            "INSIDER_THREAT": [
                "insider threat",
                "after hours access",
                "policy violation",
                "suspicious activity by employee",
                "unauthorized access by staff",
            ],
        }

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyze text and classify incident type semantically.

        Args:
            text: Incident description or alert text

        Returns:
            Dict with: predicted_type, confidence, semantic_distances, etc.
        """
        try:
            # Lazy load model on first use
            if not self._loaded:
                self._load_model()

            # Generate embedding for input text
            text_embedding = self._get_embedding(text)

            if text_embedding is None:
                logger.warning("Could not generate embedding")
                return self._fallback_analysis(text)

            # Calculate semantic similarity to each incident type
            similarities = {}
            for incident_type, descriptors in self.incident_descriptors.items():
                desc_embeddings = [
                    self._get_embedding(desc) for desc in descriptors
                ]
                desc_embeddings = [e for e in desc_embeddings if e is not None]

                if desc_embeddings:
                    # Average embedding for this type
                    type_embedding = np.mean(desc_embeddings, axis=0)

                    # Cosine similarity
                    similarity = cosine_similarity(
                        text_embedding.reshape(1, -1),
                        type_embedding.reshape(1, -1),
                    )[0][0]
                    similarities[incident_type] = float(similarity)

            # Find best match
            if similarities:
                predicted_type = max(similarities, key=similarities.get)
                confidence = min(
                    similarities[predicted_type], 0.99
                )  # Cap at 99%

                # Also extract entities and context
                entities, context_tags = self._extract_entities(text)

                return {
                    "predicted_type": predicted_type,
                    "confidence": confidence,
                    "semantic_distances": similarities,
                    "key_entities": entities,
                    "key_phrases": context_tags,
                    "context_tags": context_tags,
                    "reasoning": f"Semantic analysis matched '{text}' "
                    f"to {predicted_type} with {confidence:.1%} similarity",
                }

            return self._fallback_analysis(text)

        except Exception as e:
            logger.error(f"Semantic analysis error: {str(e)}")
            return self._fallback_analysis(text)

    def _load_model(self) -> None:
        """Load DistilBERT model and tokenizer."""
        try:
            logger.info(f"Loading semantic model: {self.model_name}")
            from transformers import AutoTokenizer, AutoModel
            import torch

            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name)

            # Set device
            if self.use_gpu:
                try:
                    self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                    self.model.to(self.device)
                except Exception as e:
                    logger.warning(f"GPU not available, using CPU: {str(e)}")
                    self.device = torch.device("cpu")
            else:
                self.device = torch.device("cpu")

            self.model.eval()  # Set to evaluation mode
            self._loaded = True
            logger.info(f"Semantic model loaded successfully (device: {self.device})")

        except ImportError as e:
            logger.error(
                f"Required packages not installed: {str(e)} "
                f"Install with: pip install transformers torch"
            )
            self._loaded = False
        except Exception as e:
            logger.error(f"Failed to load semantic model: {str(e)}")
            self._loaded = False

    def _get_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Get embedding vector for text using DistilBERT.

        Returns:
            Embedding vector or None if model not available
        """
        if not self._loaded or self.model is None:
            return None

        try:
            # Truncate text to max length
            text = text[:512]  # DistilBERT max length

            # Tokenize
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True,
            )

            # Move to device
            if self.device:
                for key in inputs:
                    inputs[key] = inputs[key].to(self.device)

            # Get embeddings
            with __import__("torch").no_grad():
                outputs = self.model(**inputs)

            # Use [CLS] token embedding (first token) as sentence embedding
            cls_embedding = outputs.last_hidden_state[:, 0, :].cpu().numpy()

            return cls_embedding[0]

        except Exception as e:
            logger.warning(f"Error generating embedding: {str(e)}")
            return None

    def _extract_entities(self, text: str) -> Tuple[List[str], List[str]]:
        """
        Extract named entities and key phrases from text.

        Returns:
            (entities, context_tags)
        """
        entities = []
        context_tags = []

        try:
            # Simple entity extraction based on keywords
            text_lower = text.lower()

            # Common threat keywords
            threat_keywords = {
                "attack": "attack_indicator",
                "exploit": "vulnerability_indicator",
                "payload": "malware_indicator",
                "command": "execution_indicator",
                "network": "network_activity",
                "file": "file_system_activity",
                "registry": "system_change",
                "process": "process_execution",
                "credential": "authentication",
                "token": "authentication",
                "session": "session_management",
            }

            for keyword, tag in threat_keywords.items():
                if keyword in text_lower:
                    context_tags.append(tag)

            # Extract potential domains/IPs (simple pattern)
            import re

            ip_pattern = r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
            ips = re.findall(ip_pattern, text)
            entities.extend([f"IP:{ip}" for ip in ips])

            domain_pattern = r"[\w\.-]+\.\w{2,}"
            domains = re.findall(domain_pattern, text)
            entities.extend([f"DOMAIN:{d}" for d in domains[:5]])  # Limit to 5

            return entities[:10], context_tags  # Limit results

        except Exception as e:
            logger.debug(f"Error extracting entities: {str(e)}")
            return [], []

    def _fallback_analysis(self, text: str) -> Dict[str, Any]:
        """Fallback analysis when model not available."""
        return {
            "predicted_type": "UNKNOWN",
            "confidence": 0.3,
            "semantic_distances": {},
            "key_entities": [],
            "key_phrases": [],
            "context_tags": [],
            "reasoning": "Semantic model not available - fallback analysis",
        }
