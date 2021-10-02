from datetime import date, timedelta

from messaging import sendMessage, getMessage

DIGITS = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'}
CATEGORIES = {"groceries", "shopping", "transport", "entertainment", "other"}
DAYS = {"today", "yesterday"}

# The object representing a single expense
class expense:
    def __init__(self, amount, category, date):
        self.amount = amount
        self.category = category
        self.date = date

def adminTerminal():
    # In future will run concurrently to chatbot()
    # and will have backdoor access to that process
    chatbot()

def chatbot():
    stop = False
    while not stop:
        message = getMessage()
        words = toWords(message)
        # Set of actions
        if "exit" in words:
            stop = True
        elif "show" in words and "budget" in words or "spending" in words:
            showBudget()  
        elif "spent" in words or "paid" in words:
            newExpense(words)

def showBudget():
    print("show budget")


def newExpense(words):
    amount = 0
    category = ""
    expenseDate = ""
    for word in words:
        if word[0] == "£" or word[0] in DIGITS:
            # identified amount of expense
            if word[0] == "£": amount = float(word[1:])
            else: amount = float(word)
        elif word in CATEGORIES:
            category = word
        elif word in DAYS:
            if word == "today":
                today = date.today()
                expenseDate = today.strftime('%m/%d/%y')
            elif word == "yesterday":
                yesterday = date.today() - timedelta(days=1)
                expenseDate = yesterday.strftime(f"%d/%m/%y")
    newExpense = expense(amount, category, expenseDate)
    reply = f"Noted! You spent £{newExpense.amount} on {newExpense.category} on {newExpense.date}"
    sendMessage(reply)
                

# Converts the string message to a list of lowercase words
def toWords(sentence):
    words = []
    word = ""
    insideAmount = False
    for character in sentence:
        if character in DIGITS: insideAmount = True
        if character == ' ' or character == ',':
            if word != "": words.append(word.lower())
            word = ""
            insideAmount = False
        elif character == '.' and insideAmount == False:
            if word != "": words.append(word.lower())
            word = ""
            insideAmount = False
        else:
            word = word + character
    if word != "": words.append(word.lower())
    return words


def main():
    adminTerminal()


if __name__ == "__main__":
    main()