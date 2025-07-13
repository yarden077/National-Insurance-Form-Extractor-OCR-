import re
def compare_with_ground_truth(pred, truth):
    """
    Compares two nested JSON dicts, returns accuracy and details.
    """
    mismatches = []
    total_fields = 0
    correct = 0

    def compare_recursive(p, t, prefix=""):
        nonlocal total_fields, correct
        # Handle dicts
        if isinstance(t, dict):
            for key in t:
                field_path = f"{prefix}.{key}" if prefix else key
                compare_recursive(p.get(key, ""), t[key], field_path)
        else:
            total_fields += 1
            if (str(p).strip() == str(t).strip()):
                correct += 1
            else:
                mismatches.append((prefix, p, t))

    compare_recursive(pred, truth)
    accuracy = correct / total_fields if total_fields > 0 else 0.0
    return accuracy, mismatches, total_fields, correct


def validate_extracted_data(data):
    errors = []

    # 1. Mandatory fields
    mandatory_fields = [
        "lastName", "firstName", "idNumber", "gender",
        "dateOfBirth", "address", "medicalInstitutionFields"
    ]
    for field in mandatory_fields:
        value = data.get(field)
        if not value or (isinstance(value, str) and not value.strip()):
            errors.append(f"Missing or empty required field: {field}")

    # 2. ID number (should be 9 digits)
    id_number = data.get("idNumber", "")
    if not re.fullmatch(r"\d{9}", id_number):
        errors.append("idNumber is missing or not a valid 9-digit number.")

    # 3. Mobile phone (if present)
    mobile = data.get("mobilePhone", "")
    if mobile and not re.fullmatch(r"05\d{8}", mobile):
        errors.append("mobilePhone must be 10 digits and start with '05'.")

    # 4. Landline phone (if present)
    landline = data.get("landlinePhone", "")
    if landline and not re.fullmatch(r"0\d{8,9}", landline):
        errors.append("landlinePhone must be 9 or 10 digits and start with '0'.")

    # 5. Date fields (day/month/year lengths)
    def validate_date(d, label):
        if not all([d.get("day"), d.get("month"), d.get("year")]):
            errors.append(f"{label} is incomplete.")
        elif not (len(d["day"]) == 2 and len(d["month"]) == 2 and len(d["year"]) == 4):
            errors.append(f"{label} should be in DD/MM/YYYY format.")

    for date_label in ["dateOfBirth", "dateOfInjury", "formFillingDate", "formReceiptDateAtClinic"]:
        validate_date(data.get(date_label, {}), date_label)

    # 6. Address completeness
    address = data.get("address", {})
    if not any(address.get(k, "").strip() for k in ["street", "city"]):
        errors.append("Address is incomplete (at least street and city should be filled).")

    # 7. Health fund (HMO) is filled
    hmo = data.get("medicalInstitutionFields", {}).get("healthFundMember", "")
    if not hmo:
        errors.append("Health fund membership field is missing.")

    return errors