"""
Tests for configuration management
"""

import pytest
from config import Config


class TestConfig:
    """Test configuration settings"""

    def test_config_has_required_fields(self):
        """Test that all required configuration fields exist"""
        assert hasattr(Config, 'GOOGLE_API_KEY')
        assert hasattr(Config, 'RESUME_LLM_MODEL')
        assert hasattr(Config, 'MATCHING_LLM_MODEL')
        assert hasattr(Config, 'CHROMA_DB_PATH')

    def test_model_name_getter(self):
        """Test the get_model_name method"""
        assert Config.get_model_name('resume') == Config.RESUME_LLM_MODEL
        assert Config.get_model_name('jd') == Config.JD_LLM_MODEL
        assert Config.get_model_name('matching') == Config.MATCHING_LLM_MODEL

    def test_score_thresholds(self):
        """Test that score thresholds are logical"""
        assert Config.STRONG_MATCH_THRESHOLD > Config.GOOD_MATCH_THRESHOLD
        assert Config.GOOD_MATCH_THRESHOLD > Config.PARTIAL_MATCH_THRESHOLD
        assert Config.PARTIAL_MATCH_THRESHOLD >= 0
        assert Config.STRONG_MATCH_THRESHOLD <= 100

    def test_path_configurations(self):
        """Test that paths are configured"""
        assert isinstance(Config.CHROMA_DB_PATH, str)
        assert isinstance(Config.PDF_STORAGE_DIR, str)
        assert isinstance(Config.LOG_DIR, str)
