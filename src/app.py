from datetime import date, timedelta, datetime
from messaging import sendMessage, getMessage
import data as data

DIGITS = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'}
CATEGORIES = {"groceries", "shopping", "transport", "entertainment",
              "toiletries", "subscriptions", "phone", "housing", "other"}
DAYS = {"today", "yesterday"}
PUNCTUATION = {'.', ',', '!', '?', ':', ';'}


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
        elif "how" in words and "much" in words and ("spent" in words or "spend" in words):
            showSpending(words)
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


def showSpending(words):
    start, end = get_dates(words)
    db = data.connect()
    spending = db.get_spending(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
    categories = db.get_categories()
    db.close()
    spending = toDict(spending)
    total = sum(spending.values())
    content = f"In total you spent £{'{:.2f}'.format(total)}. Here is a breakdown:"
    for category in categories:
        category = category[0].decode()
        cat_spending = '{:.2f}'.format(spending.get(category, 0))
        content += f"\n - {category}: £{cat_spending}"
    sendMessage(content)


def newExpense(words):
    amount = 0
    category = ""
    for word in words:
        if word[0] == "£" or word[0] in DIGITS:
            # identified amount of expense
            if word[0] == "£":
                try:
                    amount = float(word[1:])
                except ValueError:
                    continue
            else:
                try:
                    amount = float(word)
                except ValueError:
                    continue
        elif word in CATEGORIES:
            category = word
    expenseDate, _ = get_dates(words)
    expenseDate = expenseDate.strftime("%Y-%m-%d")
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
        if character == ' ' or character == ',' or character == '!' or character == '?':
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


# Able to read a custom date in the dd/mm/yyyy and dd/mm formats
def custom_date(source):
    found_date = None
    curr = ""
    year = None
    month = None
    day = None
    for i in range(len(source)):
        if source[i] in DIGITS:
            curr += source[i]
        if source[i] == '-' or source[i] == '/' or i == len(source) - 1:
            if len(curr) == 4:
                year = int(curr)
                curr = ""
            elif len(curr) == 2 and int(curr) <= 12 and day is not None:
                month = int(curr)
                curr = ""
            elif 1 <= int(curr) <= 31:
                day = int(curr)
                curr = ""
    if day is not None and month is not None:
        if year is None:
            year = int(datetime.now().strftime("%Y"))
        found_date = datetime(year=year, month=month, day=day)
    return found_date


def get_dates(source):
    start = None
    end = None
    for word in source:
        if word == "today":
            start = date.today()
            end = start
            break
        elif word == "yesterday":
            start = date.today() - timedelta(days=1)
            end = start
            break
        elif word == "week":  # Assume start of the week is Sunday
            i = source.index("week")
            if i > 0 and source[i - 1] == "this":
                weekday = int(date.today().strftime("%w"))
                start = (date.today() - timedelta(days=weekday))
                end = start + timedelta(days=6)
            elif i > 0 and (source[i - 1] == "last" or source[i - 1] == "previous"):
                weekday = int(date.today().strftime("%w"))
                start = (date.today() - timedelta(days=weekday) - timedelta(weeks=1))
                end = start + timedelta(days=6)
            break
        elif word == "weekend":  # Assume start of the weekend is Saturday
            i = source.index("weekend")
            weekday = int(date.today().strftime("%w"))
            if 0 < weekday:
                start = (date.today() + timedelta(days=(6 - weekday)))
            else:
                start = (date.today() - timedelta(days=1))
                end = start + timedelta(days=1)
            if i > 0 and (source[i - 1] == "last" or source[i - 1] == "previous"):
                start -= timedelta(weeks=1)
                end = start + timedelta(weeks=1)
            break
        elif '/' in word or '-' in word:
            start = custom_date(word)
            i = source.index(word)
            if i < len(source) - 2 and source[i + 1] == "to":
                end = custom_date(source[i + 2])
            break
    return start, end


def main():
    adminTerminal()


if __name__ == "__main__":
    main()
