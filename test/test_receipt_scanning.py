from src.receipt_scanning import scan_receipt

# All tests should be run from the src/ directory


def test_amount_finding():
    test_photos = {
        "receipt0.png": 16.63,
        "receipt1.png": 5.97,
        "receipt2.png": 67.10,
        "receipt3.png": 38.40,
        "receipt4.png": 15.07,
        "receipt5.png": 7.00,
        "receipt6.png": 2.50
    }
    try:
        for photo_path, target_amount in test_photos.items():
            with open(f"../test/test_photos/{photo_path}", "rb") as file:
                photo = file.read()
                try:
                    amount = scan_receipt(bytearray(photo))
                    assert amount is not None
                    assert amount == target_amount
                except AssertionError:
                    raise AssertionError(f"PASSED RECEIPT PHOTO; EXPECTED {target_amount} RECEIVED {amount}")
    except IOError:
        raise IOError(f"FAILED TO READ IN TEST PHOTOS")
