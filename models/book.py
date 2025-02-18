from dataclasses import dataclass, asdict
from typing import Dict, Any
import json

@dataclass
class Book:
    id: str
    timestamp: str
    book: Dict[str, Any]

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> 'Book':
        return cls(
            id=data['id'],
            timestamp=data['timestamp'],
            book=data['book']
        )

    def to_json(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_cache(self) -> str:
        return json.dumps(self.to_json())
    
    @classmethod
    def from_cache(cls, data: str) -> 'Book':
        return cls.from_json(json.loads(data))