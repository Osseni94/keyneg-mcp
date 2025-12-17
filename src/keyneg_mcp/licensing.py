"""
License validation and tier management for KeyNeg MCP Server.

Tiers:
- FREE: Limited to 3 sentiment labels, no keywords, 100 calls/day
- TRIAL: Full features, 30 days or 1000 calls
- PRO: Full features, unlimited
- ENTERPRISE: Full features + custom taxonomies

Author: Kaossara Osseni
Email: admin@grandnasser.com
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class LicenseTier(Enum):
    FREE = "free"
    TRIAL = "trial"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass
class LicenseInfo:
    tier: LicenseTier
    expires_at: Optional[datetime] = None
    calls_remaining: Optional[int] = None
    domain: Optional[str] = None
    features: dict = None

    def __post_init__(self):
        if self.features is None:
            self.features = self._default_features()

    def _default_features(self) -> dict:
        """Default features based on tier."""
        if self.tier == LicenseTier.FREE:
            return {
                "max_sentiment_labels": 3,
                "keywords_enabled": False,
                "batch_enabled": False,
                "custom_taxonomy": False,
                "max_daily_calls": 100,
            }
        elif self.tier == LicenseTier.TRIAL:
            return {
                "max_sentiment_labels": 95,
                "keywords_enabled": True,
                "batch_enabled": True,
                "custom_taxonomy": False,
                "max_daily_calls": 1000,
            }
        elif self.tier == LicenseTier.PRO:
            return {
                "max_sentiment_labels": 95,
                "keywords_enabled": True,
                "batch_enabled": True,
                "custom_taxonomy": False,
                "max_daily_calls": None,  # Unlimited
            }
        else:  # ENTERPRISE
            return {
                "max_sentiment_labels": 95,
                "keywords_enabled": True,
                "batch_enabled": True,
                "custom_taxonomy": True,
                "max_daily_calls": None,  # Unlimited
            }

    @property
    def is_valid(self) -> bool:
        """Check if license is still valid."""
        if self.expires_at and datetime.now() > self.expires_at:
            return False
        if self.calls_remaining is not None and self.calls_remaining <= 0:
            return False
        return True

    @property
    def is_limited(self) -> bool:
        """Check if this is a limited tier."""
        return self.tier in (LicenseTier.FREE, LicenseTier.TRIAL)


class LicenseManager:
    """Manages license validation and usage tracking."""

    def __init__(self):
        self._license_info: Optional[LicenseInfo] = None
        self._usage_file = self._get_usage_file_path()
        self._daily_calls = 0
        self._last_reset_date: Optional[str] = None
        self._load_usage()

    def _get_usage_file_path(self) -> Path:
        """Get path to usage tracking file."""
        cache_dir = Path.home() / ".keyneg" / "mcp"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / "usage.json"

    def _load_usage(self):
        """Load usage data from file."""
        if self._usage_file.exists():
            try:
                with open(self._usage_file) as f:
                    data = json.load(f)
                    self._daily_calls = data.get("daily_calls", 0)
                    self._last_reset_date = data.get("last_reset_date")
            except Exception:
                pass

        # Reset daily counter if new day
        today = datetime.now().strftime("%Y-%m-%d")
        if self._last_reset_date != today:
            self._daily_calls = 0
            self._last_reset_date = today
            self._save_usage()

    def _save_usage(self):
        """Save usage data to file."""
        try:
            with open(self._usage_file, "w") as f:
                json.dump({
                    "daily_calls": self._daily_calls,
                    "last_reset_date": self._last_reset_date,
                }, f)
        except Exception:
            pass

    def validate_license(self, license_key: Optional[str] = None) -> LicenseInfo:
        """
        Validate license key and return license info.

        Checks in order:
        1. Provided license_key parameter
        2. KEYNEG_LICENSE_KEY environment variable
        3. ~/.keyneg/license.key file
        4. Falls back to FREE tier
        """
        # Try to get license key from various sources
        key = license_key or os.environ.get("KEYNEG_LICENSE_KEY")

        if not key:
            license_file = Path.home() / ".keyneg" / "license.key"
            if license_file.exists():
                key = license_file.read_text().strip()

        if not key:
            # No license key - return FREE tier
            self._license_info = LicenseInfo(tier=LicenseTier.FREE)
            return self._license_info

        # Validate the key format and decode
        try:
            license_info = self._decode_license_key(key)
            self._license_info = license_info
            return license_info
        except Exception:
            # Invalid key - return FREE tier
            self._license_info = LicenseInfo(tier=LicenseTier.FREE)
            return self._license_info

    def _decode_license_key(self, key: str) -> LicenseInfo:
        """
        Decode and validate a license key.

        Key format: KEYNEG-{TIER}-{EXPIRY}-{DOMAIN_HASH}-{CHECKSUM}
        Example: KEYNEG-PRO-20251231-a1b2c3d4-e5f6g7h8
        """
        parts = key.split("-")

        if len(parts) < 4 or parts[0] != "KEYNEG":
            raise ValueError("Invalid license key format")

        tier_str = parts[1].upper()

        # Map tier string to enum
        tier_map = {
            "FREE": LicenseTier.FREE,
            "TRIAL": LicenseTier.TRIAL,
            "PRO": LicenseTier.PRO,
            "ENT": LicenseTier.ENTERPRISE,
            "ENTERPRISE": LicenseTier.ENTERPRISE,
        }

        tier = tier_map.get(tier_str, LicenseTier.FREE)

        # Parse expiry date
        expires_at = None
        if len(parts) > 2 and parts[2] != "NONE":
            try:
                expires_at = datetime.strptime(parts[2], "%Y%m%d")
            except ValueError:
                pass

        # For trial, set 30 days from first use if no expiry
        if tier == LicenseTier.TRIAL and expires_at is None:
            trial_start_file = Path.home() / ".keyneg" / "trial_start"
            if trial_start_file.exists():
                start_date = datetime.fromisoformat(trial_start_file.read_text().strip())
            else:
                start_date = datetime.now()
                trial_start_file.parent.mkdir(parents=True, exist_ok=True)
                trial_start_file.write_text(start_date.isoformat())
            expires_at = start_date + timedelta(days=30)

        return LicenseInfo(
            tier=tier,
            expires_at=expires_at,
        )

    def check_and_increment_usage(self) -> tuple[bool, str]:
        """
        Check if usage is allowed and increment counter.

        Returns:
            (allowed: bool, message: str)
        """
        if self._license_info is None:
            self.validate_license()

        info = self._license_info

        # Check if license is valid
        if not info.is_valid:
            if info.expires_at and datetime.now() > info.expires_at:
                return False, "License has expired. Please renew at grandnasser.com"
            return False, "License is not valid"

        # Check daily call limit
        max_calls = info.features.get("max_daily_calls")
        if max_calls is not None:
            if self._daily_calls >= max_calls:
                return False, f"Daily call limit ({max_calls}) reached. Upgrade at grandnasser.com"

        # Increment usage
        self._daily_calls += 1
        self._save_usage()

        return True, "OK"

    def get_feature(self, feature_name: str, default=None):
        """Get a feature value from current license."""
        if self._license_info is None:
            self.validate_license()
        return self._license_info.features.get(feature_name, default)

    @property
    def current_tier(self) -> LicenseTier:
        """Get current license tier."""
        if self._license_info is None:
            self.validate_license()
        return self._license_info.tier

    @property
    def usage_info(self) -> dict:
        """Get current usage information."""
        if self._license_info is None:
            self.validate_license()

        max_calls = self._license_info.features.get("max_daily_calls")
        return {
            "tier": self._license_info.tier.value,
            "daily_calls_used": self._daily_calls,
            "daily_calls_limit": max_calls,
            "calls_remaining": None if max_calls is None else max(0, max_calls - self._daily_calls),
            "expires_at": self._license_info.expires_at.isoformat() if self._license_info.expires_at else None,
        }


# Global license manager instance
license_manager = LicenseManager()
