"""Localization utility for multi-language support."""

import json
from pathlib import Path

LOCALES_DIR = Path("locales")

class LocalizationService:
    """Loads and provides translated strings."""

    def __init__(self) -> None:
        self.cache: dict[str, dict[str, str]] = {}

    def _load_locale(self, language: str, module: str) -> dict[str, str]:
        """Load a JSON file for a specific language and module."""
        path = LOCALES_DIR / language / f"{module}.json"
        if not path.exists():
            # Fallback to en-US
            path = LOCALES_DIR / "en-US" / f"{module}.json"
            
        if not path.exists():
            return {}

        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def get_string(self, language: str, module: str, key: str, **kwargs: str | int) -> str:
        """Fetch a translated string and format it."""
        cache_key = f"{language}_{module}"
        if cache_key not in self.cache:
            self.cache[cache_key] = self._load_locale(language, module)
            
        text = self.cache[cache_key].get(key, key) # Fallback to the key itself if missing
        
        if kwargs:
            try:
                return text.format(**kwargs)
            except KeyError:
                return text
        return text

# Global singleton instance
locales = LocalizationService()
