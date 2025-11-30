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


HOTEL_GOOGLE_TRAVEL_URLS = {
    "Secrets Puerto Los Cabos": "https://www.google.com/travel/search?q=secrets%20puerto%20los%20cabos",
    "Zoetry Los Cabos": "https://www.google.com/travel/search?q=zoetry%20los%20cabos"
}

async def scrape_google_travel_prices(hotel_name: str, checkin: str, checkout: str, guests: int):
    """Scrappea precios de Google Travel para hoteles específicos"""
    if hotel_name not in HOTEL_GOOGLE_TRAVEL_URLS:
        return []
    
    base_url = HOTEL_GOOGLE_TRAVEL_URLS[hotel_name]
    checkin_obj = datetime.strptime(checkin, "%Y-%m-%d")
    checkout_obj = datetime.strptime(checkout, "%Y-%m-%d")
    nights = (checkout_obj - checkin_obj).days
    
    # Construir URL con fechas y parámetros
    # Google Travel usa formato: &checkin_date=YYYY-MM-DD&checkout_date=YYYY-MM-DD
    search_url = f"{base_url}&checkin_date={checkin}&checkout_date={checkout}&adults={guests}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(search_url, headers=headers)
            if response.status_code != 200:
                print(f"[ERROR] Google Travel status {response.status_code} para {hotel_name}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Buscar precios en la página (Google Travel muestra comparador)
            # Típicamente: Booking.com, Expedia, Hotels.com, etc.
            results = []
            
            # Intenta extraer precios de cards de booking sites
            price_elements = soup.find_all(['div', 'span'], class_=lambda x: x and ('price' in x.lower() or 'rate' in x.lower()))
            
            # Backup: extraer números que parezcan precios (USD $XXX)
            import re
            price_pattern = re.compile(r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)')
            all_prices = price_pattern.findall(response.text)
            
            if all_prices:
                # Convertir strings a floats
                clean_prices = [float(p.replace(',', '')) for p in all_prices if float(p.replace(',', '')) > 50]
                
                # Asumir que encontramos precios de distintas agencias
                sources = ["Booking.com", "Expedia", "Hotels.com", "Despegar"]
                for i, price in enumerate(clean_prices[:4]):  # Top 4 precios
                    source = sources[i] if i < len(sources) else f"Agencia {i+1}"
                    price_per_night = price / nights if nights > 0 else price
                    
                    results.append(PriceResult(
                        source=source,
                        hotel_name=hotel_name,
                        price_per_night=round(price_per_night, 2),
                        total_price=round(price, 2),
                        url=search_url,
                        last_updated=datetime.now().isoformat()
                    ))
            
            return results
            
    except Exception as e:
        print(f"[ERROR] Scraping Google Travel para {hotel_name}: {str(e)}")
        return []


async def get_mock_prices(destination: str, checkin: str, checkout: str, guests: int):
    """Fallback si scraping falla"""
    checkin_obj = datetime.strptime(checkin, "%Y-%m-%d")
    checkout_obj = datetime.strptime(checkout, "%Y-%m-%d")
    nights = (checkout_obj - checkin_obj).days
    base_price = 250
    return [
        PriceResult(
            source="Booking.com",
            hotel_name=f"{destination}",
            price_per_night=base_price * 1.1,
            total_price=base_price * 1.1 * nights,
            url=f"https://booking.com/search?dest={destination}",
            last_updated=datetime.now().isoformat()
        ),
        PriceResult(
            source="Expedia",
            hotel_name=f"{destination}",
            price_per_night=base_price * 0.95,
            total_price=base_price * 0.95 * nights,
            url=f"https://expedia.com/search?dest={destination}",
            last_updated=datetime.now().isoformat()
        ),
        PriceResult(
            source="Despegar",
            hotel_name=f"{destination}",
            price_per_night=base_price * 1.05,
            total_price=base_price * 1.05 * nights,
            url=f"https://despegar.com/search?dest={destination}",
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

        # Intentar scraping de Google Travel para hoteles específicos
        scraping_tasks = []
        
        # Mapeo de destination a hotel name
        hotel_mapping = {
            "Secrets Puerto Los Cabos": "Secrets Puerto Los Cabos",
            "Zoetry Los Cabos": "Zoetry Los Cabos",
            "secrets": "Secrets Puerto Los Cabos",
            "zoetry": "Zoetry Los Cabos"
        }
        
        # Detectar qué hotel buscar
        dest_lower = request.destination.lower()
        target_hotel = None
        for key, hotel in hotel_mapping.items():
            if key.lower() in dest_lower:
                target_hotel = hotel
                break
        
        if target_hotel:
            scraping_tasks.append(
                scrape_google_travel_prices(target_hotel, request.checkin, request.checkout, request.guests)
            )
        else:
            # Fallback: mock prices
            scraping_tasks.append(
                get_mock_prices(request.destination, request.checkin, request.checkout, request.guests)
            )
        
        results_sets = await asyncio.gather(*scraping_tasks, return_exceptions=True)
        all_results: List[PriceResult] = []
        for rs in results_sets:
            if isinstance(rs, list):
                all_results.extend(rs)
        
        # Si no obtuvimos resultados, usar mock
        if not all_results:
            mock_results = await get_mock_prices(request.destination, request.checkin, request.checkout, request.guests)
            all_results.extend(mock_results)

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
