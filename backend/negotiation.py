import uuid
import datetime
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from schemas import NegotiationStartRequest, NegotiationStateResponse, OfferDetail
from ai_agent import ai_agent
from merchant import merchant_api


class NegotiationEngine:
    @staticmethod
    async def start_negotiation(db: AsyncIOMotorDatabase, req: NegotiationStartRequest) -> NegotiationStateResponse:
        # 1. AI Opening Bid
        ai_plan = await ai_agent.generate_opening_offer(
            product_name=req.product_name,
            original_price=req.original_price,
            user_budget=req.user_budget,
        )

        target_price = req.target_price or ai_plan["target_price"]
        opening_offer = ai_plan["opening_offer"]
        neg_id = f"neg_{uuid.uuid4().hex[:10]}"
        now = datetime.datetime.utcnow().isoformat()

        # 2. Simulated Merchant Response
        m_response = merchant_api.process_offer(
            product_name=req.product_name,
            original_price=req.original_price,
            proposed_price=opening_offer,
            round_number=1,
            max_rounds=3,
        )

        status = "ACCEPTED" if m_response["status"] == "ACCEPTED" else "IN_PROGRESS"
        final_price = opening_offer if status == "ACCEPTED" else None
        current_offer = opening_offer if status == "ACCEPTED" else m_response["counter_offer"]

        offers = [
            {
                "id": f"off_{uuid.uuid4().hex[:8]}",
                "round_number": 1,
                "sender": "AI_AGENT",
                "amount": opening_offer,
                "message": ai_plan["message"],
                "timestamp": now,
            },
            {
                "id": f"off_{uuid.uuid4().hex[:8]}",
                "round_number": 1,
                "sender": "MERCHANT",
                "amount": m_response["counter_offer"],
                "message": m_response["message"],
                "timestamp": now,
            },
        ]

        doc = {
            "_id": neg_id,
            "user_id": "default_user",
            "product_id": req.product_id,
            "product_name": req.product_name,
            "merchant_name": req.merchant_name,
            "original_price": req.original_price,
            "target_price": target_price,
            "user_budget": req.user_budget,
            "current_offer": current_offer,
            "final_price": final_price,
            "attempts_count": 1,
            "max_attempts": 3,
            "status": status,
            "is_simulated": True,
            "summary_explanation": ai_plan.get("rationale"),
            "offers": offers,
            "created_at": now,
            "updated_at": now,
        }

        await db.negotiations.insert_one(doc)
        return NegotiationEngine.build_response(doc)

    @staticmethod
    async def process_counteroffer(
        db: AsyncIOMotorDatabase, negotiation_id: str, counter_amount: float, custom_message: str = None
    ) -> NegotiationStateResponse:
        neg = await db.negotiations.find_one({"_id": negotiation_id})
        if not neg:
            raise HTTPException(status_code=404, detail="Negotiation not found.")

        if neg["status"] in ["ACCEPTED", "REJECTED"]:
            raise HTTPException(status_code=400, detail=f"Negotiation already closed with status: {neg['status']}")

        round_num = neg["attempts_count"] + 1
        now = datetime.datetime.utcnow().isoformat()
        msg = (
            custom_message
            or f"DealPilot AI counteroffer for round {round_num}: Offering ${counter_amount:.2f} for instant settlement."
        )

        m_resp = merchant_api.process_offer(
            product_name=neg["product_name"],
            original_price=neg["original_price"],
            proposed_price=counter_amount,
            round_number=round_num,
            max_rounds=neg["max_attempts"],
        )

        merchant_amount = m_resp["counter_offer"]
        new_offers = [
            {
                "id": f"off_{uuid.uuid4().hex[:8]}",
                "round_number": round_num,
                "sender": "AI_AGENT",
                "amount": counter_amount,
                "message": msg,
                "timestamp": now,
            },
            {
                "id": f"off_{uuid.uuid4().hex[:8]}",
                "round_number": round_num,
                "sender": "MERCHANT",
                "amount": merchant_amount,
                "message": m_resp["message"],
                "timestamp": now,
            },
        ]

        status = neg["status"]
        final_price = neg.get("final_price")
        current_offer = merchant_amount

        if m_resp["status"] == "ACCEPTED" or merchant_amount == counter_amount:
            status = "ACCEPTED"
            final_price = counter_amount
            current_offer = counter_amount
        elif round_num >= neg["max_attempts"]:
            if merchant_amount <= neg["user_budget"]:
                status = "ACCEPTED"
                final_price = merchant_amount
            else:
                status = "REJECTED"

        await db.negotiations.update_one(
            {"_id": negotiation_id},
            {
                "$set": {
                    "attempts_count": round_num,
                    "status": status,
                    "final_price": final_price,
                    "current_offer": current_offer,
                    "updated_at": now,
                },
                "$push": {"offers": {"$each": new_offers}},
            },
        )

        updated_doc = await db.negotiations.find_one({"_id": negotiation_id})
        return NegotiationEngine.build_response(updated_doc)

    @staticmethod
    def build_response(neg: dict) -> NegotiationStateResponse:
        final_or_curr = neg.get("final_price") or neg.get("current_offer", 0.0)
        orig = neg.get("original_price", 0.0)
        diff = orig - final_or_curr
        pct = round((diff / orig) * 100, 1) if orig > 0 else 0.0

        offers = [
            OfferDetail(
                id=o["id"],
                round_number=o["round_number"],
                sender=o["sender"],
                amount=o["amount"],
                message=o["message"],
                timestamp=o["timestamp"],
            )
            for o in neg.get("offers", [])
        ]

        return NegotiationStateResponse(
            id=neg["_id"],
            product_id=neg["product_id"],
            product_name=neg["product_name"],
            merchant=neg["merchant_name"],
            original_price=orig,
            target_price=neg.get("target_price", 0.0),
            user_budget=neg.get("user_budget", 0.0),
            current_offer=neg.get("current_offer", 0.0),
            final_price=neg.get("final_price"),
            discount_percentage=max(pct, 0.0),
            attempts_count=neg.get("attempts_count", 1),
            max_attempts=neg.get("max_attempts", 3),
            status=neg.get("status", "IN_PROGRESS"),
            is_simulated=neg.get("is_simulated", True),
            summary_explanation=neg.get("summary_explanation"),
            offers=offers,
        )