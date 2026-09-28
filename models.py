import json
import os
from dataclasses import dataclass, asdict
from typing import List, Optional

@dataclass
class RoutineItem:
    id: int
    name: str
    target: str
    type: str  # "TARGET" or "LIMIT"
    goal_seconds: int
    elapsed_seconds: int = 0

    @property
    def is_goal_reached(self) -> bool:
        if self.type == "TARGET":
            return self.elapsed_seconds >= self.goal_seconds
        else:  # LIMIT
            return self.elapsed_seconds > self.goal_seconds

    @property
    def progress_ratio(self) -> float:
        if self.goal_seconds <= 0:
            return 0.0
        return min(1.0, self.elapsed_seconds / self.goal_seconds)


class ConfigManager:
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path

    def load_routines(self) -> List[RoutineItem]:
        if not os.path.exists(self.config_path):
            return []
        
        with open(self.config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        items = []
        for raw in data:
            items.append(RoutineItem(
                id=raw.get("id", 0),
                name=raw.get("name", ""),
                target=raw.get("target", ""),
                type=raw.get("type", "TARGET"),
                goal_seconds=raw.get("goal_seconds", 3600),
                elapsed_seconds=raw.get("elapsed_seconds", 0)
            ))
        return items

    def save_routines(self, items: List[RoutineItem]):
        data = []
        for item in items:
            raw = {
                "id": item.id,
                "name": item.name,
                "target": item.target,
                "type": item.type,
                "goal_seconds": item.goal_seconds,
                "elapsed_seconds": item.elapsed_seconds
            }
            data.append(raw)
        
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
