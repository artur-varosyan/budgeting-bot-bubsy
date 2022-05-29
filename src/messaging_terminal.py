from messaging_abstract import CommunicationMethod
from typing import Callable


# A proxy for messaging with the user in the terminal
class TerminalMessaging(CommunicationMethod):

    def initialise(self):
        pass

    def listen(self, handler: Callable[[str], str]):
        while True:
            message = self.get_message()
            replies: [str] = handler(message)
            for reply in replies:
                self.send_message(reply)

    def get_message(self) -> str:
        message = input()
        return message

    def send_message(self, message):
        print(message)
