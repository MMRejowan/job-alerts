"""
Base interface for job harvesters.
"""

from abc import ABC, abstractmethod
from typing import List
from core.models import JobPosting

class BaseHarvester(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the harvester source."""
        pass

    @abstractmethod
    def harvest(self) -> List[JobPosting]:
        """Fetches raw jobs and returns normalized JobPosting objects."""
        pass
