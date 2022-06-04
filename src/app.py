import sys
import threading
import logging
import pause
from datetime import date, timedelta, datetime

from messaging_abstract import CommunicationMethod
from messaging_terminal import TerminalMessaging
from messaging_telegram import TelegramMessaging
import data as data
import ocr

DIGITS = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'}
DAYS = {"today", "yesterday"}
PUNCTUATION = {'.', ',', '!', '?', ':', ';'}
POSITIVE_RESPONSE = {"yes", "yeah", "correct", "yep", "okay"}
CANCEL_ACTION = {"cancel", "stop", "abort"}
TIME_OF_BUDGET_SUMMARY = 9  # Hours after midnight

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

    def __init__(self, communication_method: CommunicationMethod):
        # Threading objects
        self.awaiting_reply: bool = False
        self.reply_received: bool = False
        self.contacted: bool = False
        self.lock = threading.Lock()
        self.cond_var_handler = threading.Condition(self.lock)
        self.cond_var_action = threading.Condition(self.lock)
        self.incoming_message: [str] = ""
        self.reply: [str] = ""
        self.last_action = ""
        # Chosen communication method
        self.communication_method = communication_method

    def start(self):
        # Initialise communication (if needed)
        self.communication_method.initialise()
        # Start listening for communication
        self.communication_method.listen(self.handle_message, self.handle_photo)

    # Send notifications at timed intervals
    def track_time(self):
        # Get current date
        weekday = date.today().weekday()
        start_of_next_week = date.today() + (timedelta(days=7) - timedelta(days=weekday))
        start_of_next_week = datetime.combine(start_of_next_week, datetime.min.time())
        summary_time = start_of_next_week + timedelta(hours=TIME_OF_BUDGET_SUMMARY) + timedelta(minutes=0)

        while True:
            # Wait until next budget summary time
            print("Waiting until " + str(summary_time) + " for next weekly budget summary")
            pause.until(summary_time)
            self.budget_summary()
            summary_time += timedelta(days=7)

    def handle_photo(self, photo: bytearray) -> list[str]:
        amount = ocr.scan_receipt(photo)
        if amount is None:
            amount = "Could not find the total amount"
        else:
            amount = "Total spent: £" + amount
        return ["Received and processed image", amount]

    def handle_message(self, message: str) -> str:
        # If first time contacted, start tracking time
        # The bot can only send messages after at least one has been received
        if not self.contacted:
            thread = threading.Thread(target=self.track_time, daemon=True)
            thread.start()

        self.contacted = True
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
                start_command a new thread
            wait on the thread to be finished
            set reply to self.reply
            """
            self.lock.acquire()
            self.incoming_message = words
            if self.awaiting_reply:
                print(f"< Continuing {self.last_action}")
                self.reply_received = True
                self.cond_var_action.notify_all()
            else:
                print(f"< Performing {action}")
                action_thread = threading.Thread(target=actions[action], daemon=True)
                action_thread.start()
            self.cond_var_handler.wait()
            self.reply_received = False
            reply = self.reply
            self.lock.release()
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

    def budget_summary(self):
        print(f"< WEEKLY BUDGET SUMMARY")
        message = "Hi! Here is you weekly budget summary ☀️\n"
        self.communication_method.send_message(message)

        now = date.today()
        weekday = now.weekday()
        start = now - timedelta(days=weekday) - timedelta(weeks=1)
        end = start + timedelta(days=6)

        db = data.connect()
        categories = db.get_categories()
        budget = db.get_budget()
        budget = Helper.to_dict(budget)
        spending = db.get_spending(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        spending = Helper.to_dict(spending)

        start -= timedelta(weeks=1)
        end -= timedelta(weeks=1)
        last_week_spending = db.get_spending(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        last_week_spending = Helper.to_dict(last_week_spending)

        total_spending = sum(spending.values())
        total_spending_last_week = sum(last_week_spending.values())

        message = f"Overall you have spent £{'{:.2f}'.format(total_spending)} last week. "

        difference = ((total_spending - total_spending_last_week) / total_spending_last_week) * 100
        if difference > 0:
            message += f"This is {abs(round(difference))}% more 📈 than the week before 😅. "
        else:
            message += f"This is {abs(round(difference))}% less 📉 than the week before 😁. "

        message += self.budget_analysis(categories, budget, spending)
        self.communication_method.send_message(message)

    def show_budget(self):
        reply = []
        content = f"Sure! \nHere is what you spent this week:"
        now = date.today()
        weekday = now.weekday()
        start = now - timedelta(days=weekday)
        end = start + timedelta(days=6)
        db = data.connect()
        categories = db.get_categories()
        budget = db.get_budget()
        spending = db.get_spending(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        db.close()
        budget = Helper.to_dict(budget)
        spending = Helper.to_dict(spending)
        total_spending = 0
        total_limit = 0
        for category in categories:
            category = category[0].decode()
            cat_spending = '{:.2f}'.format(spending.get(category, 0))
            total_spending += spending.get(category, 0)
            cat_limit = '{:.2f}'.format(budget.get(category))
            total_limit += budget.get(category)
            content += f"\n - {category}: £{cat_spending} / £{cat_limit}"
        content += f"\nOverall you spent £{'{:.2f}'.format(total_spending)} " \
                   f"out of £{'{:.2f}'.format(total_limit)} this week."
        reply.append(content)
        analysis = self.budget_analysis(categories, budget, spending)
        if analysis != "":
            reply.append(analysis)
        self.lock.acquire()
        self.reply = reply
        self.cond_var_handler.notify_all()
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
        self.cond_var_handler.notify_all()
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
            analysis += f"You overspent on {text} by {amounts}."
            analysis += "\nConsider spending less next week! 😉"
        return analysis

    def new_expense(self):
        words = self.incoming_message
        db = data.connect()

        # Convert list of tuples of byte arrays to a set of strings
        categories = set(map(lambda c: c[0].decode(), db.get_categories()))
        category = None
        for word in words:
            if word in categories:
                category = word
                break
        amount = Helper.get_amount(words)
        expenseDate, _ = Helper.get_dates(words)
        # If no date provided, assume expense occurred today
        if expenseDate is None:
            expenseDate = date.today()
        expenseDate = expenseDate.strftime("%Y-%m-%d")

        # If no category provided, ask for clarification
        reply = []
        while category is None:
            reply.append("What is the category of the expense?")
            self.lock.acquire()
            self.reply = reply
            self.wait_for_response()
            words = self.incoming_message
            cancel = False
            for word in words:
                if word in CANCEL_ACTION:
                    cancel = True
            if cancel:
                self.reply = ["Sure I cancelled the operation for you."]
                self.cond_var_handler.notify_all()
                self.lock.release()
                return
            for word in words:
                if word in categories:
                    category = word
                    break
            reply = ["I did not quite catch that. Let's try again."]
            self.lock.release()

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
        analysis = self.expense_analysis(spending, budget, new_expense)
        if analysis != "":
            reply.append(analysis)
        self.lock.acquire()
        self.reply = reply
        self.cond_var_handler.notify_all()
        self.lock.release()
        return

    def new_budget(self):
        db = data.connect()
        budget = Helper.to_dict(db.get_budget())
        categories = set(map(lambda c: c[0].decode(), db.get_categories()))

        # Show existing budget
        reply = ["Sure I can help you to update your budget\n"]
        content = "Here is what your existing budget looks like:"
        for category in categories:
            cat_limit = '{:.2f}'.format(budget.get(category))
            content += f"\n- {category}: £{cat_limit}"
        reply.append(content)

        self.lock.acquire()
        satisfied = False
        while not satisfied:
            # Get the categories to be changed
            reply.append("Which categories would you like to change?")

            self.reply = reply
            self.wait_for_response()
            words = self.incoming_message

            # Initialise the dictionary of changed categories
            updated_categories = dict()
            for word in words:
                logging.info(word)
                if word in categories:
                    updated_categories[word] = 0

            # Allow the user to cancel this operation
            if len(updated_categories) == 0:
                content = "I have cancelled the budget change for you!"
                self.reply = [content]
                self.cond_var_handler.notify_all()
                self.lock.release()
                return

            logging.info(updated_categories.keys())
            content = "Great! Let's take this one step at a time."

            # Ask the user for new budget for each category mentioned
            content = self.set_category_budget(content, updated_categories)
            reply = [content]

            # Summarise the new budget
            content = self.summarise_budget_change(categories, updated_categories, budget)
            reply.append(content)
            reply.append("Does that look right?")

            self.reply = reply
            self.wait_for_response()
            words = self.incoming_message

            # If positive response, continue
            satisfied = any(map(lambda x: x in POSITIVE_RESPONSE, words))
            if not satisfied: reply = ["Okay, let's do this again."]

        # Add spending limit for categories that have not been changed
        for category in categories:
            if category not in updated_categories:
                updated_categories[category] = budget[category]

        weekday = date.today().weekday()
        start_of_next_week = (date.today() + (timedelta(days=7) - timedelta(days=weekday)))
        db.add_new_budget(updated_categories, start_of_next_week)
        self.reply = ["Great! Your budget has been changed"]
        self.cond_var_handler.notify_all()
        self.lock.release()
        return

    def set_category_budget(self, content, updated_categories):
        for category in updated_categories.keys():
            content += f" What would you like to change your budget for {category} to?"
            self.reply = [content]
            self.wait_for_response()
            words: [str] = self.incoming_message
            amount = Helper.get_amount(words)
            updated_categories[category] = amount
            content = '£{:.2f}'.format(amount) + f" on {category}, noted!"
        return content

    def summarise_budget_change(self, categories, updated_categories, budget):
        content = "Overall your new budget will look as follows:\n"
        for category in categories:
            if category in updated_categories.keys():
                old_limit = '{:.2f}'.format(budget.get(category))
                cat_limit = '{:.2f}'.format(updated_categories[category])
                content += f"\n* {category}: from £{old_limit} to £{cat_limit}"
            else:
                cat_limit = '{:.2f}'.format(budget.get(category))
                content += f"\n- {category}: £{cat_limit}"
        return content

    def expense_analysis(self, spending: dict, budget: dict, expense: Expense) -> str:
        analysis = ""
        category = expense.category
        limit = budget.get(category, 0)
        spent = spending.get(category, 0)
        if limit == 0:
            proportion = OVER_THE_LIMIT + 0.1
        else:
            proportion = spent / limit
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
        self.cond_var_handler.notify_all()
        self.lock.release()

    # Synchronisation
    def wait_for_response(self):
        self.reply_received = False
        self.awaiting_reply = True
        self.cond_var_handler.notify_all()
        while not self.reply_received:
            logging.info("@ Action will wait")
            self.cond_var_action.wait()
            logging.info("TIME")
        logging.info("@ Action stopped waiting")
        self.awaiting_reply = False


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
            elif word == "week":  # Assume start of the week is Monday
                i = source.index("week")
                if i > 0 and source[i - 1] == "this":
                    weekday = date.today().weekday()
                    start = (date.today() - timedelta(days=weekday))
                    end = start + timedelta(days=6)
                elif i > 0 and (source[i - 1] == "last" or source[i - 1] == "previous"):
                    weekday = date.today().weekday()
                    start = (date.today() - timedelta(days=weekday) - timedelta(weeks=1))
                    end = start + timedelta(days=6)
                break
            elif word == "weekend":  # Assume start of the weekend is Saturday
                i = source.index("weekend")
                weekday = date.today().weekday()
                if weekday < 6:
                    start = (date.today() + timedelta(days=(5 - weekday)))
                else:
                    start = (date.today() - timedelta(days=1))
                    end = start + timedelta(days=1)
                if i > 0 and (source[i - 1] == "last" or source[i - 1] == "previous"):
                    start -= timedelta(weeks=1)
                    end -= timedelta(weeks=1)
                break
            elif '/' in word or '-' in word:
                start = Helper.custom_date(word)
                i = source.index(word)
                if i < len(source) - 2 and source[i + 1] == "to":
                    end = Helper.custom_date(source[i + 2])
                break
        return start, end

    @staticmethod
    def get_amount(words: [str]) -> float:
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
        return amount


def main():
    args = sys.argv
    chosen_communication: CommunicationMethod = None
    if len(args) == 2 and args[1] == "--terminal":
        chosen_communication = TerminalMessaging()
        bot = Bubsy(chosen_communication)
        bot.start()
    elif len(args) == 1 or (len(args) >= 2 and args[1] == "--telegram"):
        chosen_communication = TelegramMessaging()
        if len(args) > 2 and args[2] == "--identify-users":
            chosen_communication.identify_users()
        else:
            bot = Bubsy(chosen_communication)
            bot.start()
    else:
        print("Error: Unknown arguments passed. Correct usage:\n "
              "--terminal  for terminal communication\n "
              "--telegram  for telegram bot communication (default)\n"
              "    --identify-users  to echo telegram user IDs (for configuration only)")
        return


if __name__ == "__main__":
    main()
