import io
import fitz
from fastapi.testclient import TestClient
from app.main import app

def make_pdf(text='x', pages=2):
    doc = fitz.open()
    for i in range(pages):
        page = doc.new_page()
        page.insert_text((72, 72), f'{text} - Page {i + 1}')
    out = doc.tobytes()
    doc.close()
    return out

client = TestClient(app)
resp = client.post('/documents', files={'file': ('sample.pdf', io.BytesIO(make_pdf('BookWorm upload pipeline test.')), 'application/pdf')})
print(resp.status_code)
print(resp.text)
