import base64
import logging
import uuid
import datetime
import httpx
from typing import Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase

from config import settings
from policy import policy_engine

logger = logging.getLogger("paypal")


class PayPalSandboxClient:
    def __init__(self):
        self.client_id = settings.PAYPAL_CLIENT_ID
        self.client_secret = settings.PAYPAL_CLIENT_SECRET
        self.base_url = settings.PAYPAL_BASE_URL.rstrip("/")

    async def get_access_token(self) -> str:
        if not self.client_secret or "placeholder" in self.client_secret:
            return "mock_paypal_access_token"

        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_auth = base64.b64encode(credentials.encode()).decode("utf-8")

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{self.base_url}/v1/oauth2/token",
                data={"grant_type": "client_credentials"},
                headers={
                    "Authorization": f"Basic {encoded_auth}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
            if resp.status_code == 200:
                return resp.json()["access_token"]
            raise RuntimeError("Failed to authenticate with PayPal Sandbox.")

    async def create_order(self, db: AsyncIOMotorDatabase, negotiation_id: str) -> Dict[str, Any]:
        neg = await db.negotiations.find_one({"_id": negotiation_id})
        if not neg:
            raise ValueError("Negotiation not found.")

        # Guard: Check User Approval
        if not neg.get("approval", {}).get("is_approved"):
            raise ValueError("Payment Blocked: User approval is required before initiating PayPal payment.")

        # Guard: Check Policy Compliance
        is_valid, reason = await policy_engine.validate_purchase(db, neg)
        if not is_valid:
            raise ValueError(f"Payment Blocked by Guardrail: {reason}")

        payable_amount = neg.get("final_price") or neg.get("current_offer")
        token = await self.get_access_token()

        if token == "mock_paypal_access_token":
            mock_id = f"MOCK_PP_ORDER_{uuid.uuid4().hex[:12].upper()}"
            return {
                "order_id": mock_id,
                "status": "CREATED",
                "currency": "USD",
                "amount": payable_amount,
                "approval_url": f"https://www.sandbox.paypal.com/checkoutnow?token={mock_id}",
            }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "PayPal-Request-Id": f"req_{uuid.uuid4().hex}",
        }

        order_payload = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "reference_id": neg["_id"],
                    "description": f"DealPilot AI purchase: {neg['product_name']}",
                    "amount": {"currency_code": "USD", "value": f"{payable_amount:.2f}"},
                }
            ],
            "application_context": {
                "brand_name": "DealPilot AI",
                "user_action": "PAY_NOW",
                "shipping_preference": "NO_SHIPPING",
            },
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(f"{self.base_url}/v2/checkout/orders", headers=headers, json=order_payload)
            if resp.status_code in [200, 201]:
                data = resp.json()
                approval_url = next((l["href"] for l in data.get("links", []) if l.get("rel") == "approve"), None)
                return {
                    "order_id": data["id"],
                    "status": data["status"],
                    "currency": "USD",
                    "amount": payable_amount,
                    "approval_url": approval_url,
                }
            raise RuntimeError(f"PayPal create-order failed: {resp.text}")

    async def capture_order(
        self, db: AsyncIOMotorDatabase, negotiation_id: str, paypal_order_id: str
    ) -> Dict[str, Any]:
        neg = await db.negotiations.find_one({"_id": negotiation_id})
        if not neg:
            raise ValueError("Negotiation not found.")

        # Guard against duplicate captures
        existing_tx = await db.transactions.find_one({"paypal_order_id": paypal_order_id})
        if existing_tx and existing_tx.get("status") == "COMPLETED":
            return {
                "transaction_id": existing_tx["_id"],
                "status": existing_tx["status"],
                "captured_amount": existing_tx["final_price"],
                "savings": existing_tx["money_saved"],
                "capture_id": existing_tx["paypal_capture_id"],
            }

        payable_amount = neg.get("final_price") or neg.get("current_offer")
        token = await self.get_access_token()

        capture_id = f"CAP_{uuid.uuid4().hex[:10].upper()}"
        status = "COMPLETED"

        if token != "mock_paypal_access_token":
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
                "PayPal-Request-Id": f"cap_{uuid.uuid4().hex}",
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.base_url}/v2/checkout/orders/{paypal_order_id}/capture", headers=headers
                )
                if resp.status_code in [200, 201]:
                    raw_res = resp.json()
                    status = raw_res.get("status", "COMPLETED")
                    try:
                        capture_id = raw_res["purchase_units"][0]["payments"]["captures"][0]["id"]
                    except Exception:
                        capture_id = paypal_order_id
                else:
                    raise RuntimeError(f"PayPal capture failed: {resp.text}")

        tx_id = f"tx_{uuid.uuid4().hex[:10]}"
        savings = max(round(neg["original_price"] - payable_amount, 2), 0.0)
        now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M")

        tx_doc = {
            "_id": tx_id,
            "negotiation_id": neg["_id"],
            "user_id": neg["user_id"],
            "product_name": neg["product_name"],
            "merchant_name": neg["merchant_name"],
            "paypal_order_id": paypal_order_id,
            "paypal_capture_id": capture_id,
            "original_price": neg["original_price"],
            "final_price": payable_amount,
            "money_saved": savings,
            "status": "COMPLETED" if status in ["COMPLETED", "APPROVED"] else "FAILED",
            "date": now,
        }

        await db.transactions.insert_one(tx_doc)
        await db.negotiations.update_one({"_id": neg["_id"]}, {"$set": {"status": "COMPLETED"}})

        return {
            "transaction_id": tx_id,
            "status": tx_doc["status"],
            "captured_amount": payable_amount,
            "savings": savings,
            "capture_id": capture_id,
        }


paypal_client = PayPalSandboxClient()