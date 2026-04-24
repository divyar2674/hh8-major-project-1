from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str  # Must be provided via .env or environment variable
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    DATABASE_URL: str = "sqlite+aiosqlite:///./incidents.db"
    ENVIRONMENT: str = "development"

    # Advanced AI Analyzer Configuration
    # Feature Flags
    USE_ML_ENSEMBLE: bool = True  # Master switch for ML features
    USE_SEMANTIC_ANALYSIS: bool = True  # Enable DistilBERT semantic analysis
    USE_ANOMALY_DETECTION: bool = True  # Enable statistical anomaly detection
    USE_CONFIDENCE_UNCERTAINTY: bool = True  # Enable Bayesian confidence bounds

    # Model Selection
    SEMANTIC_MODEL: str = "distilbert-base-uncased"  # HuggingFace model name
    SEMANTIC_USE_GPU: bool = False  # Don't use GPU by default

    # Performance Tuning
    ML_CLASSIFICATION_TIMEOUT_MS: int = 200  # Max time for ML classification
    SEMANTIC_TIMEOUT_MS: int = 150  # Max time for semantic analysis
    MODEL_CACHE_MAX_SIZE_MB: int = 500  # Max model cache size in MB
    CACHE_VECTORIZATIONS: bool = True  # Cache computed vectorizations

    # Ensemble Voting Weights (must sum to 1.0)
    KEYWORD_WEIGHT: float = 0.25  # Fast baseline classifier
    ML_WEIGHT: float = 0.40  # Trained ML model (TF-IDF + RF)
    SEMANTIC_WEIGHT: float = 0.25  # NLP semantic analysis
    ANOMALY_WEIGHT: float = 0.10  # Anomaly detection

    # Fallback & Safety
    FALLBACK_ON_ML_ERROR: bool = True  # Use keyword if ML fails
    MIN_CONFIDENCE_FOR_AUTO_ACTION: float = 0.75  # Minimum for auto execution
    ENABLE_EXPLAINABILITY: bool = True  # Generate detailed explanations

    # Uncertainty Thresholds
    CONFIDENCE_UNCERTAINTY_THRESHOLD: float = 0.15  # Flag uncertain predictions
    HIGH_CONFIDENCE_THRESHOLD: float = 0.80  # For automatic actions
    LOW_CONFIDENCE_THRESHOLD: float = 0.60  # Escalate below this

    class Config:
        env_file = ".env"


settings = Settings()


def get_config() -> Settings:
    """Get the application configuration."""
    return settings


def get_ai_config() -> dict:
    """Get AI-specific configuration as dict."""
    return {
        "use_ml_ensemble": settings.USE_ML_ENSEMBLE,
        "use_semantic_analysis": settings.USE_SEMANTIC_ANALYSIS,
        "use_anomaly_detection": settings.USE_ANOMALY_DETECTION,
        "use_confidence_uncertainty": settings.USE_CONFIDENCE_UNCERTAINTY,
        "semantic_model": settings.SEMANTIC_MODEL,
        "ensemble_weights": {
            "keyword": settings.KEYWORD_WEIGHT,
            "ml": settings.ML_WEIGHT,
            "semantic": settings.SEMANTIC_WEIGHT,
            "anomaly": settings.ANOMALY_WEIGHT,
        },
        "thresholds": {
            "high_confidence": settings.HIGH_CONFIDENCE_THRESHOLD,
            "low_confidence": settings.LOW_CONFIDENCE_THRESHOLD,
            "auto_action_min": settings.MIN_CONFIDENCE_FOR_AUTO_ACTION,
            "uncertainty": settings.CONFIDENCE_UNCERTAINTY_THRESHOLD,
        },
        "performance": {
            "ml_timeout_ms": settings.ML_CLASSIFICATION_TIMEOUT_MS,
            "semantic_timeout_ms": settings.SEMANTIC_TIMEOUT_MS,
            "cache_size_mb": settings.MODEL_CACHE_MAX_SIZE_MB,
        },
    }


