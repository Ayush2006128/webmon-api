from pydantic import BaseModel

class ChatRequest(BaseModel):
    thread_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    sources: list[str] = []

class ModelSelection(BaseModel):
    model_name: str

class BuyCreditsRequest(BaseModel):
    tier: str

class BuyCreditsResponse(BaseModel):
    order_id: str
    amount_inr: int
    key_id: str

class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

class CreditsResponse(BaseModel):
    credits: float
    last_refill_date: str