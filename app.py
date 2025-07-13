# main_app.py
import streamlit as st
from ocr import extract_markdown
import os
from openai import AzureOpenAI
from dotenv import load_dotenv
import re
import json
from evaluation_ocr import validate_extracted_data, compare_with_ground_truth
load_dotenv()
api_key = os.getenv("AZURE_OPENAI_KEY1")
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
deployment_name = "gpt-4o"

def fix_mobile_phone_fields(json_data):
    """
    Validates and fixes the 'mobilePhone' field in the extracted JSON.
    Ensures the number is 10 digits, starts with '05', and corrects it if possible.
    """
    phone = json_data.get("mobilePhone", "")
    # Remove any non-digit characters
    digits = re.sub(r'\D', '', phone)
    # Try to fix the phone to be 10 digits and start with '05'
    if len(digits) == 10 and digits.startswith('05'):
        fixed = digits
    else:
        # If too long, try to find a substring of 10 digits that starts with '05'
        match = re.search(r'05\d{8}', digits)
        if match:
            fixed = match.group(0)
        else:
            # If too short or not starting with 05, try to fix
            # Option 1: If starts with 5, add 0 at start
            if len(digits) == 9 and digits.startswith('5'):
                fixed = '0' + digits
            # Option 2: If starts with 0, add 5 after 0
            elif len(digits) == 9 and digits.startswith('0'):
                fixed = '05' + digits[1:]

            # Option 3: Otherwise, take last 9 digits and add 0 in front
            elif len(digits) >= 9:
                fixed = '0' + digits[-9:]

            else:
                fixed = digits  # Not enough data, just keep what was found

    # Only set if it's 10 digits and starts with 05
    if len(fixed) == 10 and fixed.startswith('05'):
        json_data["mobilePhone"] = fixed
    else:
        json_data["mobilePhone"] = ""  # If still invalid, leave empty

    print(json.dumps(json_data, ensure_ascii=False, indent=2))
    return json_data


# --- Streamlit UI ---
st.set_page_config(page_title="National Insurance Form Extractor", layout="centered")
st.title("National Insurance Form Extractor")

uploaded_file = st.file_uploader("Upload a scanned PDF/JPG file", type=["pdf", "jpg", "jpeg", "png"])

if uploaded_file:
    file_bytes = uploaded_file.read()
    with st.spinner("Running OCR..."):
        try:
            markdown = extract_markdown(file_bytes)
            st.markdown("**Detected Form (OCR markdown):**")
            # Add the full markdown in a collapsible section
            with st.expander("See full OCR output here"):
                st.code(markdown, language="markdown")
        except Exception as e:
            st.error(f"OCR failed: {e}")
            st.stop()

    # Prompt the LLM with the markdown
    prompt = f"""
                You are an expert at extracting structured information from scanned Hebrew/English insurance forms. 
                You are given the OCR result of the form as markdown text. It includes checkboxes (☒ = selected, ☐ = unselected) and Hebrew labels (could be English as well).

                Instructions:
                - Extract the information and return it in the JSON format below.
                - Use the visible `☒` or `☐` symbols next to Hebrew/English text to infer fields like `gender` and `healthFundMember`, etc.
                - For gender, look for a ☒ next to זכר or נקבה.
                - For healthFundMember, look for ☒ next to any of: כללית, מכבי, מאוחדת, לאומית.
                - For signature, if the form includes the word "חתימה" or "חתימהX" with the person's name, consider it signed.
                - For both `landlinePhone` and `mobilePhone`:
                    1. If the number starts with `0`, leave it as is.
                    2. If the number starts with any other digit, remove that digit and put a single `0` at the beginning.
                    3. Do not allow more than one leading zero.
                    Examples:
                        - If the number is `8975423541`, output `0975423541`
                        - If the number is `08975423541`, output `08975423541`
                        - If the number is `1234567890`, output `0234567890`
                        - If the number is `0541234567`, output `0541234567`
                - If any field is missing or uncertain, return an empty string for it.
                - Output only valid JSON. No comments or explanations.

                Here is the markdown-formatted OCR content:

                {markdown}

                OUTPUT FORMAT:
                {{
                "lastName": "",
                "firstName": "",
                "idNumber": "" (should be a valid 9-digit number),
                "gender": "",
                "dateOfBirth": {{"day": "", "month": "", "year": ""}},
                "address": {{
                    "street": "",
                    "houseNumber": "",
                    "entrance": "",
                    "apartment": "",
                    "city": "",
                    "postalCode": "",
                    "poBox": ""
                }},
                "landlinePhone": "",
                "mobilePhone": "",
                "jobType": "",
                "dateOfInjury": {{"day": "", "month": "", "year": ""}},
                "timeOfInjury": "",
                "accidentLocation": "",
                "accidentAddress": "",
                "accidentDescription": "",
                "injuredBodyPart": "",
                "signature": "",
                "formFillingDate": {{"day": "", "month": "", "year": ""}},
                "formReceiptDateAtClinic": {{"day": "", "month": "", "year": ""}},
                "medicalInstitutionFields": {{
                    "healthFundMember": "",
                    "natureOfAccident": "",
                    "medicalDiagnoses": ""
                }}
                }}
"""
    with st.spinner("Sending to LLM..."):
        try:
            client = AzureOpenAI(
                api_key=api_key,
                azure_endpoint=endpoint,
                api_version="2024-02-15-preview"
            )
            response = client.chat.completions.create(
                model=deployment_name,
                messages=[
                    {"role": "system", "content": "You are an expert at form field extraction."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1024,
                temperature=0.1
            )
            answer = response.choices[0].message.content.strip()
            st.success("Extracted JSON :")

            # Strip markdown code blocks if present
            # Remove Markdown code fences if present
            if answer.startswith("```json"):
                answer = answer[7:]
            if answer.startswith("```"):
                answer = answer[3:]
            if answer.endswith("```"):
                answer = answer[:-3]
            answer = answer.strip()
         

            data = json.loads(answer)
            data = fix_mobile_phone_fields(data)
            st.code(json.dumps(data, ensure_ascii=False, indent=2), language="json")
            st.markdown("### Evaluation: ")
            # checking if answer is valid
            validation_errors = validate_extracted_data(data)
            if not validation_errors:
                st.success("✅ Data is complete and valid!")
            else:
                st.warning("⚠️ Validation errors found:")
                for err in validation_errors:
                    st.write(f"- {err}")

            # calculting accuarcy 
            filename = uploaded_file.name.lower()
            ex_num = None
            match = re.search(r"(ex\d+)", filename)
            if match:
                ex_num = match.group(1)
                gt_path = f"phase1_data/ground_truth/{ex_num}_ground_truth.json"
                if os.path.exists(gt_path):
                    with open(gt_path, "r", encoding="utf-8") as f:
                        ground_truth = json.load(f)
                else:
                    st.warning(f"Ground truth file not found: {gt_path}")
                    ground_truth = None
            else:
                st.warning("Could not find exercise number in filename.")
                ground_truth = None
                            
            accuracy, mismatches, total, correct = compare_with_ground_truth(data, ground_truth)

            st.write(f"**Accuracy:** {accuracy:.2%} ({correct}/{total} fields matched)")

            if mismatches:
                st.warning(f"{len(mismatches)} mismatches found:")
                for field, val_pred, val_true in mismatches:
                    st.write(f"- **{field}**: predicted = `{val_pred}`, expected = `{val_true}`")
            else:
                st.success("All fields matched the ground truth!")
        except Exception as e:
            st.error(f"LLM extraction failed: {e}")


