import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import DocumentContentFormat
from dotenv import load_dotenv

load_dotenv()
endpoint = os.getenv("DOC_INTELLIGENCE_ENDPOINT")
key = os.getenv("DOC_INTELLIGENCE_KEY")

def extract_markdown(file_bytes):
    client = DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(key))
    poller = client.begin_analyze_document(
        model_id="prebuilt-layout",
        body=file_bytes,
        output_content_format=DocumentContentFormat.MARKDOWN
    )
    result = poller.result()
    return result.content  