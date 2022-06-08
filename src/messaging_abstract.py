from abc import ABC, abstractmethod
from typing import Callable, List


class CommunicationMethod(ABC):

    @abstractmethod
    def initialise(self):
        pass

    @abstractmethod
    def listen(self, text_handler: Callable[[str], list[str]], photo_handler: Callable[[bytearray], List[str]]):
        pass

    @abstractmethod
    def send_message(self, message: str):
        pass