from abc import ABC, abstractmethod
from typing import Dict, Any, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from actions.folder_automator import FolderAutomator

class Action(ABC):
    """
    Abstract base class for all Automation Actions.
    """
    def __init__(self, automator: 'FolderAutomator', params: Dict[str, Any]):
        self.automator = automator
        self.params = params
        self.logger = logging.getLogger(f"Action-{self.__class__.__name__}")

    @abstractmethod
    def execute(self):
        """
        Execute the action logic.
        Access self.automator.folder, self.automator.reader, etc.
        """
        pass
