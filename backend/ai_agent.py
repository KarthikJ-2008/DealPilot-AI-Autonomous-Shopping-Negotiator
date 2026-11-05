import json
import logging
from typing import Dict, Any, Optional

from config import settings

logger = logging.getLogger("ai_agent")

# Attempt imports for official Google GenAI SDK
try:
    from google import genai
    from google.genai import types
    _HAS_GENAI = True
except ImportError:
    _HAS_GENAI = False


class GeminiNegotiationAgent:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        self.client = None
        if _HAS_GENAI and self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Google GenAI client: {e}")

    async def generate_opening_offer(
        self, product_name: str, original_price: float, user_budget: float
    ) -> Dict[str, Any]:
        """Calculates negotiation targets and opening message using Gemini with strict fallback."""
        prompt = (
            f"You are DealPilot AI, an autonomous shopping negotiator.\n"
            f"Product: {product_name}\n"
            f"Original Listed Price: ${original_price:.2f}\n"
            f"User Maximum Budget: ${user_budget:.2f}\n"
            f"Calculate an aggressive but respectable opening target price (usually 12-18% below original price).\n"
            f"Return ONLY valid JSON matching this schema:\n"
            f"{{\n"
            f'  "target_price": float,\n'
            f'  "opening_offer": float,\n'
            f'  "message": "string",\n'
            f'  "rationale": "string"\n'
            f"}}"
        )

        response_text = await self._call_gemini(prompt)
        if response_text:
            try:
                parsed = json.loads(self._clean_json_str(response_text))
                return parsed
            except Exception as exc:
                logger.warning(f"Error parsing Gemini response: {exc}. Using deterministic logic.")

        # Deterministic Fallback Strategy
        target = round(min(user_budget * 0.90, original_price * 0.85), 2)
        opening = round(target * 0.96, 2)
        return {
            "target_price": target,
            "opening_offer": opening,
            "message": f"Hello! Our verified buyer is interested in purchasing {product_name} today. We can complete checkout immediately at ${opening:.2f}.",
            "rationale": "Target set at 15% discount; initial bid placed slightly lower to allow negotiating room.",
        }

    async def evaluate_counteroffer(
        self,
        product_name: str,
        original_price: float,
        merchant_counter: float,
        user_budget: float,
        target_price: float,
        attempt: int,
        max_attempts: int,
    ) -> Dict[str, Any]:
        """Evaluates whether to accept merchant offer or suggest counter-bid."""
        prompt = (
            f"You are DealPilot AI evaluating a merchant's counteroffer.\n"
            f"Product: {product_name}\n"
            f"Original Price: ${original_price:.2f}\n"
            f"Merchant Offered: ${merchant_counter:.2f}\n"
            f"Target Price: ${target_price:.2f}\n"
            f"User Budget: ${user_budget:.2f}\n"
            f"Current Attempt: {attempt} of {max_attempts}\n"
            f"Decision rules: If merchant counter <= user_budget AND discount >= 8%, consider accepting. Otherwise counter.\n"
            f"Return ONLY valid JSON matching:\n"
            f"{{\n"
            f'  "decision": "ACCEPT" or "COUNTER" or "REJECT",\n'
            f'  "counter_amount": float or null,\n'
            f'  "message": "string explanation or counter offer",\n'
            f'  "explanation": "string"\n'
            f"}}"
        )

        response_text = await self._call_gemini(prompt)
        if response_text:
            try:
                parsed = json.loads(self._clean_json_str(response_text))
                return parsed
            except Exception as exc:
                logger.warning(f"Error parsing Gemini response: {exc}. Using fallback logic.")

        # Deterministic Fallback
        if merchant_counter <= user_budget and (merchant_counter <= original_price * 0.92 or attempt >= max_attempts):
            return {
                "decision": "ACCEPT",
                "counter_amount": merchant_counter,
                "message": f"Deal agreed. We accept the offer of ${merchant_counter:.2f}.",
                "explanation": "Merchant offer satisfies user budget and secures reasonable market discount.",
            }
        else:
            split_diff = round((target_price + merchant_counter) / 2, 2)
            final_bid = min(split_diff, user_budget)
            return {
                "decision": "COUNTER",
                "counter_amount": final_bid,
                "message": f"We appreciate your counteroffer. Can we meet in the middle at ${final_bid:.2f} for instant order placement?",
                "explanation": "Splitting the difference to reach consensus within user budget.",
            }

    async def generate_recommendation_summary(
        self, product_name: str, merchant: str, original_price: float, final_price: float
    ) -> str:
        prompt = (
            f"Generate a concise 1-sentence buyer recommendation explaining why the final negotiated deal on "
            f"{product_name} from {merchant} (from ${original_price:.2f} down to${final_price:.2f}) is optimal."
        )
        resp = await self._call_gemini(prompt)
        if resp:
            return resp.strip()
        savings_pct = round(((original_price - final_price) / original_price) * 100, 1)
        return f"This offer secures a verified {savings_pct}% discount from an authorized vendor with immediate buyer-protection delivery."

    async def _call_gemini(self, prompt: str) -> Optional[str]:
        if not self.client:
            return None
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type="application/json" if "JSON" in prompt else "text/plain",
                ),
            )
            return response.text
        except Exception as exc:
            logger.error(f"Gemini API invocation error: {exc}")
            return None

    def _clean_json_str(self, text: str) -> str:
        clean = text.strip()
        if clean.startswith("```json"):
            clean = clean[7:]
        if clean.startswith("```"):
            clean = clean[3:]
        if clean.endswith("```"):
            clean = clean[:-3]
        return clean.strip()


ai_agent = GeminiNegotiationAgent()