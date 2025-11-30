"""UVC Price Checker Backend API (optimizado con caché y logging)"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import httpx
from typing import List, Optional
import asyncio
import time
from bs4 import BeautifulSoup
from starlette.staticfiles import StaticFiles


class PriceRequest(BaseModel):
    destination: str
    checkin: str
    checkout: str
    guests: int = 2
    rooms: int = 1
    force_refresh: bool = False


class PriceResult(BaseModel):
    source: str
    hotel_name: str
    price_per_night: float
    total_price: float
    currency: str = "USD"
    url: str
    last_updated: str


class PriceComparison(BaseModel):
    destination: str
    checkin: str
    checkout: str
    nights: int
    results: List[PriceResult]
    lowest_price: Optional[float] = None
    average_price: Optional[float] = None
    timestamp: str


app = FastAPI(title="UVC Price Checker API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ CACHÉ ------------------
CACHE_TTL_SECONDS = 600
price_cache: dict = {}

def make_cache_key(r: PriceRequest) -> str:
    return f"{r.destination}|{r.checkin}|{r.checkout}|{r.guests}|{r.rooms}"

def get_cached_response(key: str):
    entry = price_cache.get(key)
    if not entry:
        return None
    if entry["expires"] < time.time():
        price_cache.pop(key, None)
        return None
    return entry["data"]

def set_cache(key: str, data: dict):
    price_cache[key] = {"expires": time.time() + CACHE_TTL_SECONDS, "data": data}

# ------------------ MIDDLEWARE LOGGING ------------------
@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = (time.time() - start) * 1000
    print(f"[REQ] {request.method} {request.url.path} {duration:.1f}ms")
    response.headers["X-Process-Time-ms"] = f"{duration:.1f}"
    return response


async def get_mock_prices(destination: str, checkin: str, checkout: str, guests: int):
    checkin_obj = datetime.strptime(checkin, "%Y-%m-%d")
    checkout_obj = datetime.strptime(checkout, "%Y-%m-%d")
    nights = (checkout_obj - checkin_obj).days
    base_price = 150
    return [
        PriceResult(
            source="Booking.com",
            hotel_name=f"Dreams Resort - {destination}",
            price_per_night=base_price * 1.1,
            total_price=base_price * 1.1 * nights,
            url=f"https://booking.com/search?dest={destination}",
            last_updated=datetime.now().isoformat()
        ),
        PriceResult(
            source="Hotels.com",
            hotel_name=f"Secrets Resort - {destination}",
            price_per_night=base_price * 1.15,
            total_price=base_price * 1.15 * nights,
            url=f"https://hotels.com/search?dest={destination}",
            last_updated=datetime.now().isoformat()
        ),
        PriceResult(
            source="Expedia",
            hotel_name=f"Breathless Resort - {destination}",
            price_per_night=base_price * 0.95,
            total_price=base_price * 0.95 * nights,
            url=f"https://expedia.com/search?dest={destination}",
            last_updated=datetime.now().isoformat()
        ),
    ]


@app.get("/status")
async def status():
    return {
        "status": "online",
        "service": "UVC Price Checker API",
        "version": "1.1.0",
        "cache_entries": len(price_cache),
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/check-prices", response_model=PriceComparison)
async def check_prices(request: PriceRequest):
    try:
        checkin_obj = datetime.strptime(request.checkin, "%Y-%m-%d")
        checkout_obj = datetime.strptime(request.checkout, "%Y-%m-%d")
        if checkin_obj >= checkout_obj:
            raise HTTPException(status_code=400, detail="Check-out debe ser después de check-in")
        if checkin_obj < datetime.now():
            raise HTTPException(status_code=400, detail="Check-in debe ser fecha futura")
        nights = (checkout_obj - checkin_obj).days

        cache_key = make_cache_key(request)
        if not request.force_refresh:
            cached = get_cached_response(cache_key)
            if cached:
                return PriceComparison(**cached)

        results_sets = await asyncio.gather(
            get_mock_prices(request.destination, request.checkin, request.checkout, request.guests),
            return_exceptions=True
        )
        all_results: List[PriceResult] = []
        for rs in results_sets:
            if isinstance(rs, list):
                all_results.extend(rs)

        prices = [r.price_per_night for r in all_results if r.price_per_night > 0]
        lowest_price = min(prices) if prices else None
        average_price = sum(prices) / len(prices) if prices else None

        response_obj = PriceComparison(
            destination=request.destination,
            checkin=request.checkin,
            checkout=request.checkout,
            nights=nights,
            results=all_results,
            lowest_price=round(lowest_price, 2) if lowest_price else None,
            average_price=round(average_price, 2) if average_price else None,
            timestamp=datetime.now().isoformat()
        )
        set_cache(cache_key, response_obj.model_dump())
        return response_obj
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Formato de fecha inválido: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener precios: {str(e)}")


@app.get("/api/destinations")
async def get_destinations():
    return {
        "destinations": [
            {"code": "CUN", "name": "Cancún", "country": "Mexico"},
            {"code": "PUJ", "name": "Punta Cana", "country": "Dominican Republic"},
            {"code": "CZM", "name": "Cozumel", "country": "Mexico"},
            {"code": "PVR", "name": "Puerto Vallarta", "country": "Mexico"},
            {"code": "CSL", "name": "Cabo San Lucas", "country": "Mexico"},
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Mount static frontend (serve index.html) from TIMESHARE folder
# This lets us host frontend and backend on the same Railway app
try:
    app.mount("/", StaticFiles(directory="TIMESHARE_netlify_FINAL", html=True), name="static")
except Exception as e:
    print(f"[WARN] Static mount failed: {e}")
