"""Feature flags schema."""

from pydantic import BaseModel


class FeatureFlags(BaseModel):
    """Toggleable feature flags for the dashboard and bot."""

    premium_enabled: bool = False
    ai_features_enabled: bool = False
    beta_features_enabled: bool = False
    experimental_enabled: bool = False
