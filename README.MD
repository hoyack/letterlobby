# Prelude
The other day a politician sponsored a bill I didn't like and I wanted to write them a letter in protest. I decided to build this project to help people write politicians more letters. The power of a letter being mailed to a politician has always been stated to be one of the highest impact activities that a citizen can do to express their opinion, yet so few people have the nessarry tools on hand today to do so.

# Introduction
This project's motivation is to provide a framework for mailing letters to politicians.
It incorporates the concept of a "Bill" which can be created and "Politicians" which can be stored.
A user may call for a "letter" related to the "Bill" and have it sent to the "Politician"
The letter is written by AI, on behalf of the user.
It incoprorates the user's feedback and sentiment.
Payment is collected from the user to cover the costs of mailing the letter.
The letter is mailed using a 3rd party Direct-Mail API service.

# Prerequisites
You must be running OLLAMA locally and have a model loaded:
https://github.com/ollama/ollama
```
curl -fsSL https://ollama.com/install.sh | sh
ollama serve
ollama run llama3.2
```
Confirm API works:
```
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2",
  "prompt":"Why is the sky blue?"
}'
```

The project relies on an accessable Postgres server.
```
docker run --name letterlobby-postgres \
    -e POSTGRES_USER=letterlobby_user \
    -e POSTGRES_PASSWORD=letterlobby_password \
    -e POSTGRES_DB=letterlobby_db \
    -p 5432:5432 \
    -d postgres:14
```

Test with PG Admin. Once you can connect to your PG server you can continue.

You will need to use the connection string for Postgres in the `.env` later:
```
DATABASE_URL=postgresql+psycopg2://letterlobby_user:letterlobby_password@localhost:5432/letterlobby_db
```

Install Anaconda (optional / recommended if not using Docker)
https://docs.anaconda.com/distro-or-miniconda/

Obtain STRIPE dev API key:
https://support.stripe.com/questions/what-are-stripe-api-keys-and-how-to-find-them

Obtain the Stripe API Key (Test Mode) for use in the `.env`
```
STRIPE_SECRET_KEY=sk_test_xxxxxx
```
Set up Stripe Webhook:
https://docs.stripe.com/development/dashboard/webhooks

Configure Stripe to Listen for Event Type `checkout.session.completed`
Obtain the Stripe Webhook "Signing Secret" for use in the `.env`
```
STRIPE_ENDPOINT_SECRET=whsec_xxxxx
```
Set up LOB:
https://docs.lob.com/#tag/Getting-Started`

Obtain the LOB API Key (test) for use in the `.env`
```
LOB_API_KEY=live_XXXXXXXXXXXXXXXXXXXXXXX
```
# Local Setup

RUN `git clone https://github.com/hoyack/letterlobby.git`
```
cd letterlobby
```
If you want to use Anaconda or Miniconda (otherwise venv is recommend):
```
conda create -n letterlobby python=3.10
conda activate letterlobby
```
Continue with installation once your environment has Python running.
```
pip install -r requirements.txt
cp .env-sample .env
```
Edit the `.env` file to include the nessarry variables:
`nano .env` or use `code .` to start VS Code in the working directory.
```
DATABASE_URL=postgresql+psycopg2://letterlobby_user:letterlobby_password@localhost:5432/letterlobby_db
STRIPE_SECRET_KEY=sk_test_xxxxxx
STRIPE_ENDPOINT_SECRET=whsec_xxxxx
LOB_API_KEY=live_XXXXXXXXXXXXXXXXXXXXXXX
```
# Start Server

```
RUN `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
```

## Expose the project to recieve webhook callbacks
If running locally, for dev/testing you can use NGROK to get Stripe webhook callbacks.
Install NGROK:
```
curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
	| sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \
	&& echo "deb https://ngrok-agent.s3.amazonaws.com buster main" \
	| sudo tee /etc/apt/sources.list.d/ngrok.list \
	&& sudo apt update \
	&& sudo apt install ngrok
```

Set up NGROK
```
ngrok config add-authtoken <your-secret-token>
```
Start the NGROK server on the port you host this project:
`ngrok http http://localhost:8000`

# Building with Docker
You must be running Postgres and it must be started. (See # Prerequisites).
Run the following commands (tested on Ubuntu)
```
git clone https://github.com/hoyack/letterlobby.git`
cd letterlobby
cp .env-sample .env
```
Edit the `.env` and if using a local Docker Postgres container your postgres connection string might look like this:
```
DATABASE_URL=postgresql+psycopg2://letterlobby_user:letterlobby_password@host.docker.internal:5432/letterlobby_db
```
note the host is `host.docker.internal:5432` because the Fast API has to connect to Postgres at a host that it can communicate with and if you use something like `localhost` then the container will try to communicate with itself at `localhost` instead of the `localhost` on your bare metal so by using this `host.docker.internal` hostname, our postgres connection string should be able to connect to the database.
```
docker compose build
docker compose up
```
Now you should see something like:
```
~/letterlobby$ docker compose up
WARN[0000] /home/hoyack/letterlobby/docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion 
[+] Running 1/1
 ✔ Container letterlobby-app-1  Recreated                                                            0.1s 
Attaching to app-1
app-1  | INFO:     Started server process [1]
app-1  | INFO:     Waiting for application startup.
app-1  | INFO:     Application startup complete.
app-1  | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
app-1  | INFO:     172.18.0.1:57980 - "GET / HTTP/1.1" 200 OK

```
and then you should be able to access your project at `http://localhost:8000`
At this point you can also follow the previous instructions to expose the project by `NGROK` if you want and configure the stripe webhook accordingly. 

# Using The Project

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
