import re
from typing import List, Optional, Tuple, Dict, Any
from backend.app.models.schemas import MRZData

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

class MRZParser:
    @staticmethod
    def extract_mrz_lines(raw_text: str) -> List[str]:
        """
        Scans text lines for potential MRZ format lines (TD3: 44 chars, TD1: 30 chars).
        """
        lines = [line.strip().replace(" ", "").upper() for line in raw_text.splitlines() if line.strip()]
        mrz_candidates = []
        for line in lines:
            # Clean characters to valid MRZ alphabet
            cleaned = re.sub(r'[^A-Z0-9<]', '<', line)
            # TD3 length is 44
            if 40 <= len(cleaned) <= 46 and ('<' in cleaned or cleaned.startswith('P')):
                # Normalize to 44
                if len(cleaned) < 44:
                    cleaned = cleaned.ljust(44, '<')
                elif len(cleaned) > 44:
                    cleaned = cleaned[:44]
                mrz_candidates.append(cleaned)
            # TD1 length is 30
            elif 28 <= len(cleaned) <= 32 and ('<' in cleaned or cleaned.startswith(('I', 'A', 'C'))):
                if len(cleaned) < 30:
                    cleaned = cleaned.ljust(30, '<')
                elif len(cleaned) > 30:
                    cleaned = cleaned[:30]
                mrz_candidates.append(cleaned)

        return mrz_candidates

    @classmethod
    def parse(cls, lines: List[str]) -> Optional[MRZData]:
        if not lines:
            return None

        # Try TD3 (Passport - 2 lines of 44 chars)
        td3_lines = [l for l in lines if len(l) == 44]
        if len(td3_lines) >= 2:
            return cls._parse_td3(td3_lines[-2], td3_lines[-1])

        # Try TD1 (ID Card - 3 lines of 30 chars)
        td1_lines = [l for l in lines if len(l) == 30]
        if len(td1_lines) >= 3:
            return cls._parse_td1(td1_lines[-3], td1_lines[-2], td1_lines[-1])

        return None

    @classmethod
    def _parse_td3(cls, line1: str, line2: str) -> MRZData:
        # Line 1: P<ISSNAMES<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
        # P = Passport, ISS = 3-letter country code
        doc_type = line1[0:2].replace('<', '').strip()
        country_code = line1[2:5].replace('<', '').strip()
        name_section = line1[5:].split('<<')
        surname = name_section[0].replace('<', ' ').strip()
        given_names = name_section[1].replace('<', ' ').strip() if len(name_section) > 1 else ""

        # Line 2: DocumentNumber(9) + CheckDigit(1) + Nationality(3) + DOB(6) + CheckDigit(1) + Sex(1) + Expiry(6) + CheckDigit(1) + Personal(14) + CheckDigit(1) + OverallCheck(1)
        doc_number_raw = line2[0:9]
        doc_number_clean = doc_number_raw.replace('<', '').strip()
        doc_num_check = line2[9]

        nationality = line2[10:13].replace('<', '').strip()
        dob_raw = line2[13:19]
        dob_check = line2[19]
        sex = line2[20].replace('<', '').strip()
        expiry_raw = line2[21:27]
        expiry_check = line2[27]
        personal_raw = line2[28:42]
        personal_check = line2[42]
        overall_check = line2[43]

        # Verify Check digits
        ck_doc = verify_checksum(doc_number_raw, doc_num_check)
        ck_dob = verify_checksum(dob_raw, dob_check)
        ck_exp = verify_checksum(expiry_raw, expiry_check)

        # Composite data: doc(9)+check(1)+dob(6)+check(1)+exp(6)+check(1)+pers(14)+check(1)
        composite_data = line2[0:10] + line2[13:20] + line2[21:43]
        ck_overall = verify_checksum(composite_data, overall_check)

        # Format dates (YYMMDD -> YYYY-MM-DD)
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
            personal_number=personal_raw.replace('<', '').strip(),
            checksum_overall=ck_overall,
            checksum_passport_number=ck_doc,
            checksum_dob=ck_dob,
            checksum_expiry=ck_exp
        )

    @classmethod
    def _parse_td1(cls, line1: str, line2: str, line3: str) -> MRZData:
        doc_type = line1[0:2].replace('<', '').strip()
        country_code = line1[2:5].replace('<', '').strip()
        doc_num_raw = line1[5:14]
        doc_num_clean = doc_num_raw.replace('<', '').strip()
        doc_num_check = line1[14]

        dob_raw = line2[0:6]
        dob_check = line2[6]
        sex = line2[7].replace('<', '').strip()
        expiry_raw = line2[8:14]
        expiry_check = line2[14]
        nationality = line2[15:18].replace('<', '').strip()

        name_section = line3.split('<<')
        surname = name_section[0].replace('<', ' ').strip()
        given_names = name_section[1].replace('<', ' ').strip() if len(name_section) > 1 else ""

        ck_doc = verify_checksum(doc_num_raw, doc_num_check)
        ck_dob = verify_checksum(dob_raw, dob_check)
        ck_exp = verify_checksum(expiry_raw, expiry_check)

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
            checksum_overall=True,
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
        # DOB: 30-99 -> 1900s, 00-29 -> 2000s
        # Expiry: usually 2000s
        if is_dob:
            year = 1900 + yy if yy > 26 else 2000 + yy
        else:
            year = 2000 + yy
        return f"{year}-{mm}-{dd}"

mrz_parser = MRZParser()
