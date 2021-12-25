from datetime import datetime, date, timedelta
from src.app import get_dates


def test_date():
    try:
        words = ["today"]
        target = date.today().strftime("%Y-%m-%d")
        output = get_dates(words)[0].strftime("%Y-%m-%d")
        assert output == target
        words = ["yesterday"]
        target = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        output = get_dates(words)[0].strftime("%Y-%m-%d")
        assert output == target
        words = ["12/12/2012"]
        target = datetime(2012, 12, 12).strftime("%Y-%m-%d")
        output = get_dates(words)[0].strftime("%Y-%m-%d")
        assert output == target
        words = ["from", "29/08/2019", "to", "01/10/2021"]
        target = datetime(2019, 8, 29).strftime("%Y-%m-%d")
        target2 = datetime(2021, 10, 1).strftime("%Y-%m-%d")
        output, output2 = get_dates(words)
        output = output.strftime("%Y-%m-%d")
        output2 = output2.strftime("%Y-%m-%d")
        assert output == target
        output = output2
        target = target2
        assert output == target
        words = ["31-05-2021"]
        target = datetime(2021, 5, 31).strftime("%Y-%m-%d")
        output = get_dates(words)[0].strftime("%Y-%m-%d")
        assert output == target
        words = []
        target = None
        output = get_dates(words)
        assert get_dates(words) == (target, target)
    except AssertionError as e:
        raise AssertionError(f"PASSED: {words}; EXPECTED {target} RECEIVED {output}")
