import random
import logging
from typing import Dict, Any

logger = logging.getLogger("merchant_simulator")


class MerchantSimulator:
    """Simulates an authorized merchant's pricing desk API for negotiations.
    All interactions are explicitly stamped with `is_simulated=True`.
    """

    @staticmethod
    def process_offer(
        product_name: str,
        original_price: float,
        proposed_price: float,
        round_number: int,
        max_rounds: int,
    ) -> Dict[str, Any]:
        logger.info(
            f"[Merchant API Simulation] Evaluating offer: ${proposed_price:.2f} "
            f"for '{product_name}' (Original: ${original_price:.2f}, Round: {round_number}/{max_rounds})"
        )

        # Floor margin threshold: Simulated merchant won't sell below 82% of original price
        hard_floor = round(original_price * 0.82, 2)

        # If buyer's proposal is fair (within reasonable discount range >= 90% of price)
        if proposed_price >= round(original_price * 0.90, 2):
            return {
                "status": "ACCEPTED",
                "counter_offer": proposed_price,
                "message": f"Offer of ${proposed_price:.2f} accepted by merchant pricing algorithm.",
                "is_simulated": True,
            }

        # If on final round, merchant offers their absolute bottom line if proposed price is close
        if round_number >= max_rounds:
            final_offer = max(hard_floor, round(original_price * 0.88, 2))
            return {
                "status": "FINAL_OFFER",
                "counter_offer": final_offer,
                "message": f"This is our final concession: ${final_offer:.2f}. We cannot reduce further.",
                "is_simulated": True,
            }

        # Otherwise, merchant counters halfway between buyer offer and original price
        counter = round((original_price + proposed_price) / 2.05, 2)
        counter = max(counter, hard_floor)

        return {
            "status": "COUNTEROFFER",
            "counter_offer": counter,
            "message": f"We cannot do ${proposed_price:.2f}, but we can offer ${counter:.2f} with complimentary priority shipping.",
            "is_simulated": True,
        }


merchant_api = MerchantSimulator()