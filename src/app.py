import messaging

# The object representing a single expense
class expense:
    def __init__(self, amount, category, date):
        self.amount = amount
        self.category = category
        self.date = date

def adminTerminal():
    # In future will run concurrently to chatbot()
    # and will have backdoor access to that process
    chatbot()

def chatbot():
    message = messaging.getMessage()
    words = toWords(message)
    print(words)
    messaging.sendMessage(f"Received: {message}")

def toWords(sentence):
    words = []
    word = ""
    for character in sentence:
        if character == '.' or character == ',' or character == ' ':
            if word != "": words.append(word)
            word = ""
        else:
            word = word + character
    if word != "": words.append(word)
    return words


def main():
    adminTerminal()


if __name__ == "__main__":
    main()