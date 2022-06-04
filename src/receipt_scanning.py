from typing import Optional
import requests
import json
import base64

# This implementation uses a free Optical Character Recognition (OCR) API
# You may sign up and request the API Key here https://ocr.space/OCRAPI

SUCCESS_CODE = 200
DIGITS = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'}
WORDS_ASSOCIATED_WITH_AMOUNT = ["total", "balance", "paid", "subtotal"]
MAX_VERTICAL_LINE_OFFSET = 0.5  # percentage

initialised = False
api_key = None


def is_amount(text: str) -> bool:
    contains_numbers = any(map(lambda digit: digit in text, DIGITS))
    contains_decimal_point = '.' in text
    if contains_numbers and contains_decimal_point:
        return True
    else:
        return False


def numeric_only(char: str) -> bool:
    if char.isnumeric() or char == ".":
        return True
    else:
        return False


def parse_amount(text: str) -> str:
    filtered_text = filter(numeric_only, text)
    filtered_text = "".join(filtered_text)
    return filtered_text


# Given the location of the keyword, find the numeric amount
def find_numeric_amount(overlay: [dict], line_no: int, word_no: int, y_coordinate: float) -> Optional[float]:
    # Start from the same line
    # TODO: The order of amount and keyword lines could be different
    for line in overlay[line_no:]:
        words = line["Words"]

        # If on same line as keyword, start with next word
        if overlay[line_no] == line:
            words = words[word_no + 1:]

        for word in words:
            word_text = word["WordText"].lower()
            vertical_diff = abs(word["Top"] - y_coordinate)
            max_diff = float(word["Height"]) * MAX_VERTICAL_LINE_OFFSET
            if vertical_diff < max_diff and is_amount(word_text):
                amount = parse_amount(word_text)
                amount = float(amount)
                return amount

    return None


# Find total amount paid by finding a keyword and considering location in image
# Use the fact that the total keyword and the amount paid on a receipt should be on the same line
# TODO: Use Hamming Distance calculation to identify unclear printed text
def find_keyword(overlay: [dict]) -> Optional[float]:
    for line_no, line in enumerate(overlay):
        words = line["Words"]

        for word_no, word in enumerate(words):
            word_text = word["WordText"].lower()
            if any(map(lambda keyword: keyword in word_text, WORDS_ASSOCIATED_WITH_AMOUNT)):
                keyword_y_coordinate = word["Top"]
                amount = find_numeric_amount(overlay, line_no, word_no, keyword_y_coordinate)
                if amount is not None:
                    return amount

    return None


def initialise():
    try:
        with open("ocr_config.json") as src_file:
            config = json.load(src_file)
        global api_key
        api_key = config["apiKey"]
    except Exception:
        raise RuntimeError("The configuration file 'ocr_config.json' is missing or contains errors")


# Given a photo of a receipt, use OCR to find the total amount spent
def scan_receipt(photo: bytearray) -> Optional[float]:
    if not initialised:
        initialise()

    base64_encoded_data = base64.b64encode(photo)
    base64_string = "data:image/jpg;base64," + str(base64_encoded_data.decode('utf-8'))

    payload = {'isOverlayRequired': True,
               'apikey': api_key,
               'language': "eng",
               'OCREngine': 2,
               'base64Image': base64_string,
               }

    r = requests.post('https://api.ocr.space/parse/image', data=payload, )

    result = r.content.decode()
    result = json.loads(result)

    if r.status_code == SUCCESS_CODE and not result["IsErroredOnProcessing"]:
        overlay = result["ParsedResults"][0]["TextOverlay"]["Lines"]
        amount = find_keyword(overlay)
        return amount
    else:
        return None
