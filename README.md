# National Insurance Form Extractor (OCR + GenAI)
A Streamlit app that extracts structured data from scanned Israeli National Insurance forms using Azure Document Intelligence (OCR) and Azure OpenAI GPT-4o.

## Setup

1. Clone this repository.
2. Install requirements:
   `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in your Azure credentials.
4. Run the app:
  `streamlit run app.py`

## Project Structure

- `app.py`: Streamlit UI and main logic
- `ocr.py`: OCR function using Azure Document Intelligence
- `evaluation_ocr.py`: Validation and evaluation functions
- `phase1_data/`: Data and ground truth files
- `requirements.txt`: Required pip packages
