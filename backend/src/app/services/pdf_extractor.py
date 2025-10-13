import requests
import pdfplumber
import io
import time

def extract_pdf_text_retry(url, retries=3, delay=5):
    headers = {'User-Agent': 'Mozilla/5.0'}
    for attempt in range(retries):
        try:
            res = requests.get(url, headers=headers, timeout=30)
            if res.status_code == 200 and res.content[:4] == b'%PDF':
                with pdfplumber.open(io.BytesIO(res.content)) as pdf:
                    return " ".join([page.extract_text() or '' for page in pdf.pages])
            time.sleep(delay)
        except Exception:
            time.sleep(delay)
    return "Failed to extract text."
