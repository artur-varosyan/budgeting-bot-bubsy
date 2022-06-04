from typing import Optional

import requests
import json
import base64

DIGITS = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'}
WORDS_ASSOCIATED_WITH_AMOUNT = ["total", "balance", "paid", "subtotal"]
MAX_VERTICAL_LINE_OFFSET = 0.5  # percentage


def is_amount(text: str) -> bool:
    if any(map(lambda digit: digit in text, DIGITS)):
        return True


# Find total amount paid by finding a keyword and considering location in image
# Use the fact that the total keyword and the amount paid on a receipt should be on the same line
def find_amount(overlay: [dict]) -> str:
    found_keyword = False
    keyword_y_coordinate = 0

    line_no = 0
    word_no = 0
    for line_no, line in enumerate(overlay):
        words = line["Words"]

        for word_no, word in enumerate(words):
            word_text = word["WordText"].lower()
            if any(map(lambda keyword: keyword in word_text, WORDS_ASSOCIATED_WITH_AMOUNT)):
                print("FOUND KEYWORD")
                found_keyword = True
                keyword_y_coordinate = word["Top"]
                break
        else:
            continue
        break

    if found_keyword:
        found_amount = False
        amount = ""

        # start from the next line
        # TODO: The order of amount and keyword lines could be different
        for line in overlay[line_no:]:
            words = line["Words"]

            # If on same line as keyword, start with next word
            if overlay[line_no] == line:
                words = words[word_no + 1:]

            for word in words:
                word_text = word["WordText"].lower()
                vertical_diff = abs(word["Top"] - keyword_y_coordinate)
                max_diff = float(word["Height"]) * MAX_VERTICAL_LINE_OFFSET
                if vertical_diff < max_diff and is_amount(word_text):
                    found_amount = True
                    amount = word_text
                    print(amount)
                    return amount


def scan_receipt(photo: bytearray) -> Optional[str]:
    base64_encoded_data = base64.b64encode(photo)
    base64_string = "data:image/jpg;base64," + str(base64_encoded_data.decode('utf-8'))

    payload = {'isOverlayRequired': True,
               'apikey': "dccaf2816b88957",
               'language': "eng",
               'OCREngine': 2,
               'base64Image': base64_string,
               }

    r = requests.post('https://api.ocr.space/parse/image', data=payload, )

    print(r.status_code)
    print(r.reason)
    print(r.request)
    result = r.content.decode()
    print(result)
    result = json.loads(result)
    overlay = result["ParsedResults"][0]["TextOverlay"]["Lines"]
    amount = find_amount(overlay)
    return amount


def send_image():
    payload = {'isOverlayRequired': True,
               'apikey': "dccaf2816b88957",
               'language': "eng",
               'OCREngine': 2
               }

    with open("photos/downloaded.png", 'rb') as f:
        print("request sent")
        r = requests.post('https://api.ocr.space/parse/image',
                          files={"downloaded.png": f},
                          data=payload,
                          )

        print("response received")
        result = r.content.decode()
        result = json.loads(result)
        print(result)
        print(type(result))
        text = result["ParsedResults"][0]["ParsedText"]
        overlay = result["ParsedResults"][0]["TextOverlay"]["Lines"]
        find_amount(overlay)


if __name__ == "__main__":
    send_image()
