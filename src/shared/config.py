"""Compatibility module: re-export settings from core.settings."""
from src.core.settings import get_settings, AppSettings

__all__ = ["get_settings", "AppSettings"]
