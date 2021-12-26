# A proxy for messaging with the user in the terminal

def listen(handler):
    while True:
        message = getMessage()
        reply = handler(message)
        sendMessage(reply)


def getMessage():
    message = input()
    return message


def sendMessage(message):
    print(message)
