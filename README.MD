uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

`curl http://localhost:8000/bills`

This should return a list of bills with their id. For example:
```
[
  {
    "title": "My First Bill",
    "description": "A test bill",
    "bill_number": "SB001",
    "legislative_body": "Texas Senate",
    "status": null,
    "id": "6c66d061-25c5-47f5-8a95-dc3694f6aecb",
    "created_at": "2024-12-07T16:27:50.526490Z",
    "updated_at": null
  }
]
```
`curl http://localhost:8000/politicians`

check politicians:
```
[
  {
    "name": "Jane Doe",
    "title": "Senator",
    "office_address_line1": "100 Main St",
    "office_address_line2": null,
    "office_city": "Austin",
    "office_state": "TX",
    "office_zip": "78701",
    "legislative_body": "Texas Senate",
    "id": "365c2a96-7d81-4816-82b1-bd6be9ba028a",
    "created_at": "2024-12-07T16:31:06.226373Z",
    "updated_at": null
  }
]
```
Take note of bill_id and politician_id from the above responses.

```
curl -X POST http://localhost:8000/letter-requests/ \
  -H "Content-Type: application/json" \
  -d '{
        "bill_id": "6c66d061-25c5-47f5-8a95-dc3694f6aecb",
        "politician_id": "365c2a96-7d81-4816-82b1-bd6be9ba028a",
        "user_provided_name": "John Doe",
        "user_provided_address_line1": "123 Maple St",
        "user_provided_city": "Austin",
        "user_provided_state": "TX",
        "user_provided_zip": "78701",
        "user_comments": "I strongly support this new transparency bill, it will help citizens trust the process."
      }'
```

This should return a JSON object with a new letter_id. For example:

```
{
  "bill_id": "6c66d061-25c5-47f5-8a95-dc3694f6aecb",
  "politician_id": "365c2a96-7d81-4816-82b1-bd6be9ba028a",
  "user_provided_name": "John Doe",
  "user_provided_address_line1": "123 Maple St",
  "user_provided_address_line2": null,
  "user_provided_city": "Austin",
  "user_provided_state": "TX",
  "user_provided_zip": "78701",
  "user_comments": "I strongly support this new transparency bill, it will help citizens trust the process.",
  "id": "NEW-LETTER-ID-HERE",
  "final_letter_text": null,
  "status": "drafting",
  "stripe_charge_id": null,
  "paid_at": null,
  "created_at": "2024-12-07T...",
  "updated_at": null
}
```

Take note of the id in this response (the NEW-LETTER-ID-HERE).

Now you can draft the letter by calling the /draft endpoint with any runtime parameters (like stance and personal feedback) if desired. For example:

```
curl -X POST http://localhost:8000/letter-requests/NEW-LETTER-ID-HERE/draft \
  -H "Content-Type: application/json" \
  -d '{
        "bill_name": "Transparency Act",
        "lawmaker_name": "Senator Jane Doe",
        "stance": "support",
        "support_level": 10,
        "personal_feedback": "I'd like more clarity on how committee discussions will be reported."
      }'
```
Once finalized, initiate payment:
`curl -X POST http://localhost:8000/letter-requests/NEW-LETTER-ID-HERE/pay`

After payment completion, Stripe will send a webhook to your /stripe-webhook endpoint. If everything is configured correctly, the UserLetterRequest status should change to paid.

You can verify by fetching the letter request again:
`curl http://localhost:8000/letter-requests/NEW-LETTER-ID-HERE`

check that status is paid.

Next create the direct mailer
`curl -X POST http://localhost:8000/letter-requests/<LETTER_REQUEST_UUID>/mail`

Expect a response such as
```
    "message": "Letter mailed successfully"
```
