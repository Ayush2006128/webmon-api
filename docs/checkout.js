document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const order_id = urlParams.get('order_id');
    const amount = urlParams.get('amount'); // Optional, display only
    const key_id = urlParams.get('key_id');
    const token = urlParams.get('token');
    const api_base = urlParams.get('api_base') || 'https://webmon-api.fastapicloud.dev'; // Allow passing backend URL for GitHub pages
    
    const loadingState = document.getElementById('loading-state');
    const paymentDetails = document.getElementById('payment-details');
    const errorState = document.getElementById('error-state');
    const successState = document.getElementById('success-state');
    const errorMsgEl = document.getElementById('error-msg');
    const statusMsgEl = document.getElementById('status-msg');

    if (!order_id || !key_id || !token) {
        loadingState.style.display = 'none';
        errorState.style.display = 'flex';
        errorMsgEl.textContent = 'Invalid payment link. Missing order_id, key_id, or token.';
        return;
    }

    // Populate data
    document.getElementById('display-order-id').textContent = order_id;
    if (amount) {
        document.getElementById('display-amount').textContent = amount;
    } else {
        document.getElementById('display-amount').textContent = "???";
    }

    loadingState.style.display = 'none';
    paymentDetails.style.display = 'flex';

    document.getElementById('pay-btn').addEventListener('click', async () => {
        statusMsgEl.textContent = "Initializing payment...";
        statusMsgEl.className = "status-message";
        
        const options = {
            "key": key_id,
            "order_id": order_id,
            "name": "Webmon AI",
            "description": "AI Credits Refill",
            "theme": {
                "color": "#111111"
            },
            "handler": async function (response) {
                // Payment succeeded, now verify on backend
                statusMsgEl.innerHTML = '<div class="spinner"></div> Verifying payment...';
                
                try {
                    const verifyUrl = api_base ? `${api_base.replace(/\/+$/, '')}/payment/verify` : '/payment/verify';
                    const verifyRes = await fetch(verifyUrl, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${token}`
                        },
                        body: JSON.stringify({
                            razorpay_order_id: response.razorpay_order_id,
                            razorpay_payment_id: response.razorpay_payment_id,
                            razorpay_signature: response.razorpay_signature
                        })
                    });

                    const data = await verifyRes.json();

                    if (verifyRes.ok) {
                        paymentDetails.style.display = 'none';
                        successState.style.display = 'flex';
                    } else {
                        statusMsgEl.textContent = "Verification failed: " + (data.detail || "Unknown error");
                        statusMsgEl.className = "status-message error";
                    }
                } catch (err) {
                    statusMsgEl.textContent = "Verification request failed.";
                    statusMsgEl.className = "status-message error";
                }
            },
            "modal": {
                "ondismiss": function(){
                    statusMsgEl.textContent = "Payment cancelled.";
                    statusMsgEl.className = "status-message error";
                }
            }
        };
        const rzp = new Razorpay(options);
        rzp.on('payment.failed', function (response){
            statusMsgEl.textContent = "Payment failed: " + response.error.description;
            statusMsgEl.className = "status-message error";
        });
        rzp.open();
    });
});
