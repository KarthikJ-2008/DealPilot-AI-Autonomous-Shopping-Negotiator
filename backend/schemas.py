from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field


# --- Product Search Schemas ---
class ProductSearchRequest(BaseModel):
    product_name: str = Field(..., min_length=2)
    budget: float = Field(..., gt=0)
    brand: Optional[str] = None
    requirements: Optional[List[str]] = []
    preferred_currency: str = "USD"


class ProductItem(BaseModel):
    id: str
    name: str
    brand: Optional[str] = "Generic"
    merchant: str
    price: float
    currency: str = "USD"
    rating: float = 4.0
    image: str = ""
    url: str = ""
    availability: str = "In Stock"
    source: str = "channel3"


class ProductSearchResponse(BaseModel):
    products: List[ProductItem]


# --- Negotiation Schemas ---
class NegotiationStartRequest(BaseModel):
    product_id: str
    product_name: str
    merchant_name: str
    original_price: float
    user_budget: float
    target_price: Optional[float] = None


class OfferDetail(BaseModel):
    id: str
    round_number: int
    sender: str
    amount: float
    message: str
    timestamp: datetime


class NegotiationStateResponse(BaseModel):
    id: str
    product_id: str
    product_name: str
    merchant: str
    original_price: float
    target_price: float
    user_budget: float
    current_offer: float
    final_price: Optional[float]
    discount_percentage: float
    attempts_count: int
    max_attempts: int
    status: str
    is_simulated: bool
    summary_explanation: Optional[str]
    offers: List[OfferDetail] = []


class CounterOfferRequest(BaseModel):
    counter_amount: float = Field(..., gt=0)
    message: Optional[str] = None


# --- Policy Schemas ---
class PolicyModel(BaseModel):
    max_spending_budget: float
    approved_merchants: List[str]
    max_negotiation_attempts: int
    require_approval_all: bool
    approval_threshold: float


class PolicyUpdate(BaseModel):
    max_spending_budget: Optional[float] = None
    approved_merchants: Optional[List[str]] = None
    max_negotiation_attempts: Optional[int] = None
    require_approval_all: Optional[bool] = None
    approval_threshold: Optional[float] = None


class PurchaseApproveRequest(BaseModel):
    negotiation_id: str


class PurchaseApproveResponse(BaseModel):
    approval_id: str
    negotiation_id: str
    approved_amount: float
    status: str
    message: str


# --- Recommendation Schemas ---
class RecommendationResponse(BaseModel):
    negotiation_id: str
    product_name: str
    merchant: str
    original_price: float
    negotiated_price: float
    savings: float
    seller_verified: bool
    budget_compliant: bool
    explanation: str


# --- Payment Schemas ---
class CreateOrderRequest(BaseModel):
    negotiation_id: str


class CreateOrderResponse(BaseModel):
    order_id: str
    status: str
    currency: str
    amount: float
    approval_url: Optional[str] = None


class CaptureOrderRequest(BaseModel):
    negotiation_id: str
    paypal_order_id: str


class CaptureOrderResponse(BaseModel):
    transaction_id: str
    status: str
    captured_amount: float
    savings: float
    capture_id: str


# --- Analytics Schemas ---
class AnalyticsSummary(BaseModel):
    total_money_saved: float
    total_purchases: int
    average_discount: float
    successful_negotiations: int
    failed_negotiations: int
    total_spending: float
    monthly_spending: Dict[str, float]
    savings_over_time: Dict[str, float]
    negotiation_success_rate: float
    merchant_performance: Dict[str, Dict[str, Any]]


class TransactionItem(BaseModel):
    id: str
    negotiation_id: str
    product_name: str
    merchant_name: str
    original_price: float
    final_price: float
    savings: float
    payment_status: str
    date: str