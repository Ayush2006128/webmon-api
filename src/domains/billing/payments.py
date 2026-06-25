import razorpay
from src.core.config import RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET

client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

def create_razorpay_order(amount_inr: int, receipt_id: str) -> dict:
    data = {
        "amount": amount_inr * 100,  # Razorpay accepts amount in paise
        "currency": "INR",
        "receipt": receipt_id,
        "payment_capture": 1
    }
    order = client.order.create(data=data)
    return order

def verify_razorpay_signature(order_id: str, payment_id: str, signature: str) -> bool:
    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        })
        return True
    except razorpay.errors.SignatureVerificationError:
        return False
