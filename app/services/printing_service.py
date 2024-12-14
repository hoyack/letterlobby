# app/services/printing_service.py

import os
import pdfkit
import cups
from app.core.config import settings

def html_to_pdf(html_content: str) -> bytes:
    pdf = pdfkit.from_string(html_content, False)
    return pdf

def print_pdf(pdf_bytes: bytes, printer_name: str) -> str:
    # Save PDF to a temp file
    tmp_pdf_path = "/tmp/queued_letter.pdf"
    with open(tmp_pdf_path, "wb") as f:
        f.write(pdf_bytes)

    # Connect to remote CUPS server
    conn = cups.Connection(host=settings.CUPS_SERVER_HOST, port=settings.CUPS_SERVER_PORT)
    printers = conn.getPrinters()

    if printer_name not in printers:
        os.remove(tmp_pdf_path)
        raise ValueError(f"Printer {printer_name} not found")

    job_id = conn.printFile(printer_name, tmp_pdf_path, "QueuedLetterJob", {})
    os.remove(tmp_pdf_path)
    return str(job_id)
