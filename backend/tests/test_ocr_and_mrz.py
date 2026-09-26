import pytest
from backend.app.services.mrz_parser import mrz_parser, calculate_check_digit, verify_checksum

def test_icao_check_digit():
    # TD3 sample check digit
    # Passport number "L898902C3" with check digit 6
    digit = calculate_check_digit("L898902C3")
    assert digit == 6
    assert verify_checksum("L898902C3", "6") is True
    assert verify_checksum("L898902C3", "7") is False

def test_mrz_td3_parsing():
    line1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"
    line2 = "L898902C36UTO7408122F1204159ZE184226B<<<<<10"
    mrz = mrz_parser.parse([line1, line2])
    assert mrz is not None
    assert mrz.document_type == "PASSPORT"
    assert mrz.country_code == "UTO"
    assert mrz.surname == "ERIKSSON"
    assert mrz.given_names == "ANNA MARIA"
    assert mrz.passport_number == "L898902C3"
    assert mrz.nationality == "UTO"
    assert mrz.sex == "F"
    assert mrz.checksum_passport_number is True
    assert mrz.checksum_dob is True
    assert mrz.checksum_expiry is True

def test_mrz_extraction_from_noisy_text():
    text = """
    REPUBLIC OF UTOPIA
    PASSPORT
    Some header noise
    P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<
    L898902C36UTO7408122F1204159ZE184226B<<<<<10
    Random bottom footer
    """
    candidates = mrz_parser.extract_mrz_lines(text)
    assert len(candidates) >= 2
    res = mrz_parser.parse(candidates)
    assert res is not None
    assert res.surname == "ERIKSSON"
