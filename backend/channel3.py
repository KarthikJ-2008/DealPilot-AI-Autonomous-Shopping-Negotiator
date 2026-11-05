import logging
import httpx
from typing import List, Dict, Any

from config import settings
from schemas import ProductItem, ProductSearchRequest

logger = logging.getLogger("channel3")

# Category-aware product imagery
CATEGORY_IMAGES = {
    "phone": [
        "https://images.unsplash.com/photo-1592750475338-74b7b21085ab?w=600&q=80",
        "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=600&q=80",
        "https://images.unsplash.com/photo-1580910051074-3eb694886505?w=600&q=80",
        "https://images.unsplash.com/photo-1565849904461-04a58ad377e0?w=600&q=80",
    ],
    "laptop": [
        "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=600&q=80",
        "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=600&q=80",
        "https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?w=600&q=80",
        "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=600&q=80",
    ],
    "watch": [
        "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&q=80",
        "https://images.unsplash.com/photo-1579586337278-3befd40fd17a?w=600&q=80",
        "https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=600&q=80",
        "https://images.unsplash.com/photo-1546868871-7041f2a55e12?w=600&q=80",
    ],
    "camera": [
        "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=600&q=80",
        "https://images.unsplash.com/photo-1502920917128-1aa500764cbd?w=600&q=80",
        "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=600&q=80",
        "https://images.unsplash.com/photo-1617005082133-548c4dd27f35?w=600&q=80",
    ],
    "earbuds": [
        "https://images.unsplash.com/photo-1600294037681-c80b4cb5b434?w=600&q=80",
        "https://images.unsplash.com/photo-1590658268033-6bf12165a8df?w=600&q=80",
        "https://images.unsplash.com/photo-1572536147248-ac59a8abfa4b?w=600&q=80",
        "https://images.unsplash.com/photo-1606220588913-b3aacb4d2f46?w=600&q=80",
    ],
    "headphone": [
        "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&q=80",
        "https://images.unsplash.com/photo-1583394838336-acd977736f90?w=600&q=80",
        "https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=600&q=80",
        "https://images.unsplash.com/photo-1484704849700-f032a568e944?w=600&q=80",
    ],
    "tablet": [
        "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?w=600&q=80",
        "https://images.unsplash.com/photo-1561154464-82e9adf32764?w=600&q=80",
        "https://images.unsplash.com/photo-1585790050230-5dd28404ccb9?w=600&q=80",
        "https://images.unsplash.com/photo-1512499617640-c74ae3a79d37?w=600&q=80",
    ],
    "monitor": [
        "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=600&q=80",
        "https://images.unsplash.com/photo-1585792180666-f7347c490ee2?w=600&q=80",
        "https://images.unsplash.com/photo-1547658719-da2b51169166?w=600&q=80",
        "https://images.unsplash.com/photo-1551645120-d70bfe84c826?w=600&q=80",
    ],
    "keyboard": [
        "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=600&q=80",
        "https://images.unsplash.com/photo-1618384887929-16ec33fab9ef?w=600&q=80",
        "https://images.unsplash.com/photo-1595225476474-87563907a212?w=600&q=80",
        "https://images.unsplash.com/photo-1561152820-34078fbc37c7?w=600&q=80",
    ],
    "mouse": [
        "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=600&q=80",
        "https://images.unsplash.com/photo-1626218174358-7769486c4b79?w=600&q=80",
        "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=600&q=80",
        "https://images.unsplash.com/photo-1605774330484-7d4560037f54?w=600&q=80",
    ],
    "shoes": [
        "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600&q=80",
        "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?w=600&q=80",
        "https://images.unsplash.com/photo-1560769629-975ec94e6a86?w=600&q=80",
        "https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?w=600&q=80",
    ],
    "gaming": [
        "https://images.unsplash.com/photo-1606813907291-d86efa9b94db?w=600&q=80",
        "https://images.unsplash.com/photo-1600080972464-8e5f35f63d08?w=600&q=80",
        "https://images.unsplash.com/photo-1621259182978-fbf93132d53d?w=600&q=80",
        "https://images.unsplash.com/photo-1578301978693-85fa9c0320b9?w=600&q=80",
    ],
}


def get_image_for_query(product_name: str, brand: str = "", index: int = 0) -> str:
    q = f"{product_name} {brand}".lower()
    if any(k in q for k in ["iphone", "phone", "galaxy", "pixel", "mobile", "smartphone"]):
        category = "phone"
    elif any(k in q for k in ["macbook", "laptop", "thinkpad", "notebook", "computer"]):
        category = "laptop"
    elif any(k in q for k in ["watch", "smartwatch", "rolex", "band"]):
        category = "watch"
    elif any(k in q for k in ["camera", "dslr", "sony alpha", "canon", "nikon", "lens"]):
        category = "camera"
    elif any(k in q for k in ["airpod", "earbud", "buds", "in-ear", "tws"]):
        category = "earbuds"
    elif any(k in q for k in ["ipad", "tablet", "surface pro"]):
        category = "tablet"
    elif any(k in q for k in ["monitor", "display", "screen", "ultrasharp", "tv"]):
        category = "monitor"
    elif any(k in q for k in ["keyboard", "keychron", "mechanical"]):
        category = "keyboard"
    elif any(k in q for k in ["mouse", "mx master", "trackpad", "logitech mx"]):
        category = "mouse"
    elif any(k in q for k in ["shoe", "sneaker", "nike", "adidas", "jordan"]):
        category = "shoes"
    elif any(k in q for k in ["ps5", "playstation", "xbox", "nintendo", "gaming", "console"]):
        category = "gaming"
    else:
        category = "headphone"

    images = CATEGORY_IMAGES[category]
    return images[index % len(images)]


