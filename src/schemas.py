# src/schemas.py
from dataclasses import dataclass
from typing import Set, Optional

@dataclass
class GameState:
    used_chengyu: Set[str]
    last_chengyu: str

@dataclass
class ResponseFormat:
    chengyu_response: str
    validation_message: str
    defeat_message: Optional[str] = None
    # chat_with_user: Optional[str] = None


