import re
from datetime import datetime, date
from typing import List, Optional, Tuple, Dict, Any
from backend.app.models.schemas import MRZData

ISO_COUNTRY_CODES: Dict[str, str] = {
    "AFG": "Afghanistan", "ALB": "Albania", "DZA": "Algeria", "AND": "Andorra", "AGO": "Angola",
    "ARG": "Argentina", "ARM": "Armenia", "AUS": "Australia", "AUT": "Austria", "AZE": "Azerbaijan",
    "BHR": "Bahrain", "BGD": "Bangladesh", "BLR": "Belarus", "BEL": "Belgium", "BLZ": "Belize",
    "BEN": "Benin", "BTN": "Bhutan", "BOL": "Bolivia", "BIH": "Bosnia and Herzegovina", "BWA": "Botswana",
    "BRA": "Brazil", "BRN": "Brunei", "BGR": "Bulgaria", "BFA": "Burkina Faso", "BDI": "Burundi",
    "KHM": "Cambodia", "CMR": "Cameroon", "CAN": "Canada", "CHL": "Chile", "CHN": "China",
    "COL": "Colombia", "CRI": "Costa Rica", "HRV": "Croatia", "CUB": "Cuba", "CYP": "Cyprus",
    "CZE": "Czech Republic", "DNK": "Denmark", "DJI": "Djibouti", "DOM": "Dominican Republic", "ECU": "Ecuador",
    "EGY": "Egypt", "SLV": "El Salvador", "EST": "Estonia", "ETH": "Ethiopia", "FIN": "Finland",
    "FRA": "France", "DEU": "Germany", "GHA": "Ghana", "GRC": "Greece", "GTM": "Guatemala",
    "HND": "Honduras", "HKG": "Hong Kong", "HUN": "Hungary", "ISL": "Iceland", "IND": "India",
    "IDN": "Indonesia", "IRN": "Iran", "IRQ": "Iraq", "IRL": "Ireland", "ISR": "Israel",
    "ITA": "Italy", "JAM": "Jamaica", "JPN": "Japan", "JOR": "Jordan", "KAZ": "Kazakhstan",
    "KEN": "Kenya", "KOR": "South Korea", "KWT": "Kuwait", "KGZ": "Kyrgyzstan", "LVA": "Latvia",
    "LBN": "Lebanon", "LBY": "Libya", "LIE": "Liechtenstein", "LTU": "Lithuania", "LUX": "Luxembourg",
    "MYS": "Malaysia", "MDV": "Maldives", "MEX": "Mexico", "MCO": "Monaco", "MNG": "Mongolia",
    "NPL": "Nepal", "NLD": "Netherlands", "NZL": "New Zealand", "NGA": "Nigeria", "NOR": "Norway",
    "OMN": "Oman", "PAK": "Pakistan", "PAN": "Panama", "PHL": "Philippines", "POL": "Poland",
    "PRT": "Portugal", "QAT": "Qatar", "ROU": "Romania", "RUS": "Russia", "SAU": "Saudi Arabia",
    "SGP": "Singapore", "ZAF": "South Africa", "ESP": "Spain", "LKA": "Sri Lanka", "SWE": "Sweden",
    "CHE": "Switzerland", "THA": "Thailand", "TUR": "Turkey", "UKR": "Ukraine", "ARE": "United Arab Emirates",
    "GBR": "United Kingdom", "USA": "United States", "UTO": "Utopia", "VNM": "Vietnam", "ZWE": "Zimbabwe"
}

def resolve_country_name(code: Optional[str]) -> str:
    if not code:
        return ""
    clean = code.strip().upper()
    return ISO_COUNTRY_CODES.get(clean, clean)

def icao_char_value(c: str) -> int:
    c = c.upper()
    if '0' <= c <= '9':
        return ord(c) - ord('0')
    if 'A' <= c <= 'Z':
        return ord(c) - ord('A') + 10
    if c == '<':
        return 0
    return 0

def calculate_check_digit(data: str) -> int:
    weights = [7, 3, 1]
    total = 0
    for i, char in enumerate(data):
        w = weights[i % 3]
        total += icao_char_value(char) * w
    return total % 10

