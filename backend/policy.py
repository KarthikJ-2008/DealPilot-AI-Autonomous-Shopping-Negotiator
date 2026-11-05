import hashlib
import uuid
import datetime
from typing import Tuple, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase


class FinancialPolicyEngine:
    @staticmethod
    async def get_or_create_policy(db: AsyncIOMotorDatabase, user_id: str = "default_user") -> Dict[str, Any]:
        policy = await db.policies.find_one({"_id": user_id})
        if not policy:
            default_policy = {
                "_id": user_id,
                "user_id": user_id,
                "max_spending_budget": 300.0,
                "approved_merchants": [
                    "AudioTech Direct",
                    "GadgetWorld US",
                    "ElectroPrime Outlet",
                    "SoundWave Central",
                    "Store A",
                    "Verified Merchant",
                ],
                "max_negotiation_attempts": 3,
                "require_approval_all": True,
                "approval_threshold": 50.0,
                "updated_at": datetime.datetime.utcnow().isoformat(),
            }
            await db.policies.insert_one(default_policy)
            return default_policy
        return policy

    @classmethod
    async def validate_purchase(cls, db: AsyncIOMotorDatabase, negotiation: Dict[str, Any]) -> Tuple[bool, str]:
        user_id = negotiation.get("user_id", "default_user")
        policy = await cls.get_or_create_policy(db, user_id)
        final_price = negotiation.get("final_price") or negotiation.get("current_offer", 0.0)

        # Rule 1: Max Spending Budget Limit
        if final_price > policy.get("max_spending_budget", 300.0):
            return (
                False,
                f"Policy Violation: Price ${final_price:.2f} exceeds strict spending ceiling of ${policy.get('max_spending_budget'):.2f}.",
            )

        # Rule 2: User Request Budget Limit
        if final_price > negotiation.get("user_budget", 0.0):
            return (
                False,
                f"Policy Violation: Price ${final_price:.2f} exceeds user's allocated budget of ${negotiation.get('user_budget'):.2f}.",
            )

        # Rule 3: Approved Merchant Whitelist
        merchant_name = negotiation.get("merchant_name", "")
        approved_list = policy.get("approved_merchants", [])
        if approved_list and merchant_name not in approved_list:
            return (
                False,
                f"Policy Violation: Merchant '{merchant_name}' is not in the approved merchant whitelist.",
            )

        return True, "Compliance checks passed."

    @classmethod
    async def register_user_approval(
        cls, db: AsyncIOMotorDatabase, negotiation_id: str, user_id: str = "default_user"
    ) -> Dict[str, Any]:
        negotiation = await db.negotiations.find_one({"_id": negotiation_id})
        if not negotiation:
            raise ValueError("Negotiation record not found.")

        is_valid, reason = await cls.validate_purchase(db, negotiation)
        if not is_valid:
            raise ValueError(f"Approval rejected: {reason}")

        if negotiation.get("approval", {}).get("is_approved"):
            return negotiation["approval"]

        target_amount = negotiation.get("final_price") or negotiation.get("current_offer", 0.0)
        timestamp = datetime.datetime.utcnow().isoformat()
        audit_payload = f"{negotiation_id}:{user_id}:{target_amount}:{timestamp}"
        sig_hash = hashlib.sha256(audit_payload.encode()).hexdigest()

        approval_data = {
            "id": f"app_{uuid.uuid4().hex[:10]}",
            "negotiation_id": negotiation_id,
            "user_id": user_id,
            "approved_amount": target_amount,
            "is_approved": True,
            "signature_hash": sig_hash,
            "created_at": timestamp,
        }

        await db.negotiations.update_one(
            {"_id": negotiation_id},
            {"$set": {"approval": approval_data}}
        )
        return approval_data


policy_engine = FinancialPolicyEngine()