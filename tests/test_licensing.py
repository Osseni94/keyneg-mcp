"""Tests for licensing module."""

import pytest
from datetime import datetime, timedelta
from keyneg_mcp.licensing import (
    LicenseInfo,
    LicenseTier,
    LicenseManager,
)


class TestLicenseInfo:
    """Tests for LicenseInfo dataclass."""

    def test_free_tier_defaults(self):
        """Free tier should have limited features."""
        info = LicenseInfo(tier=LicenseTier.FREE)

        assert info.features["max_sentiment_labels"] == 3
        assert info.features["keywords_enabled"] is False
        assert info.features["batch_enabled"] is False
        assert info.features["max_daily_calls"] == 100

    def test_trial_tier_defaults(self):
        """Trial tier should have full features."""
        info = LicenseInfo(tier=LicenseTier.TRIAL)

        assert info.features["max_sentiment_labels"] == 95
        assert info.features["keywords_enabled"] is True
        assert info.features["batch_enabled"] is True
        assert info.features["max_daily_calls"] == 1000

    def test_pro_tier_defaults(self):
        """Pro tier should have unlimited calls."""
        info = LicenseInfo(tier=LicenseTier.PRO)

        assert info.features["max_sentiment_labels"] == 95
        assert info.features["keywords_enabled"] is True
        assert info.features["max_daily_calls"] is None

    def test_enterprise_tier_defaults(self):
        """Enterprise tier should have custom taxonomy."""
        info = LicenseInfo(tier=LicenseTier.ENTERPRISE)

        assert info.features["custom_taxonomy"] is True
        assert info.features["max_daily_calls"] is None

    def test_valid_license(self):
        """License without expiry should be valid."""
        info = LicenseInfo(tier=LicenseTier.PRO)
        assert info.is_valid is True

    def test_expired_license(self):
        """Expired license should not be valid."""
        info = LicenseInfo(
            tier=LicenseTier.TRIAL,
            expires_at=datetime.now() - timedelta(days=1),
        )
        assert info.is_valid is False

    def test_future_expiry_valid(self):
        """License with future expiry should be valid."""
        info = LicenseInfo(
            tier=LicenseTier.TRIAL,
            expires_at=datetime.now() + timedelta(days=30),
        )
        assert info.is_valid is True


class TestLicenseManager:
    """Tests for LicenseManager."""

    def test_no_key_returns_free(self):
        """No license key should return FREE tier."""
        manager = LicenseManager()
        info = manager.validate_license(None)

        assert info.tier == LicenseTier.FREE

    def test_invalid_key_returns_free(self):
        """Invalid license key should return FREE tier."""
        manager = LicenseManager()
        info = manager.validate_license("invalid-key")

        assert info.tier == LicenseTier.FREE

    def test_valid_pro_key(self):
        """Valid PRO key should return PRO tier."""
        manager = LicenseManager()
        # Format: KEYNEG-{TIER}-{EXPIRY}-{HASH}
        key = "KEYNEG-PRO-NONE-abc123"
        info = manager.validate_license(key)

        assert info.tier == LicenseTier.PRO

    def test_valid_trial_key(self):
        """Valid TRIAL key should return TRIAL tier."""
        manager = LicenseManager()
        key = "KEYNEG-TRIAL-NONE-abc123"
        info = manager.validate_license(key)

        assert info.tier == LicenseTier.TRIAL

    def test_valid_enterprise_key(self):
        """Valid ENTERPRISE key should return ENTERPRISE tier."""
        manager = LicenseManager()
        key = "KEYNEG-ENT-NONE-abc123"
        info = manager.validate_license(key)

        assert info.tier == LicenseTier.ENTERPRISE

    def test_key_with_expiry(self):
        """Key with expiry date should be parsed."""
        manager = LicenseManager()
        key = "KEYNEG-PRO-20301231-abc123"
        info = manager.validate_license(key)

        assert info.tier == LicenseTier.PRO
        assert info.expires_at is not None
        assert info.expires_at.year == 2030

    def test_usage_increment(self):
        """Usage should increment on check."""
        manager = LicenseManager()
        manager.validate_license("KEYNEG-PRO-NONE-abc123")

        initial = manager._daily_calls
        manager.check_and_increment_usage()

        assert manager._daily_calls == initial + 1

    def test_free_tier_limit(self):
        """Free tier should hit daily limit."""
        manager = LicenseManager()
        manager.validate_license(None)  # FREE tier

        # Simulate hitting limit
        manager._daily_calls = 100

        allowed, message = manager.check_and_increment_usage()
        assert allowed is False
        assert "limit" in message.lower()
