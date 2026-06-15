import os
import razorpay
from dotenv import load_dotenv

load_dotenv()

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "test_key_id")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "test_key_secret")

client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

def create_razorpay_order(amount_inr: int, receipt_id: str) -> dict:
    """Create an order on Razorpay for the given amount (in INR)."""
    data = {
        "amount": amount_inr * 100,  # Razorpay accepts amount in paise
        "currency": "INR",
        "receipt": receipt_id,
        "payment_capture": 1
    }
    order = client.order.create(data=data)
    return order

def verify_razorpay_signature(order_id: str, payment_id: str, signature: str) -> bool:
    """Verify the payment signature returned by Razorpay."""
    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        })
        return True
    except razorpay.errors.SignatureVerificationError:
        return False
