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


def test_ocr_service_nonexistent_file():
    from backend.app.services.ocr_service import ocr_service
    res = ocr_service.process_document("non_existent_file.png")
    assert res["status"] == "UNAVAILABLE"
    assert res["ocr_status"] == "UNAVAILABLE"
    assert res["confidence"] == 0.0
    assert res["raw_text"] == ""


def test_ocr_service_field_extraction_and_date_normalization():
    from backend.app.services.ocr_service import ModularOCREngine
    engine = ModularOCREngine()

    # Test Indian PAN card text extraction
    pan_text = """
    INCOME TAX DEPARTMENT
    GOVT. OF INDIA
    Permanent Account Number Card
    ABCDE1234F
    Name: RAHUL KUMAR
    Father's Name: SURESH KUMAR
    Date of Birth: 15/08/1990
    Date of Issue: 10/11/2015
    """
    fields = engine._extract_fields(pan_text, None, {}, {})
    assert fields.document_number == "ABCDE1234F"
    assert "RAHUL KUMAR" in fields.name
    assert fields.date_of_birth == "1990-08-15"
    assert fields.date_of_issue == "2015-11-10"
    assert fields.nationality == "IND"

    # Test Indian Aadhaar format extraction
    aadhaar_text = """
    Government of India
    Unique Identification Authority of India
    Name: ANANYA IYER
    DOB: 24-03-1995
    Gender: FEMALE
    4567 8901 2345
    """
    fields_aadhaar = engine._extract_fields(aadhaar_text, None, {}, {})
    assert fields_aadhaar.document_number == "4567 8901 2345"
    assert fields_aadhaar.gender == "F"
    assert fields_aadhaar.date_of_birth == "1995-03-24"
    assert fields_aadhaar.nationality == "IND"


def test_ocr_confidence_calculation():
    from backend.app.services.ocr_service import ModularOCREngine
    from backend.app.models.schemas import ExtractedFields
    engine = ModularOCREngine()

    # Empty raw text yields minimal fallback confidence
    empty_fields = ExtractedFields()
    conf_empty = engine._compute_confidence(empty_fields, None, "", "Local")
    assert conf_empty == 0.35

    # Populated fields yield high confidence
    full_fields = ExtractedFields(
        name="JANE DOE",
        document_number="P1234567",
        nationality="USA",
        date_of_birth="1990-01-01",
        date_of_issue="2020-01-01",
        date_of_expiry="2030-01-01",
        gender="F",
        issuing_country="USA"
    )
    conf_full = engine._compute_confidence(full_fields, None, "Full sample text", "Google Gemini Multimodal Vision OCR")
    assert conf_full >= 0.85


def test_mrz_td1_parsing():
    # TD1 standard 3-line format (National ID card)
    line1 = "I<UTOD231458907<<<<<<<<<<<<<<<"
    line2 = "7408122F1204159UTO<<<<<<<<<<<6"
    line3 = "ERIKSSON<<ANNA<MARIA<<<<<<<<<<"
    mrz = mrz_parser.parse([line1, line2, line3])
    assert mrz is not None
    assert mrz.document_type == "NATIONAL_ID"
    assert mrz.country_code == "UTO"
    assert mrz.surname == "ERIKSSON"
    assert mrz.given_names == "ANNA MARIA"
    assert mrz.passport_number == "D23145890"
    assert mrz.nationality == "UTO"
    assert mrz.sex == "F"


def test_mrz_best_effort_extraction_on_invalid_checksum():
    from backend.app.services.ocr_service import ModularOCREngine
    from backend.app.models.schemas import MRZData
    engine = ModularOCREngine()

    # MRZData with valid=False due to minor OCR misread on check digit
    flawed_mrz = MRZData(
        valid=False,
        raw_mrz=["P<DEMSHARMA<<ARJUN<<<<<<<<<<<<<<<<<<<<<<<<<<<", "K819273619DEM9205141M2806099<<<<<<<<<<<<<<04"],
        document_type="PASSPORT",
        country_code="DEM",
        surname="SHARMA",
        given_names="ARJUN",
        passport_number="K81927361",
        nationality="DEM",
        date_of_birth="1992-05-14",
        sex="M",
        expiry_date="2028-06-09"
    )

    fields = engine._extract_fields("", flawed_mrz, {}, {})
    # Should still extract name and doc number via best-effort extraction
    assert fields.name == "SHARMA ARJUN"
    assert fields.document_number == "K81927361"
    assert fields.nationality == "DEM"
    assert fields.date_of_birth == "1992-05-14"


def test_date_normalization_variations():
    from backend.app.services.ocr_service import normalize_date_string
    assert normalize_date_string("15/08/1990") == "1990-08-15"
    assert normalize_date_string("15-08-1990") == "1990-08-15"
    assert normalize_date_string("14 MAY 1992") == "1992-05-14"
    assert normalize_date_string("14 MAY, 1992") == "1992-05-14"
    assert normalize_date_string("10-JUN-2018") == "2018-06-10"
    assert normalize_date_string("2024.12.31") == "2024-12-31"


def test_driving_licence_and_voter_id_extraction():
    from backend.app.services.ocr_service import ModularOCREngine
    engine = ModularOCREngine()

    dl_text = """
    UNION OF INDIA DRIVING LICENCE
    DL No: DL-1420110012345
    Name: VIKAS VERMA
    DOB: 05/11/1988
    Valid Till: 04/11/2038
    """
    fields_dl = engine._extract_fields(dl_text, None, {}, {})
    assert "DL-1420110012345" in fields_dl.document_number
    assert "VIKAS VERMA" in fields_dl.name

    epic_text = """
    ELECTION COMMISSION OF INDIA
    ELECTOR PHOTO IDENTITY CARD
    EPIC No: WBF1234567
    Name: SUNITA PATEL
    """
    fields_epic = engine._extract_fields(epic_text, None, {}, {})
    assert fields_epic.document_number == "WBF1234567"
    assert "SUNITA PATEL" in fields_epic.name


def test_ocr_cache_lifecycle():
    from backend.app.services.ocr_service import _cache_put, _OCR_CACHE, clear_ocr_cache, get_ocr_cache_size
    clear_ocr_cache()
    assert get_ocr_cache_size() == 0

    dummy_result = {"status": "OK", "raw_text": "sample text", "confidence": 0.95}
    _cache_put("hash_abc123", dummy_result)
    assert get_ocr_cache_size() == 1
    assert "hash_abc123" in _OCR_CACHE

    clear_ocr_cache()
    assert get_ocr_cache_size() == 0


def test_bounding_box_generation():
    from backend.app.services.ocr_service import ModularOCREngine
    from backend.app.models.schemas import ExtractedFields
    engine = ModularOCREngine()

    fields = ExtractedFields(
        name="ALEX SMITH",
        document_number="P98765432",
        nationality="GBR",
        date_of_birth="1985-04-12",
        date_of_issue="2015-05-01",
        date_of_expiry="2025-05-01"
    )
    boxes = engine._generate_bounding_boxes(fields, w=800, h=500)
    assert len(boxes) >= 6
    labels = [b.text for b in boxes]
    assert any("Name" in l for l in labels)
    assert any("Doc No" in l for l in labels)
    assert any("MRZ" in l for l in labels)


