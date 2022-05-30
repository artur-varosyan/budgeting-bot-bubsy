import requests
import json

WORDS_ASSOCIATED_WITH_AMOUNT = ["total", "balance", "paid", "subtotal"]

def process(content: str) -> [str]:
    content = content.replace("\r\n", "\n")
    lines = content.split("\n")
    lines = list(map(lambda line: line.lower().split(" "), lines))
    print(len(lines))
    print(lines)
    print()

    half = round(len(lines) / 2)
    print(lines[half])

    # find the line with word total
    found = False
    line_number = 0
    for i, line in enumerate(lines):
        if any(map(lambda word: word in line, WORDS_ASSOCIATED_WITH_AMOUNT)):
            line_number = i
            found = True
            print(f"found! {line}")
            print(line_number) #174 1130
            break

    total_line = half + line_number
    print(lines[total_line])


def send_image():
    payload = {'isOverlayRequired': True,
               'apikey': "",
               'language': "eng",
               'OCREngine': 2
               }

    with open("downloaded.png", 'rb') as f:
        r = requests.post('https://api.ocr.space/parse/image',
                          files={"downloaded.png": f},
                          data=payload,
                          )

        result = r.content.decode()
        result = json.loads(result)
        print(result)
        print(type(result))
        text = result["ParsedResults"][0]["ParsedText"]
        process(text)


if __name__ == "__main__":
    send_image()
