"""Pydantic schemas for Reaction Roles."""

from pydantic import BaseModel, Field


class ReactionRoleItemSchema(BaseModel):
    id: int | None = None
    role_id: str
    emoji: str | None = None
    label: str | None = None


class ReactionRoleGroupSchema(BaseModel):
    id: int | None = None
    name: str = Field(..., max_length=100)
    min_roles: int = Field(0, ge=0)
    max_roles: int = Field(0, ge=0)
    required_roles: list[str] = Field(default_factory=list)
    blacklisted_roles: list[str] = Field(default_factory=list)
    items: list[ReactionRoleItemSchema] = Field(default_factory=list)
