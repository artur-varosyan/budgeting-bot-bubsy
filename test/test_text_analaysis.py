from datetime import datetime, date, timedelta
from src.app import Helper, Bubsy


def test_words():
    try:
        message = "This is a test."
        target = ["this", "is", "a", "test"]
        output = Helper.to_words(message)
        assert output == target
        message = "Show me my budget, please"
        target = ["show", "me", "my", "budget", "please"]
        output = Helper.to_words(message)
        assert output == target
        message = "Not again! I paid £100 for transport!!!"
        target = ["not", "again", "i", "paid", "£100", "for", "transport"]
        output = Helper.to_words(message)
        assert output == target
        message = "How much have I spent from 22/01/2020 to 24/02/2020?"
        target = ["how", "much", "have", "i", "spent", "from", "22/01/2020", "to", "24/02/2020"]
        output = Helper.to_words(message)
        assert output == target
        message = ""
        target = []
        output = Helper.to_words(message)
        assert output == target
    except AssertionError:
        raise AssertionError(f"PASSED: {message}; EXPECTED {target} RECEIVED {output}")


def test_action():
    try:
        words = ["how", "much", "did", "I", "spend", "today"]
        target = "SHOW_SPENDING"
        output = Bubsy.get_action(words)
        assert output == target
        words = ["how", "much", "have", "I", "spent", "yesterday"]
        target = "SHOW_SPENDING"
        output = Bubsy.get_action(words)
        assert output == target
        words = ["show", "me", "my", "budget"]
        target = "SHOW_BUDGET"
        output = Bubsy.get_action(words)
        assert output == target
        words = ["can", "i", "see", "my", "spending"]
        target = "SHOW_BUDGET"
        output = Bubsy.get_action(words)
        assert output == target
        words = ["i", "spent", "£99", "on", "groceries", "last", "weekend"]
        target = "ADD_EXPENSE"
        output = Bubsy.get_action(words)
        assert output == target
        words = ["i", "paid", "for", "housing", "today", "it", "was", "450", "pounds"]
        target = "ADD_EXPENSE"
        output = Bubsy.get_action(words)
        assert output == target
        words = ["i", "like", "this", "app"]
        target = "UNKNOWN"
        output = Bubsy.get_action(words)
        assert output == target
    except AssertionError:
        raise AssertionError(f"PASSED: {words}; EXPECTED {target} RECEIVED {output}")


def test_date():
    try:
        words = ["today"]
        target = date.today().strftime("%Y-%m-%d")
        output = Helper.get_dates(words)[0].strftime("%Y-%m-%d")
        assert output == target
        words = ["yesterday"]
        target = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        output = Helper.get_dates(words)[0].strftime("%Y-%m-%d")
        assert output == target
        words = ["12/12/2012"]
        target = datetime(2012, 12, 12).strftime("%Y-%m-%d")
        output = Helper.get_dates(words)[0].strftime("%Y-%m-%d")
        assert output == target
        words = ["from", "29/08/2019", "to", "01/10/2021"]
        target = datetime(2019, 8, 29).strftime("%Y-%m-%d")
        target2 = datetime(2021, 10, 1).strftime("%Y-%m-%d")
        output, output2 = Helper.get_dates(words)
        output = output.strftime("%Y-%m-%d")
        output2 = output2.strftime("%Y-%m-%d")
        assert output == target
        output = output2
        target = target2
        assert output == target
        words = ["31-05-2021"]
        target = datetime(2021, 5, 31).strftime("%Y-%m-%d")
        output = Helper.get_dates(words)[0].strftime("%Y-%m-%d")
        assert output == target
        words = []
        target = None
        output = Helper.get_dates(words)
        assert Helper.get_dates(words) == (target, target)
    except AssertionError:
        raise AssertionError(f"PASSED: {words}; EXPECTED {target} RECEIVED {output}")
