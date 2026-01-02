"""
Configuration Management for Career Copilot

This module centralizes all configuration settings to avoid hardcoding
values throughout the codebase.
"""

import os
from dotenv import load_dotenv

# Load environment variables once at module level
load_dotenv()


class Config:
    """Main configuration class for Career Copilot"""

    # ==================== API Configuration ====================
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

    # ==================== LLM Models ====================
    RESUME_LLM_MODEL = "gemini-2.5-flash"
    JD_LLM_MODEL = "gemini-2.5-flash"
    MATCHING_LLM_MODEL = "gemini-2.5-flash"

    # ==================== File Processing ====================
    PDF_UPLOAD_TIMEOUT_SECONDS = 60
    MAX_PDF_UPLOAD_ATTEMPTS = 60
    MAX_PDF_SIZE_MB = 10

    # ==================== Display Settings ====================
    MAX_SKILLS_DISPLAY = 10
    DEFAULT_PDF_VIEWER_HEIGHT = 800
    CHUNK_PREVIEW_LENGTH = 200

    # ==================== Matching Configuration ====================
    # Rough matching settings
    ROUGH_MATCH_TOP_K = 50

    # Precise matching settings
    PRECISE_MATCH_TOP_N = 10

    # Hybrid matching settings
    HYBRID_ROUGH_TOP_K = 50
    HYBRID_PRECISE_TOP_N = 10

    # Score thresholds
    MIN_MATCH_SCORE = 60
    STRONG_MATCH_THRESHOLD = 80
    GOOD_MATCH_THRESHOLD = 65
    PARTIAL_MATCH_THRESHOLD = 50

    # ==================== Storage Paths ====================
    CHROMA_DB_PATH = "./chroma_db"
    CACHE_DIR = "./cache"
    RESUME_CACHE_DIR = "./cache/resume_extractions"
    PDF_STORAGE_DIR = "./pdf_storage"
    LOG_DIR = "./logs"

    # ==================== Cache Settings ====================
    ENABLE_CACHE = True
    CACHE_MAX_AGE_DAYS = 30

    # ==================== Logging ====================
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # ==================== Batch Processing ====================
    BATCH_PROGRESS_UPDATE_INTERVAL = 1  # Update progress every N files

    # ==================== Text Processing ====================
    MAX_CHUNK_SIZE = 512  # Maximum characters per chunk
    MIN_CHUNK_SIZE = 50   # Minimum characters per chunk

    @classmethod
    def validate(cls):
        """Validate required configuration settings"""
        if not cls.GOOGLE_API_KEY:
            raise ValueError(
                "GOOGLE_API_KEY not found in environment. "
                "Please set it in your .env file."
            )

    @classmethod
    def get_model_name(cls, model_type: str) -> str:
        """
        Get model name by type

        Args:
            model_type: One of 'resume', 'jd', 'matching'

        Returns:
            Model name string
        """
        model_map = {
            'resume': cls.RESUME_LLM_MODEL,
            'jd': cls.JD_LLM_MODEL,
            'matching': cls.MATCHING_LLM_MODEL
        }
        return model_map.get(model_type, cls.RESUME_LLM_MODEL)


# Validate configuration on import
try:
    Config.validate()
except ValueError as e:
    # Don't fail on import, but warn
    import warnings
    warnings.warn(f"Configuration validation failed: {e}")
