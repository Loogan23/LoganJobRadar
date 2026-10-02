from abc import ABC, abstractmethod
from typing import List
from core.models import Job

class BaseScraper(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def search(self, query: str, location: str = "", is_remote: bool = False, limit: int = 15) -> List[Job]:
        pass
