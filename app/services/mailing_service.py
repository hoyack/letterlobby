# app/services/mailing_service.py

import json
import requests
from app.core.config import settings

LOB_BASE_URL = "https://api.lob.com/v1/letters"

def format_letter_text(
    letter_text: str,
    recipient_name: str,
    recipient_address: dict,
    sender_name: str,
    sender_address: dict
) -> str:
    """
    Convert plain drafted text into styled HTML, inserting variables like recipient name and sender details.
    Assumes letter_text is a string with paragraphs separated by double newlines.
    """
    paragraphs = [p.strip() for p in letter_text.strip().split("\n\n") if p.strip()]
    paragraph_html = "\n".join(f"<p>{p}</p>" for p in paragraphs)

    html = f"""
<html>
  <head>
    <meta charset="UTF-8">
    <style>
      body {{
        font-family: "Times New Roman", serif;
        font-size: 12pt;
        margin: 1in;
      }}
      p {{
        margin-bottom: 0.5em;
        line-height: 1.5em;
      }}
    </style>
  </head>
  <body>
    <!-- Sender Address -->
    <div style="margin-bottom: 1in;">
      {sender_name}<br>
      {sender_address["line1"]}<br>
      {sender_address.get("line2","")}<br>
      {sender_address["city"]}, {sender_address["state"]} {sender_address["zip"]}
    </div>

    <!-- Recipient Address -->
    <div style="margin-bottom: 1in;">
      {recipient_name}<br>
      {recipient_address["line1"]}<br>
      {recipient_address.get("line2","")}<br>
      {recipient_address["city"]}, {recipient_address["state"]} {recipient_address["zip"]}
    </div>

    {paragraph_html}

    <p>Sincerely,<br>[Your Name]</p>
  </body>
</html>
"""
    return html

def send_letter(
    formatted_html: str,
    recipient_name: str,
    recipient_address: dict,
    sender_name: str,
    sender_address: dict
) -> dict:
    """
    Sends the formatted HTML letter to Lob as a multipart/form-data file upload.
    """
    auth = (settings.LOB_API_KEY, '')

    files = {
        'file': ('letter.html', formatted_html, 'text/html')
    }

    data = {
        "description": "Legislative letter",
        "to[name]": recipient_name,
        "to[address_line1]": recipient_address["line1"],
        "to[address_line2]": recipient_address.get("line2", ""),
        "to[address_city]": recipient_address["city"],
        "to[address_state]": recipient_address["state"],
        "to[address_zip]": recipient_address["zip"],
        "to[address_country]": "US",

        "from[name]": sender_name,
        "from[address_line1]": sender_address["line1"],
        "from[address_line2]": sender_address.get("line2",""),
        "from[address_city]": sender_address["city"],
        "from[address_state]": sender_address["state"],
        "from[address_zip]": sender_address["zip"],
        "from[address_country]": "US",

        "color": "false",
        "double_sided": "false",
        "use_type": "operational"
    }

    response = requests.post(LOB_BASE_URL, auth=auth, data=data, files=files)
    response.raise_for_status()
    return response.json()

def mail_letter(letter_req, db, sender_address: dict):
    """
    Send the letter via Lob and record the result in a mailing transaction.
    'sender_address' should be a dict with keys: line1, line2(optional), city, state, zip, organization_name(optional)
    """
    if letter_req.status != "paid":
        raise ValueError("Letter not paid for mailing.")

    letter_data = json.loads(letter_req.final_letter_text)
    letter_text = letter_data.get("letter", "")

    if not letter_text or not isinstance(letter_text, str):
        raise ValueError("No valid 'letter' field found in final_letter_text.")

    politician = letter_req.politician
    recipient_name = politician.name
    recipient_address = {
        "line1": politician.office_address_line1,
        "line2": politician.office_address_line2 or "",
        "city": politician.office_city,
        "state": politician.office_state,
        "zip": politician.office_zip
    }

    sender_name = sender_address.get("organization_name","Your Organization")
    formatted_html = format_letter_text(
        letter_text,
        recipient_name,
        recipient_address,
        sender_name=sender_name,
        sender_address=sender_address
    )

    from app.models.mailing_transaction import MailingTransaction, MailingStatus

    try:
        mail_response = send_letter(
            formatted_html,
            recipient_name,
            recipient_address,
            sender_name=sender_name,
            sender_address=sender_address
        )
    except requests.HTTPError as e:
        # On failure, record a failed mailing transaction
        mailing_tx = MailingTransaction(
            user_letter_request_id=letter_req.id,
            external_mail_service_id=None,
            status=MailingStatus.failed,
            error_message=str(e),
            mail_service_response=None
        )
        db.add(mailing_tx)
        db.commit()
        raise

    # On success, record a successful mailing transaction with mail_service_response
    mailing_tx = MailingTransaction(
        user_letter_request_id=letter_req.id,
        external_mail_service_id=mail_response.get("id"),
        status=MailingStatus.sent,
        error_message=None,
        mail_service_response=mail_response
    )
    db.add(mailing_tx)
    letter_req.status = "mailed"
    db.commit()
    db.refresh(letter_req)

    return mail_response
