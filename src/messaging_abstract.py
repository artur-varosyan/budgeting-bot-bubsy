from abc import ABC, abstractmethod
from typing import Callable


class CommunicationMethod(ABC):

    @abstractmethod
    def listen(self, handler: Callable[[str], str]):
        pass

    @abstractmethod
    def send_message(self, message):
        pass