from datetime import date, timedelta
from messaging import sendMessage, getMessage
import data

DIGITS = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'}
CATEGORIES = {"groceries", "shopping", "transport", "entertainment",
              "toiletries", "subscriptions", "phone", "housing", "other"}
DAYS = {"today", "yesterday"}


# The object representing a single expense
class Expense:
    def __init__(self, amount, category, date, week, description):
        self.amount = amount
        self.category = category
        self.date = date
        self.week = week
        self.description = description


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
        else:
            sendMessage("Sorry I don't quite understand")


def showBudget():
    content = f"Sure! \nHere is what you spent this week:"
    now = date.today()
    start = now - timedelta(days=int(now.strftime("%w")))
    end = start + timedelta(days=6)
    db = data.connect()
    categories = db.get_categories()
    budget = db.get_budget()
    spending = db.get_spending(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
    db.close()
    budget = toDict(budget)
    spending = toDict(spending)
    for category in categories:
        category = category[0].decode()
        cat_spending = '{:.2f}'.format(spending.get(category, 0))
        cat_limit = '{:.2f}'.format(budget.get(category))
        content += f"\n - {category}: £{cat_spending} / £{cat_limit}"
    sendMessage(content)


def newExpense(words):
    amount = 0
    category = ""
    expenseDate = ""
    for word in words:
        if word[0] == "£" or word[0] in DIGITS:
            # identified amount of expense
            if word[0] == "£":
                amount = float(word[1:])
            else:
                amount = float(word)
        elif word in CATEGORIES:
            category = word
        elif word in DAYS:
            if word == "today":
                today = date.today()
                expenseDate = today.strftime("%Y-%m-%d")
            elif word == "yesterday":
                yesterday = date.today() - timedelta(days=1)
                expenseDate = yesterday.strftime("%Y-%m-%d")
    new_expense = Expense(amount, category, expenseDate, 12, "")
    db = data.connect()
    db.add_expense(new_expense)
    db.close()
    reply = f"Noted! You spent £{new_expense.amount} on {new_expense.category} on {new_expense.date}"
    sendMessage(reply)


# Converts the string message to a list of lowercase words
def toWords(sentence):
    words = []
    word = ""
    insideAmount = False
    for character in sentence:
        if character in DIGITS:
            insideAmount = True
        if character == ' ' or character == ',':
            if word != "":
                words.append(word.lower())
            word = ""
            insideAmount = False
        elif character == '.' and insideAmount is False:
            if word != "":
                words.append(word.lower())
            word = ""
            insideAmount = False
        else:
            word = word + character
    if word != "":
        words.append(word.lower())
    return words


def toDict(source):
    dest = {}
    for pair in source:
        dest[pair[0].decode()] = pair[1]
    return dest


def main():
    adminTerminal()


if __name__ == "__main__":
    main()
