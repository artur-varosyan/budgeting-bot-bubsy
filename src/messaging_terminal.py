# A proxy for messaging with the user in the terminal

def listen(handler):
    while True:
        message = getMessage()
        replies: [str] = handler(message)
        for reply in replies:
            sendMessage(reply)


def getMessage():
    message = input()
    return message


def sendMessage(message):
    print(message)
