# app/services/mailing_service.py

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
    # Split the letter into paragraphs by double newlines
    paragraphs = [p.strip() for p in letter_text.strip().split("\n\n") if p.strip()]

    # Convert each paragraph into a <p> element
    # Also consider replacing placeholders like "[Your Name]" if present in the text
    paragraph_html = "\n".join(f"<p>{p}</p>" for p in paragraphs)

    # Construct the full HTML
    # Insert addresses and names into the template
    # You can customize the style as you wish
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
      {sender_address["city"]}, {sender_address["state"]} {sender_address["zip"]}
    </div>

    <!-- Recipient Address -->
    <div style="margin-bottom: 1in;">
      {recipient_name}<br>
      {recipient_address["line1"]}<br>
      {recipient_address["city"]}, {recipient_address["state"]} {recipient_address["zip"]}
    </div>

    {paragraph_html}

    <p>Sincerely,<br>[Your Name]</p>
  </body>
</html>
"""
    return html

def send_letter(formatted_html: str, recipient_name: str, recipient_address: dict) -> dict:
    """
    Sends the formatted HTML letter to Lob as a multipart/form-data file upload.
    """
    auth = (settings.LOB_API_KEY, '')

    # Prepare the file payload
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

        "from[name]": "Your Organization",
        "from[address_line1]": "500 Example St",
        "from[address_city]": "YourCity",
        "from[address_state]": "TX",
        "from[address_zip]": "78702",
        "from[address_country]": "US",

        "color": "false",
        "double_sided": "false",
        "use_type": "operational"
    }

    response = requests.post(LOB_BASE_URL, auth=auth, data=data, files=files)
    response.raise_for_status()
    return response.json()

def mail_letter(letter_req, db):
    """
    Example of how you'd integrate the formatting and sending steps inside your mail endpoint logic.
    Assumes letter_req is a UserLetterRequest object.
    """
    if letter_req.status != "paid":
        raise ValueError("Letter not paid for mailing.")

    # Parse final_letter_text (JSON) to get the raw draft
    import json
    letter_data = json.loads(letter_req.final_letter_text)
    raw_letter_text = letter_data.get("letter", "")

    # Format the letter with variables
    # Assume we have recipient_name, recipient_address from politician
    politician = letter_req.politician
    recipient_name = politician.name
    recipient_address = {
        "line1": politician.office_address_line1,
        "line2": politician.office_address_line2 or "",
        "city": politician.office_city,
        "state": politician.office_state,
        "zip": politician.office_zip
    }

    sender_name = "Your Organization"
    sender_address = {
        "line1": "500 Example St",
        "city": "YourCity",
        "state": "TX",
        "zip": "78702"
    }

    formatted_html = format_letter_text(raw_letter_text, recipient_name, recipient_address, sender_name, sender_address)

    try:
        mail_response = send_letter(formatted_html, recipient_name, recipient_address)
    except requests.HTTPError as e:
        # Handle failure, create MailingTransaction with failed status, etc.
        raise

    # On success, update mailing transaction and letter request status
    # ...
    return mail_response