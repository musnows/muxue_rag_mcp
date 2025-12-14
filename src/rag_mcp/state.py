import os
import json
from typing import List

STATE_FILE = os.path.expanduser("~/.rag_mcp/state.json")

class StateManager:
    @staticmethod
    def load_state() -> List[str]:
        if not os.path.exists(STATE_FILE):
            return []
        try:
            with open(STATE_FILE, 'r') as f:
                data = json.load(f)
                return data.get("directories", [])
        except Exception:
            return []

    @staticmethod
    def add_directory(path: str):
        dirs = StateManager.load_state()
        abs_path = os.path.abspath(path)
        if abs_path not in dirs:
            dirs.append(abs_path)
            StateManager.save_state(dirs)

    @staticmethod
    def remove_directory(path: str):
        dirs = StateManager.load_state()
        abs_path = os.path.abspath(path)
        if abs_path in dirs:
            dirs.remove(abs_path)
            StateManager.save_state(dirs)

    @staticmethod
    def save_state(dirs: List[str]):
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        with open(STATE_FILE, 'w') as f:
            json.dump({"directories": dirs}, f)
