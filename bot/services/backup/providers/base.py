"""Abstract Base Class for Backup Storage Providers."""

from abc import ABC, abstractmethod


class BackupStorageProvider(ABC):
    """Interface for saving and loading backup payloads."""

    @abstractmethod
    async def save_backup(self, backup_id: int, payload: dict) -> str:
        """Save the payload and return an identifier/URI."""

    @abstractmethod
    async def load_backup(self, identifier: str) -> dict:
        """Load a backup payload from its identifier/URI."""
