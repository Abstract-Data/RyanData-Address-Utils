from ryandata_address_utils import RyanDataAddressError, parse


def test_validation_exception() -> None:
    # Trigger a validation error with an invalid ZIP code
    try:
        parse("123 Main St, Austin TX 99999", validate=True)
        print("No exception raised (unexpected for invalid ZIP)")
    except Exception as e:
        print(f"Caught exception type: {type(e).__name__}")
        print(f"Exception message: {e}")
        if isinstance(e, RyanDataAddressError):
            print("SUCCESS: It IS a RyanDataAddressError")
        else:
            print(f"FAILURE: It IS NOT a RyanDataAddressError, it is {type(e)}")
            exit(1)


if __name__ == "__main__":
    test_validation_exception()
