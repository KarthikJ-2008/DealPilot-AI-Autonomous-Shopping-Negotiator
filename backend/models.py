from datetime import datetime, timezone


def get_current_time():
    return datetime.now(timezone.utc)


class User:
    @staticmethod
    def create(user_id, email):
        return { "id": user_id, "email": email, "created_at": get_current_time()}


class Product:
    @staticmethod
    def create(product_id, name, brand=None, category=None,
                description=None, image_url=None, product_url=None,
                rating=0.0):
        return {
            "id": product_id,
            "name": name,
            "brand": brand,
            "category": category,
            "description": description,
            "image_url": image_url,
            "product_url": product_url,
            "rating": rating,
            "created_at": get_current_time()
        }


class Merchant:
    @staticmethod
    def create(merchant_id, name, domain=None,
               is_authorized=True, reliability_score=0.95):
        return {
            "id": merchant_id,
            "name": name,
            "domain": domain,
            "is_authorized": is_authorized,
            "reliability_score": reliability_score,
            "created_at": get_current_time()
        }


class Negotiation:
    @staticmethod
    def create(negotiation_id, user_id, product_id, merchant_id,
               original_price, target_price, user_budget,
               current_offer, max_attempts=3):

        return {
            "id": negotiation_id,
            "user_id": user_id,
            "product_id": product_id,
            "merchant_id": merchant_id,
            "original_price": original_price,
            "target_price": target_price,
            "user_budget": user_budget,
            "current_offer": current_offer,
            "final_price": None,
            "attempts_count": 0,
            "max_attempts": max_attempts,
            "status": "IN_PROGRESS",
            "is_simulated": True,
            "summary_explanation": None,
            "created_at": get_current_time(),
            "updated_at": get_current_time()
        }


class Offer:
    @staticmethod
    def create(offer_id, negotiation_id, round_number,
               sender, amount, message, metadata_info=None):

        return {
            "id": offer_id,
            "negotiation_id": negotiation_id,
            "round_number": round_number,
            "sender": sender,
            "amount": amount,
            "message": message,
            "metadata_info": metadata_info,
            "timestamp": get_current_time()
        }


class Policy:
    @staticmethod
    def create(policy_id, user_id):
        return {
            "id": policy_id,
            "user_id": user_id,
            "max_spending_budget": 500.0,
            "approved_merchants": [],
            "max_negotiation_attempts": 3,
            "require_approval_all": True,
            "approval_threshold": 50.0,
            "updated_at": get_current_time()
        }


class Approval:
    @staticmethod
    def create(approval_id, negotiation_id, user_id,
               approved_amount, signature_hash):

        return {
            "id": approval_id,
            "negotiation_id": negotiation_id,
            "user_id": user_id,
            "approved_amount": approved_amount,
            "is_approved": False,
            "signature_hash": signature_hash,
            "created_at": get_current_time()
        }


class Transaction:
    @staticmethod
    def create(transaction_id, negotiation_id, user_id,
               original_price, final_price):

        return {
            "id": transaction_id,
            "negotiation_id": negotiation_id,
            "user_id": user_id,
            "paypal_order_id": None,
            "paypal_capture_id": None,
            "original_price": original_price,
            "final_price": final_price,
            "money_saved": original_price - final_price,
            "status": "PENDING",
            "payment_provider": "PAYPAL_SANDBOX",
            "raw_payload": None,
            "created_at": get_current_time()
        }
