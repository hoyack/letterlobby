# app/services/payment_service.py

import stripe
from app.core.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

def create_checkout_session(letter_request_id: str, amount: int, success_url: str, cancel_url: str):
    """
    Create a Stripe Checkout Session for the given amount and letter_request_id.
    amount is in cents (e.g., $5.00 = 500).
    success_url and cancel_url are where Stripe will redirect after payment.
    """
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": "Letter Mailing Service"
                },
                "unit_amount": amount
            },
            "quantity": 1
        }],
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "letter_request_id": letter_request_id
        }
    )
    return session
