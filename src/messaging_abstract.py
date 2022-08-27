from abc import ABC, abstractmethod
from typing import Callable, List, Union


class CommunicationMethod(ABC):

    @abstractmethod
    def initialise(self):
        pass

    @abstractmethod
    def listen(self, text_handler: Callable[[str], Union[List[str], List[str]]], photo_handler: Callable[[bytearray], List[str]]):
        pass

    @abstractmethod
    def send_message(self, message: str):
        pass