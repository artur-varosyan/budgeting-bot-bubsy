import sys
import threading
import logging
from functools import partial
from datetime import date, timedelta, datetime

from messaging_terminal import listen as listen_terminal
from messaging_telegram import listen as listen_telegram

import data as data

DIGITS = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'}
DAYS = {"today", "yesterday"}
PUNCTUATION = {'.', ',', '!', '?', ':', ';'}

# SPENDING CONSTANTS
OVER_THE_LIMIT = 1.0
CLOSE_TO_LIMIT = 0.9


# The object representing a single expense
class Expense:
    def __init__(self, amount: float, category: str, date: str, description: str, recurring: bool):
        self.amount = amount
        self.category = category
        self.date = date
        self.description = description
        self.recurring = recurring


class Bubsy:

    def __init__(self, communication_method):
        # Threading objects
        self.awaiting_reply: bool = False
        self.reply_received: bool = False
        self.lock = threading.Lock()
        self.cond_var_handler = threading.Condition(self.lock)
        self.cond_var_action = threading.Condition(self.lock)
        self.incoming_message: str = ""
        self.reply: [str] = ""
        self.last_action = ""
        # Chosen communication method
        self.communication_method = communication_method

    def adminTerminal(self):
        # In future will run concurrently to chatbot()
        # and will have backdoor access to that process
        self.chatbot()

    def chatbot(self):
        self.communication_method(self.handle_message)

    def handle_message(self, message: str) -> str:
        actions = {"SHOW_BUDGET": self.show_budget,
                   "SHOW_SPENDING": self.show_spending,
                   "ADD_EXPENSE": self.new_expense,
                   "NEW_BUDGET": self.new_budget,
                   "EXIT": None,
                   "UNKNOWN": self.unknown_query}
        print(f"> New Message Received: '{message}'")
        words = Helper.to_words(message)
        action = self.get_action(words)
        if action == "EXIT":
            # TODO: Only works when in terminal mode
            print("Exiting. Program stopped by user")
            sys.exit(0)
        else:
            """
            if (thread is waiting for reply):
                set self.incoming to the new message
                increase the semaphore
            else:
                start a new thread
            wait on the thread to be finished
            set reply to self.reply
            """
            self.lock.acquire()
            logging.info("Handler acquired lock")
            self.incoming_message = words
            if self.awaiting_reply:
                print(f"< Continuing {self.last_action}")
                logging.info("Handler identified waiting thread")
                self.reply_received = True
                self.cond_var_action.notifyAll()
                logging.info("Handler notified waiting thread")
            else:
                print(f"< Performing {action}")
                logging.info("Handler started a new thread")
                action_thread = threading.Thread(target=actions[action], daemon=True)
                action_thread.start()
            logging.info("Handler waiting")
            self.cond_var_handler.wait()
            logging.info("Handler returns")
            self.reply_received = False
            reply = self.reply
            self.lock.release()
            logging.info("Handler releases lock")
            #reply = actions[action](words)
        self.last_action = action
        return reply

    @staticmethod
    def get_action(words: [str]) -> str:
        # Set of actions
        if "exit" in words:
            return "EXIT"
        elif "show" in words and "budget" in words or "spending" in words:
            return "SHOW_BUDGET"
        elif "how" in words and "much" in words and ("spent" in words or "spend" in words):
            return "SHOW_SPENDING"
        elif "spent" in words or "paid" in words:
            return "ADD_EXPENSE"
        elif ("update" in words or "change" in words or "new" in words) and "budget" in words:
            return "NEW_BUDGET"
        else:
            return "UNKNOWN"

    def show_budget(self):
        reply = []
        content = f"Sure! \nHere is what you spent this week:"
        now = date.today()
        start = now - timedelta(days=int(now.strftime("%w")))
        end = start + timedelta(days=6)
        db = data.connect()
        categories = db.get_categories()
        budget = db.get_budget()
        spending = db.get_spending(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        db.close()
        budget = Helper.to_dict(budget)
        spending = Helper.to_dict(spending)
        for category in categories:
            category = category[0].decode()
            cat_spending = '{:.2f}'.format(spending.get(category, 0))
            cat_limit = '{:.2f}'.format(budget.get(category))
            content += f"\n - {category}: £{cat_spending} / £{cat_limit}"
        reply.append(content)
        reply.append(self.budget_analysis(categories, budget, spending))
        self.lock.acquire()
        self.reply = reply
        self.cond_var_handler.notifyAll()
        self.lock.release()
        return

    def show_spending(self):
        words = self.incoming_message
        start, end = Helper.get_dates(words)
        db = data.connect()
        spending = db.get_spending(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        categories = db.get_categories()
        db.close()
        spending = Helper.to_dict(spending)
        total = sum(spending.values())
        content = f"In total you spent £{'{:.2f}'.format(total)}. Here is a breakdown:"
        for category in categories:
            category = category[0].decode()
            cat_spending = '{:.2f}'.format(spending.get(category, 0))
            content += f"\n - {category}: £{cat_spending}"
        self.lock.acquire()
        self.reply = [content]
        self.cond_var_handler.notifyAll()
        self.lock.release()
        return

    def budget_analysis(self, categories: dict, budget: dict, spending: dict) -> str:
        analysis = ""
        overspent = []
        for category in categories:
            category = category[0].decode()
            cat_budget = budget.get(category, 0)
            cat_spent = spending.get(category, 0)
            diff = cat_spent - cat_budget
            if diff > 0:
                overspent.append((category, diff))
        if len(overspent) > 0:
            text = ""
            amounts = ""
            for category in overspent:
                if text != "":
                    text += ", "
                    amounts += ", "
                text += category[0]
                amounts += '£{:.2f}'.format(category[1])
            analysis += f"You overspent on {text} by {amounts}"
            analysis += "\nConsider spending less next week"
        return analysis

    def new_expense(self):
        words = self.incoming_message
        amount = 0
        db = data.connect()
        # convert list of tuples of byte arrays to a set of strings
        categories = set(map(lambda c: c[0].decode(), db.get_categories()))
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
            elif word in categories:
                category = word
        expenseDate, _ = Helper.get_dates(words)
        expenseDate = expenseDate.strftime("%Y-%m-%d")
        new_expense = Expense(amount, category, expenseDate, "", False)
        db.add_expense(new_expense)
        now = date.today()
        start = now - timedelta(days=int(now.strftime("%w")))
        end = start + timedelta(days=6)
        spending = Helper.to_dict(db.get_spending(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")))
        budget = Helper.to_dict(db.get_budget())
        self.expense_analysis(spending, budget, new_expense)
        db.close()
        reply = [f"Noted! You spent {'£{:.2f}'.format(new_expense.amount)} on {new_expense.category} on {new_expense.date}"]
        reply.append(self.expense_analysis(spending, budget, new_expense))
        self.lock.acquire()
        self.reply = reply
        self.cond_var_handler.notifyAll()
        self.lock.release()
        return

    def new_budget(self):
        reply = ["Sure I can help you to update your budget\n"]
        content = "Here is what your existing budget looks like:"
        db = data.connect()
        budget = Helper.to_dict(db.get_budget())
        categories = db.get_categories()
        for category in categories:
            category = category[0].decode()
            cat_limit = '{:.2f}'.format(budget.get(category))
            content += f"\n- {category}: £{cat_limit}"
        reply.append(content)
        reply.append("Which categories would you like to change?")
        self.lock.acquire()
        logging.info("@ Action acquires lock")
        self.reply = reply
        self.awaiting_reply = True
        self.cond_var_handler.notifyAll()
        logging.info("@ Action notifies handler")
        while not self.reply_received:
            logging.info("@ Action will wait")
            self.cond_var_action.wait()
        logging.info("@ Action stopped waiting")
        self.awaiting_reply = False
        reply = ["Intercepted a message!"]
        self.reply = reply
        self.cond_var_handler.notifyAll()
        self.lock.release()
        logging.info("@ Action released lock")
        # TODO:
        # 1. Update get_budget() to solely return the limits and not the spending
        # 2. Add synchronisation - when an action is identified, start a new thread
        #    - Sleep this thread while awaiting for a response using a conditional variable
        #    - Create an idle/busy variable
        #    - When a reply comes in, wake up the thread and continue
        #    - Add an option to escape the sequence
        #    - (potentially) Add support for multiple separate messages, e.g. by returning a list of strings
        return

    def expense_analysis(self, spending: dict, budget: dict, expense: Expense) -> str:
        analysis = ""
        category = expense.category
        limit = budget.get(category, 0)
        spent = spending.get(category, 0)
        proportion = spent / limit  # FIXME: Potential division by zero
        if proportion > OVER_THE_LIMIT:
            amount = '£{:.2f}'.format(spent - limit)
            analysis += f"You overspent on {category} by {amount}!"
        elif proportion > CLOSE_TO_LIMIT:
            remaining = '£{:.2f}'.format(limit - spent)
            analysis += f"\nYou have reached {round(proportion * 100)}% of your spending limit on {category}! " \
                        f"You have {remaining} left for this week! "
        return analysis

    def unknown_query(self):
        self.lock.acquire()
        self.reply = ["Sorry I don't quite understand"]
        self.cond_var_handler.notifyAll()
        self.lock.release()


class Helper:
    # Converts the string message to a list of lowercase words
    @staticmethod
    def to_words(sentence: str) -> [str]:
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

    @staticmethod
    def to_dict(source: list) -> dict:
        dest = {}
        for pair in source:
            dest[pair[0].decode()] = pair[1]
        return dest

    # Able to read a custom date in the dd/mm/yyyy and dd/mm formats
    @staticmethod
    def custom_date(source: str) -> datetime:
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

    @staticmethod
    def get_dates(source: str) -> (datetime, datetime):
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
                start = Helper.custom_date(word)
                i = source.index(word)
                if i < len(source) - 2 and source[i + 1] == "to":
                    end = Helper.custom_date(source[i + 2])
                break
        return start, end


def main():
    args = sys.argv
    listen = None
    if len(args) == 2 and args[1] == "--terminal":
        listen = listen_terminal
    elif len(args) == 1 or (len(args) == 2 and args[1] == "--telegram"):
        listen = listen_telegram
    else:
        print("Error: Unknown arguments passed. Correct usage:\n "
              "--terminal  for terminal communication\n "
              "--telegram  for telegram bot communication (default)")
        return
    bot = Bubsy(listen)
    bot.adminTerminal()


if __name__ == "__main__":
    main()
