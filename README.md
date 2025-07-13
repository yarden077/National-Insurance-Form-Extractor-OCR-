# National Insurance Form Extractor (OCR + GenAI)
A Streamlit app that extracts structured data from scanned Israeli National Insurance forms using Azure Document Intelligence (OCR) and Azure OpenAI GPT-4o.

## Project Structure

- `app.py`: Streamlit UI and main logic
- `ocr.py`: OCR function using Azure Document Intelligence
- `evaluation_ocr.py`: Validation and evaluation functions
- `phase1_data/`: Data and ground truth files
- `requirements.txt`: Required pip packages
## How to Run

1. **Clone the repository:**
    ```bash
    git clone https://github.com/<yarden077>/<National-Insurance-Form-Extractor-OCR->.git
    cd <National-Insurance-Form-Extractor-OCR->
    ```

2. **Install requirements:**
    ```bash
    pip install -r requirements.txt
    ```

3. **Create your `.env` file:**
    - Copy the provided `.env.example` to `.env`:
      ```bash
      cp .env.example .env
      ```
    - Fill in your Azure credentials in the `.env` file.

4. **Run the Streamlit app:**
    ```bash
    streamlit run app.py
    ```

5. **Upload a sample form (PDF/JPG/PNG), view the extracted JSON and evaluation!**
