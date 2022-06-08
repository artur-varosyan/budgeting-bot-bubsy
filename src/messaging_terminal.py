from messaging_abstract import CommunicationMethod
from typing import Callable, List


# A proxy for messaging with the user in the terminal
class TerminalMessaging(CommunicationMethod):

    def initialise(self):
        pass

    def listen(self, handler: Callable[[str], str], photo_handler: Callable[[bytearray], List[str]]):
        # Note: Photo messages are not supported in the terminal
        while True:
            message = self.get_message()
            replies = handler(message)
            for reply in replies:
                self.send_message(reply)

    def get_message(self) -> str:
        message = input()
        return message

    def send_message(self, message: str):
        print(message)
