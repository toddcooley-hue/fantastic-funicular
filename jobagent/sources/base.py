# job_agent/sources/base.py
from typing import List, Dict, Any
from abc import ABC, abstractmethod

class JobSource(ABC):
    @abstractmethod
    def fetch(self) -> List[Dict[str, Any]]:
        """Return list of normalized job dicts with keys:
        ['external_id','title','company','location','url','description','published_at','salary','raw']"""
        ...
