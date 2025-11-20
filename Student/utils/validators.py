# student/utils/validators.py
import re

def is_valid_registration(reg):
    if not reg:
        return False
    # Basic check like UAP25001 or similar (letters+digits)
    return bool(re.match(r"^[A-Za-z0-9\-]+$", reg.strip()))
