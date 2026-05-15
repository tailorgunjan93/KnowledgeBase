"""Compatibility module: re-export settings from core.settings."""
from src.core.settings import AppSettings, get_settings

__all__ = ["get_settings", "AppSettings"]
