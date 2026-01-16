# agents/base_agent.py

from abc import ABC, abstractmethod

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def run(self, context: dict) -> dict:
        """
        Executes agent logic and returns structured output.
        """
        pass