def verify_checksum(data: str, expected_digit: str) -> bool:
    if not expected_digit or expected_digit == '<':
        return True
    try:
        expected = int(expected_digit)
        return calculate_check_digit(data) == expected
    except ValueError:
        return False

def clean_ocr_digits(val: str) -> str:
    """Corrects common OCR letter substitutions in strictly numerical MRZ positions."""
    repl = {
        'O': '0', 'o': '0', 'Q': '0', 'D': '0',
        'I': '1', 'l': '1', '|': '1', '[': '1', ']': '1',
        'Z': '2', 'z': '2',
        'S': '5', 's': '5',
        'B': '8'
    }
    return "".join(repl.get(c, c) for c in val)

def clean_ocr_alpha(val: str) -> str:
    """Corrects common OCR number substitutions in strictly alphabetical MRZ positions."""
    repl = {
        '0': 'O',
        '1': 'I',
        '2': 'Z',
        '5': 'S',
        '8': 'B'
    }
    return "".join(repl.get(c, c) for c in val)

class MRZParser:
    @staticmethod
    def extract_mrz_lines(raw_text: str) -> List[str]:
        """
        Scans text lines for potential MRZ format lines:
        - TD3: 2 lines of 44 chars (Passports)
        - TD2: 2 lines of 36 chars (Visas / Official IDs)
        - TD1: 3 lines of 30 chars (ID cards)
        """
        if not raw_text:
            return []

        raw_lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
        candidates = []

        for line in raw_lines:
            # Replace whitespace within MRZ lines
            no_spaces = line.replace(" ", "")
            # Convert non-alphanumeric and symbols into standard ICAO filler '<'
            cleaned = re.sub(r'[^A-Za-z0-9<]', '<', no_spaces).upper()

            # Must contain at least one '<' or begin with standard document indicators
            has_mrz_marker = ('<' in cleaned) or cleaned.startswith(('P', 'I', 'V', 'A', 'C'))
            if not has_mrz_marker:
                continue

            # TD3 length candidate (40-48 chars)
            if 40 <= len(cleaned) <= 48:
                norm = cleaned.ljust(44, '<')[:44]
                candidates.append(norm)
            # TD2 length candidate (34-38 chars)
            elif 34 <= len(cleaned) <= 38:
                norm = cleaned.ljust(36, '<')[:36]
                candidates.append(norm)
            # TD1 length candidate (28-32 chars)
            elif 28 <= len(cleaned) <= 32:
                norm = cleaned.ljust(30, '<')[:30]
                candidates.append(norm)

        # De-duplicate consecutive identical lines
        unique_candidates: List[str] = []
        for c in candidates:
            if not unique_candidates or unique_candidates[-1] != c:
                unique_candidates.append(c)

        return unique_candidates

    @classmethod
    def parse(cls, lines: List[str]) -> Optional[MRZData]:
        if not lines:
            return None

        # Filter candidates by length
        td3_lines = [l for l in lines if len(l) == 44]
        if len(td3_lines) >= 2:
            return cls._parse_td3(td3_lines[-2], td3_lines[-1])

        td2_lines = [l for l in lines if len(l) == 36]
        if len(td2_lines) >= 2:
            return cls._parse_td2(td2_lines[-2], td2_lines[-1])

        td1_lines = [l for l in lines if len(l) == 30]
        if len(td1_lines) >= 3:
            return cls._parse_td1(td1_lines[-3], td1_lines[-2], td1_lines[-1])

        return None

    @classmethod
    def _parse_td3(cls, line1: str, line2: str) -> MRZData:
        """
        TD3: Standard Passport Format (2 lines x 44 characters)
        Line 1: P<ISSNAME<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
        Line 2: DOC_NO(9)+CHK(1)+NAT(3)+DOB(6)+CHK(1)+SEX(1)+EXP(6)+CHK(1)+OPT(14)+CHK(1)+COMP(1)
        """
        # Line 1 extraction
        raw_doc_code = clean_ocr_alpha(line1[0:2]).replace('<', '').strip()
        country_code = clean_ocr_alpha(line1[2:5]).replace('<', '').strip()
        name_section = line1[5:].split('<<')
        surname = name_section[0].replace('<', ' ').strip()
        given_names = name_section[1].replace('<', ' ').strip() if len(name_section) > 1 else ""

        # Line 2 extraction with OCR character cleaning on numeric positions
        raw_doc_num = line2[0:9]
        doc_number_clean = raw_doc_num.replace('<', '').strip()
        doc_num_check = clean_ocr_digits(line2[9])

        nationality = clean_ocr_alpha(line2[10:13]).replace('<', '').strip()
        dob_raw = clean_ocr_digits(line2[13:19])
        dob_check = clean_ocr_digits(line2[19])
        raw_sex = line2[20].upper().replace('<', '')
        sex = raw_sex if raw_sex in ('M', 'F') else '<'

        expiry_raw = clean_ocr_digits(line2[21:27])
        expiry_check = clean_ocr_digits(line2[27])
        personal_raw = line2[28:42]
        personal_clean = personal_raw.replace('<', '').strip()
        personal_check = clean_ocr_digits(line2[42])
        overall_check = clean_ocr_digits(line2[43])

        # Verify Check digits
        ck_doc = verify_checksum(raw_doc_num, doc_num_check)
        ck_dob = verify_checksum(dob_raw, dob_check)
        ck_exp = verify_checksum(expiry_raw, expiry_check)

        # Composite data checksum
        composite_data = line2[0:10] + line2[13:20] + line2[21:43]
        ck_overall = verify_checksum(composite_data, overall_check)

        formatted_dob = cls._format_mrz_date(dob_raw, is_dob=True)
        formatted_expiry = cls._format_mrz_date(expiry_raw, is_dob=False)

        all_valid = ck_doc and ck_dob and ck_exp

        return MRZData(
            valid=all_valid,
            raw_mrz=[line1, line2],
            document_type="PASSPORT",
            country_code=country_code,
            surname=surname,
            given_names=given_names,
            passport_number=doc_number_clean,
            nationality=nationality,
            date_of_birth=formatted_dob,
            sex=sex,
            expiry_date=formatted_expiry,
            personal_number=personal_clean,
            checksum_overall=ck_overall,
            checksum_passport_number=ck_doc,
            checksum_dob=ck_dob,
            checksum_expiry=ck_exp
        )

    @classmethod
    def _parse_td2(cls, line1: str, line2: str) -> MRZData:
        """
        TD2: Official ID / Visa Format (2 lines x 36 characters)
        Line 1: V<ISSNAME<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
        Line 2: DOC_NO(9)+CHK(1)+NAT(3)+DOB(6)+CHK(1)+SEX(1)+EXP(6)+CHK(1)+OPT(7)+COMP(1)
        """
        raw_doc_code = clean_ocr_alpha(line1[0:2]).replace('<', '').strip()
        doc_type = "VISA" if raw_doc_code.startswith("V") else "NATIONAL_ID"
        country_code = clean_ocr_alpha(line1[2:5]).replace('<', '').strip()
        name_section = line1[5:].split('<<')
        surname = name_section[0].replace('<', ' ').strip()
        given_names = name_section[1].replace('<', ' ').strip() if len(name_section) > 1 else ""

        raw_doc_num = line2[0:9]
        doc_number_clean = raw_doc_num.replace('<', '').strip()
        doc_num_check = clean_ocr_digits(line2[9])

        nationality = clean_ocr_alpha(line2[10:13]).replace('<', '').strip()
        dob_raw = clean_ocr_digits(line2[13:19])
        dob_check = clean_ocr_digits(line2[19])
        raw_sex = line2[20].upper().replace('<', '')
        sex = raw_sex if raw_sex in ('M', 'F') else '<'

        expiry_raw = clean_ocr_digits(line2[21:27])
        expiry_check = clean_ocr_digits(line2[27])
        optional_data = line2[28:35].replace('<', '').strip()
        overall_check = clean_ocr_digits(line2[35])

        ck_doc = verify_checksum(raw_doc_num, doc_num_check)
        ck_dob = verify_checksum(dob_raw, dob_check)
        ck_exp = verify_checksum(expiry_raw, expiry_check)

        composite_data = line2[0:10] + line2[13:20] + line2[21:35]
        ck_overall = verify_checksum(composite_data, overall_check)

        formatted_dob = cls._format_mrz_date(dob_raw, is_dob=True)
        formatted_expiry = cls._format_mrz_date(expiry_raw, is_dob=False)

        all_valid = ck_doc and ck_dob and ck_exp

        return MRZData(
            valid=all_valid,
            raw_mrz=[line1, line2],
            document_type=doc_type,
            country_code=country_code,
            surname=surname,
            given_names=given_names,
            passport_number=doc_number_clean,
            nationality=nationality,
            date_of_birth=formatted_dob,
            sex=sex,
            expiry_date=formatted_expiry,
            personal_number=optional_data,
            checksum_overall=ck_overall,
            checksum_passport_number=ck_doc,
            checksum_dob=ck_dob,
            checksum_expiry=ck_exp
        )

    @classmethod
    def _parse_td1(cls, line1: str, line2: str, line3: str) -> MRZData:
        """
        TD1: Standard National ID / Card Format (3 lines x 30 characters)
        Line 1: I<ISSDOC_NO(9)+CHK(1)+OPT(15)
        Line 2: DOB(6)+CHK(1)+SEX(1)+EXP(6)+CHK(1)+NAT(3)+OPT(7)+COMP(1)
        Line 3: SURNAME<<GIVEN_NAMES<<<<<<<<<<<<
        """
        raw_doc_code = clean_ocr_alpha(line1[0:2]).replace('<', '').strip()
        country_code = clean_ocr_alpha(line1[2:5]).replace('<', '').strip()
        doc_num_raw = line1[5:14]
        doc_num_clean = doc_num_raw.replace('<', '').strip()
        doc_num_check = clean_ocr_digits(line1[14])

        dob_raw = clean_ocr_digits(line2[0:6])
        dob_check = clean_ocr_digits(line2[6])
        raw_sex = line2[7].upper().replace('<', '')
        sex = raw_sex if raw_sex in ('M', 'F') else '<'

        expiry_raw = clean_ocr_digits(line2[8:14])
        expiry_check = clean_ocr_digits(line2[14])
        nationality = clean_ocr_alpha(line2[15:18]).replace('<', '').strip()
        overall_check = clean_ocr_digits(line2[29])

        name_section = line3.split('<<')
        surname = name_section[0].replace('<', ' ').strip()
        given_names = name_section[1].replace('<', ' ').strip() if len(name_section) > 1 else ""

        ck_doc = verify_checksum(doc_num_raw, doc_num_check)
        ck_dob = verify_checksum(dob_raw, dob_check)
        ck_exp = verify_checksum(expiry_raw, expiry_check)

        composite_data = line1[5:30] + line2[0:7] + line2[8:15] + line2[18:29]
        ck_overall = verify_checksum(composite_data, overall_check)

        formatted_dob = cls._format_mrz_date(dob_raw, is_dob=True)
        formatted_expiry = cls._format_mrz_date(expiry_raw, is_dob=False)

        return MRZData(
            valid=ck_doc and ck_dob and ck_exp,
            raw_mrz=[line1, line2, line3],
            document_type="NATIONAL_ID",
            country_code=country_code,
            surname=surname,
            given_names=given_names,
            passport_number=doc_num_clean,
            nationality=nationality,
            date_of_birth=formatted_dob,
            sex=sex,
            expiry_date=formatted_expiry,
            checksum_overall=ck_overall,
            checksum_passport_number=ck_doc,
            checksum_dob=ck_dob,
            checksum_expiry=ck_exp
        )

    @staticmethod
    def _format_mrz_date(yymmdd: str, is_dob: bool = False) -> str:
        if len(yymmdd) != 6 or not yymmdd.isdigit():
            return yymmdd
        yy = int(yymmdd[0:2])
        mm = yymmdd[2:4]
        dd = yymmdd[4:6]

        # Valid month and day range check
        m_int = int(mm)
        d_int = int(dd)
        if not (1 <= m_int <= 12 and 1 <= d_int <= 31):
            return ""

        # Century rule
        current_year_2digit = datetime.now().year % 100
        if is_dob:
            year = 2000 + yy if yy <= current_year_2digit else 1900 + yy
        else:
            year = 2000 + yy if yy >= 20 else 1900 + yy

        try:
            date(year, m_int, d_int)
            return f"{year}-{mm}-{dd}"
        except ValueError:
            return ""

mrz_parser = MRZParser()
