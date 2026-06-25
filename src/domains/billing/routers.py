import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.security import get_current_user, get_api_key
from src.core.config import RAZORPAY_KEY_ID
from src.models import User, PaymentTransaction
from src.schemas import BuyCreditsRequest, BuyCreditsResponse, VerifyPaymentRequest, CreditsResponse
from src.domains.billing.payments import create_razorpay_order, verify_razorpay_signature

router = APIRouter(tags=["Billing"])

TIERS = {
    "tier_20": {"credits": 20, "price": 255},
    "tier_40": {"credits": 40, "price": 449},
    "tier_90": {"credits": 90, "price": 999},
}

def check_and_refill_credits(user: User, db: Session):
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    if user.last_refill_date.year < now.year or user.last_refill_date.month < now.month:
        if user.credits < 5.0:
            user.credits = 5.0
        user.last_refill_date = now
        db.commit()
        db.refresh(user)

@router.get("/credits", response_model=CreditsResponse, dependencies=[Depends(get_api_key)])
def get_credits(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Retrieve the current user's available credits.
    
    It also checks and automatically refills the user's base credits if a new month has started.
    Returns the current balance and the date of the last refill.
    """
    check_and_refill_credits(user, db)
    return {"credits": user.credits, "last_refill_date": user.last_refill_date.isoformat()}

@router.post("/payment/create-order", response_model=BuyCreditsResponse, dependencies=[Depends(get_api_key)])
def create_order(request: BuyCreditsRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Create a Razorpay payment order for purchasing credits.
    
    Expects a specific tier to be provided. It calculates the amount required based on the tier
    and creates a corresponding Razorpay order, logging the transaction details.
    Returns the order ID and required payment details.
    """
    if request.tier not in TIERS:
        raise HTTPException(status_code=400, detail="Invalid tier")
    
    tier_info = TIERS[request.tier]
    amount = tier_info["price"]
    credits = tier_info["credits"]
    
    receipt_id = f"receipt_{uuid.uuid4().hex[:8]}"
    
    try:
        order = create_razorpay_order(amount, receipt_id)
        
        tx = PaymentTransaction(
            user_id=user.id,
            razorpay_order_id=order["id"],
            amount_inr=amount,
            credits_added=credits,
            status="created"
        )
        db.add(tx)
        db.commit()
        
        return {
            "order_id": order["id"],
            "amount_inr": amount,
            "key_id": RAZORPAY_KEY_ID
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/payment/verify")
def verify_payment(request: VerifyPaymentRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Verify a completed Razorpay payment.
    
    Validates the payment signature against the Razorpay service. If the payment is valid
    and hasn't been processed yet, it updates the transaction status and credits the user's account.
    """
    is_valid = verify_razorpay_signature(request.razorpay_order_id, request.razorpay_payment_id, request.razorpay_signature)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid signature")
        
    tx = db.query(PaymentTransaction).filter(PaymentTransaction.razorpay_order_id == request.razorpay_order_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if tx.status == "paid":
        return {"status": "already_paid"}
        
    tx.status = "paid"
    tx.razorpay_payment_id = request.razorpay_payment_id
    user.credits += tx.credits_added
    
    db.commit()
    return {"status": "success", "credits_added": tx.credits_added, "total_credits": user.credits}