class Channel3Client:
    def __init__(self):
        self.api_key = settings.CHANNEL3_API_KEY
        self.base_url = settings.CHANNEL3_BASE_URL.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}" if self.api_key else "",
            "Content-Type": "application/json",
            "User-Agent": "DealPilot-AI-Agent/1.0",
        }

    async def search_products(self, query: ProductSearchRequest) -> List[ProductItem]:
        # If API key is not configured or in sandbox mock mode, return real category-matched mock catalogue
        if not self.api_key or self.api_key == "mock" or "channel3" not in settings.CHANNEL3_BASE_URL:
            logger.info("Channel3 credentials in simulation mode. Providing category-matched dynamic catalogue.")
            return self._get_mock_products(query)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/search",
                    headers=self.headers,
                    json={
                        "query": query.product_name,
                        "brand": query.brand,
                        "max_price": query.budget,
                        "currency": query.preferred_currency,
                        "tags": query.requirements,
                    },
                )
                if response.status_code == 200:
                    data = response.json()
                    return self._normalize_channel3_response(data, query)
                else:
                    logger.warning(f"Channel3 returned {response.status_code}. Using dynamic mock fallback.")
                    return self._get_mock_products(query)
        except Exception as exc:
            logger.error(f"Error communicating with Channel3: {str(exc)}. Using dynamic fallback.")
            return self._get_mock_products(query)

    def _normalize_channel3_response(self, raw_data: Dict[str, Any], query: ProductSearchRequest) -> List[ProductItem]:
        results: List[ProductItem] = []
        raw_items = raw_data.get("items", raw_data.get("results", []))
        for idx, item in enumerate(raw_items):
            img = item.get("image_url") or item.get("image")
            if not img or "placeholder" in img:
                img = get_image_for_query(query.product_name, query.brand or "", idx)

            results.append(
                ProductItem(
                    id=str(item.get("id", f"c3_prod_{idx}")),
                    name=item.get("title", item.get("name", query.product_name)),
                    brand=item.get("brand", query.brand or "Authorized Brand"),
                    merchant=item.get("merchant_name", item.get("store", "Verified Merchant")),
                    price=float(item.get("price", query.budget)),
                    currency=item.get("currency", "USD"),
                    rating=float(item.get("rating", 4.7)),
                    image=img,
                    url=item.get("product_url", "https://example.com/product"),
                    availability="In Stock",
                    source="channel3",
                )
            )
        return results

    def _get_mock_products(self, query: ProductSearchRequest) -> List[ProductItem]:
        base_name = query.product_name.strip()
        b = query.budget
        brand = query.brand or "Verified Brand"

        p1 = round(b * 0.96, 2)
        p2 = round(b * 1.05, 2)
        p3 = round(b * 0.90, 2)
        p4 = round(b * 1.12, 2)

        return [
            ProductItem(
                id="c3_prod_1",
                name=f"{base_name} - Authorized Pro Edition",
                brand=brand,
                merchant="ElectroDirect Official",
                price=p1,
                currency=query.preferred_currency,
                rating=4.9,
                image=get_image_for_query(base_name, brand, 0),
                url="https://example.com/item/1",
                availability="In Stock (2-Day Express)",
                source="channel3",
            ),
            ProductItem(
                id="c3_prod_2",
                name=f"{base_name} - Retail Box Sealed",
                brand=brand,
                merchant="SoundHut Superstore",
                price=p2,
                currency=query.preferred_currency,
                rating=4.7,
                image=get_image_for_query(base_name, brand, 1),
                url="https://example.com/item/2",
                availability="In Stock (Standard 3-Day)",
                source="channel3",
            ),
            ProductItem(
                id="c3_prod_3",
                name=f"{base_name} - Certified Refurbished",
                brand=brand,
                merchant="BestBuy Certified",
                price=p3,
                currency=query.preferred_currency,
                rating=4.8,
                image=get_image_for_query(base_name, brand, 2),
                url="https://example.com/item/3",
                availability="Store Pickup Ready",
                source="channel3",
            ),
            ProductItem(
                id="c3_prod_4",
                name=f"{base_name} - Creator Bundle Kit",
                brand=brand,
                merchant="B&H Photo Video",
                price=p4,
                currency=query.preferred_currency,
                rating=4.6,
                image=get_image_for_query(base_name, brand, 3),
                url="https://example.com/item/4",
                availability="In Stock",
                source="channel3",
            ),
        ]


channel3_client = Channel3Client()
