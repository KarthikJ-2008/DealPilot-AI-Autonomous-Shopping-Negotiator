import os
import logging
from typing import List
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorDatabase

from config import settings
from database import get_db
import schemas
from channel3 import channel3_client
from negotiation import NegotiationEngine
from policy import policy_engine
from paypal import paypal_client
from analytics import AnalyticsService
from ai_agent import ai_agent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("dealpilot")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Autonomous Shopping Negotiator Backend API (MongoDB)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "service": "DealPilot AI Engine",
        "database": "MongoDB",
        "gemini_active": bool(settings.GEMINI_API_KEY),
        "channel3_active": bool(settings.CHANNEL3_API_KEY),
        "paypal_client_id": settings.PAYPAL_CLIENT_ID,
    }


@app.post("/api/products/search", response_model=schemas.ProductSearchResponse, tags=["Products"])
async def search_products(req: schemas.ProductSearchRequest):
    products = await channel3_client.search_products(req)
    return schemas.ProductSearchResponse(products=products)


@app.post("/api/negotiations/start", response_model=schemas.NegotiationStateResponse, tags=["Negotiations"])
async def start_negotiation(req: schemas.NegotiationStartRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    return await NegotiationEngine.start_negotiation(db, req)


@app.get("/api/negotiations/{neg_id}", response_model=schemas.NegotiationStateResponse, tags=["Negotiations"])
async def get_negotiation(neg_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    neg = await db.negotiations.find_one({"_id": neg_id})
    if not neg:
        raise HTTPException(status_code=404, detail="Negotiation not found")
    return NegotiationEngine.build_response(neg)


@app.get("/api/negotiations/{neg_id}/offers", response_model=List[schemas.OfferDetail], tags=["Negotiations"])
async def get_negotiation_offers(neg_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    neg = await db.negotiations.find_one({"_id": neg_id})
    if not neg:
        raise HTTPException(status_code=404, detail="Negotiation not found")
    return [
        schemas.OfferDetail(
            id=o["id"],
            round_number=o["round_number"],
            sender=o["sender"],
            amount=o["amount"],
            message=o["message"],
            timestamp=o["timestamp"],
        )
        for o in neg.get("offers", [])
    ]


@app.post("/api/negotiations/{neg_id}/counteroffer", response_model=schemas.NegotiationStateResponse, tags=["Negotiations"])
async def counteroffer(neg_id: str, body: schemas.CounterOfferRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    return await NegotiationEngine.process_counteroffer(db, neg_id, body.counter_amount, body.message)


@app.get("/api/recommendations/{neg_id}", response_model=schemas.RecommendationResponse, tags=["Recommendations"])
async def get_recommendation(neg_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    neg = await db.negotiations.find_one({"_id": neg_id})
    if not neg:
        raise HTTPException(status_code=404, detail="Negotiation not found")

    is_compliant, _ = await policy_engine.validate_purchase(db, neg)
    payable = neg.get("final_price") or neg.get("current_offer", 0.0)

    explanation = await ai_agent.generate_recommendation_summary(
        product_name=neg["product_name"],
        merchant=neg["merchant_name"],
        original_price=neg["original_price"],
        final_price=payable,
    )

    return schemas.RecommendationResponse(
        negotiation_id=neg["_id"],
        product_name=neg["product_name"],
        merchant=neg["merchant_name"],
        original_price=neg["original_price"],
        negotiated_price=payable,
        savings=round(neg["original_price"] - payable, 2),
        seller_verified=True,
        budget_compliant=is_compliant,
        explanation=explanation,
    )


@app.get("/api/policies", response_model=schemas.PolicyModel, tags=["Policies"])
async def get_policies(db: AsyncIOMotorDatabase = Depends(get_db)):
    p = await policy_engine.get_or_create_policy(db)
    return schemas.PolicyModel(
        max_spending_budget=p["max_spending_budget"],
        approved_merchants=p.get("approved_merchants", []),
        max_negotiation_attempts=p["max_negotiation_attempts"],
        require_approval_all=p["require_approval_all"],
        approval_threshold=p["approval_threshold"],
    )


@app.put("/api/policies", response_model=schemas.PolicyModel, tags=["Policies"])
async def update_policies(update: schemas.PolicyUpdate, db: AsyncIOMotorDatabase = Depends(get_db)):
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    await db.policies.update_one({"_id": "default_user"}, {"$set": update_data}, upsert=True)
    p = await policy_engine.get_or_create_policy(db)
    return schemas.PolicyModel(
        max_spending_budget=p["max_spending_budget"],
        approved_merchants=p.get("approved_merchants", []),
        max_negotiation_attempts=p["max_negotiation_attempts"],
        require_approval_all=p["require_approval_all"],
        approval_threshold=p["approval_threshold"],
    )


@app.post("/api/purchases/approve", response_model=schemas.PurchaseApproveResponse, tags=["Policies"])
async def approve_purchase(req: schemas.PurchaseApproveRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        apprv = await policy_engine.register_user_approval(db, req.negotiation_id)
        return schemas.PurchaseApproveResponse(
            approval_id=apprv["id"],
            negotiation_id=apprv["negotiation_id"],
            approved_amount=apprv["approved_amount"],
            status="APPROVED",
            message="Purchase cryptographically approved and locked for checkout.",
        )
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))


@app.post("/api/payments/create-order", response_model=schemas.CreateOrderResponse, tags=["Payments"])
async def paypal_create_order(req: schemas.CreateOrderRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        data = await paypal_client.create_order(db, req.negotiation_id)
        return schemas.CreateOrderResponse(**data)
    except ValueError as v_err:
        raise HTTPException(status_code=403, detail=str(v_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Order creation error: {str(exc)}")


@app.post("/api/payments/capture-order", response_model=schemas.CaptureOrderResponse, tags=["Payments"])
async def paypal_capture_order(req: schemas.CaptureOrderRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        res = await paypal_client.capture_order(db, req.negotiation_id, req.paypal_order_id)
        return schemas.CaptureOrderResponse(**res)
    except ValueError as v_err:
        raise HTTPException(status_code=400, detail=str(v_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Order capture error: {str(exc)}")


@app.get("/api/analytics", response_model=schemas.AnalyticsSummary, tags=["Analytics"])
async def get_analytics(db: AsyncIOMotorDatabase = Depends(get_db)):
    return await AnalyticsService.get_summary(db)


@app.get("/api/transactions", response_model=List[schemas.TransactionItem], tags=["Analytics"])
async def get_transactions(db: AsyncIOMotorDatabase = Depends(get_db)):
    return await AnalyticsService.get_transactions(db)


# Static hosting for frontend
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/app", StaticFiles(directory=frontend_dir, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)