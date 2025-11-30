"""
UVC Price Checker Backend API
Real-time hotel price comparison scraper
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
import httpx
from typing import List, Optional
import asyncio
from bs4 import BeautifulSoup

app = FastAPI(title="UVC Price Checker API", version="1.0.0")

# CORS para permitir requests desde Netlify
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica tu dominio de Netlify
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PriceRequest(BaseModel):
    """Request model para búsqueda de precios"""
    destination: str
    checkin: str  # formato: YYYY-MM-DD
    checkout: str  # formato: YYYY-MM-DD
    guests: int = 2
    rooms: int = 1


class PriceResult(BaseModel):
    """Modelo de respuesta con precios encontrados"""
    source: str
    hotel_name: str
    price_per_night: float
    total_price: float
    currency: str = "USD"
    url: str
    last_updated: str


class PriceComparison(BaseModel):
    """Comparación completa de precios"""
    destination: str
    checkin: str
    checkout: str
    nights: int
    results: List[PriceResult]
    lowest_price: Optional[float] = None
    average_price: Optional[float] = None
    timestamp: str


async def scrape_booking_com(destination: str, checkin: str, checkout: str, guests: int = 2):
    """
    Scraper para Booking.com
    Nota: Booking tiene protección anti-bot, considera usar APIs oficiales o proxies
    """
    try:
        # Formato de URL de Booking.com
        checkin_obj = datetime.strptime(checkin, "%Y-%m-%d")
        checkout_obj = datetime.strptime(checkout, "%Y-%m-%d")
        
        url = (
            f"https://www.booking.com/searchresults.html"
            f"?ss={destination}"
            f"&checkin={checkin_obj.strftime('%Y-%m-%d')}"
            f"&checkout={checkout_obj.strftime('%Y-%m-%d')}"
            f"&group_adults={guests}"
            f"&no_rooms=1"
        )
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers, follow_redirects=True)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Parsear resultados (estos selectores pueden cambiar)
                results = []
                
                # Buscar cards de hoteles
                hotel_cards = soup.select('[data-testid="property-card"]')[:5]
                
                for card in hotel_cards:
                    try:
                        name_elem = card.select_one('[data-testid="title"]')
                        price_elem = card.select_one('[data-testid="price-and-discounted-price"]')
                        
                        if name_elem and price_elem:
                            hotel_name = name_elem.text.strip()
                            price_text = price_elem.text.strip()
                            
                            # Extraer precio numérico
                            price = float(''.join(filter(str.isdigit, price_text.replace(',', ''))))
                            
                            nights = (checkout_obj - checkin_obj).days
                            price_per_night = price / nights if nights > 0 else price
                            
                            results.append(PriceResult(
                                source="Booking.com",
                                hotel_name=hotel_name,
                                price_per_night=round(price_per_night, 2),
                                total_price=round(price, 2),
                                url=url,
                                last_updated=datetime.now().isoformat()
                            ))
                    except Exception as e:
                        continue
                
                return results
    except Exception as e:
        print(f"Error scraping Booking.com: {e}")
        return []


async def scrape_hotels_com(destination: str, checkin: str, checkout: str, guests: int = 2):
    """
    Scraper para Hotels.com
    Similar approach con headers y parsing
    """
    try:
        checkin_obj = datetime.strptime(checkin, "%Y-%m-%d")
        checkout_obj = datetime.strptime(checkout, "%Y-%m-%d")
        
        url = (
            f"https://www.hotels.com/Hotel-Search"
            f"?destination={destination}"
            f"&startDate={checkin_obj.strftime('%Y-%m-%d')}"
            f"&endDate={checkout_obj.strftime('%Y-%m-%d')}"
            f"&adults={guests}"
        )
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers, follow_redirects=True)
            
            if response.status_code == 200:
                # Implementar parsing similar a Booking
                # Por ahora retornamos mock data para testing
                nights = (checkout_obj - checkin_obj).days
                
                return [
                    PriceResult(
                        source="Hotels.com",
                        hotel_name=f"Hotel in {destination}",
                        price_per_night=185.00,
                        total_price=185.00 * nights,
                        url=url,
                        last_updated=datetime.now().isoformat()
                    )
                ]
    except Exception as e:
        print(f"Error scraping Hotels.com: {e}")
        return []


async def get_mock_prices(destination: str, checkin: str, checkout: str, guests: int):
    """
    Datos mock para testing mientras configuramos los scrapers reales
    """
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


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "UVC Price Checker API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/check-prices", response_model=PriceComparison)
async def check_prices(request: PriceRequest):
    """
    Endpoint principal para comparar precios
    
    Example request:
    {
        "destination": "Cancun",
        "checkin": "2025-06-01",
        "checkout": "2025-06-05",
        "guests": 2,
        "rooms": 1
    }
    """
    try:
        # Validar fechas
        checkin_obj = datetime.strptime(request.checkin, "%Y-%m-%d")
        checkout_obj = datetime.strptime(request.checkout, "%Y-%m-%d")
        
        if checkin_obj >= checkout_obj:
            raise HTTPException(status_code=400, detail="Check-out debe ser después de check-in")
        
        if checkin_obj < datetime.now():
            raise HTTPException(status_code=400, detail="Check-in debe ser fecha futura")
        
        nights = (checkout_obj - checkin_obj).days
        
        # Ejecutar scrapers en paralelo
        results = await asyncio.gather(
            get_mock_prices(request.destination, request.checkin, request.checkout, request.guests),
            # scrape_booking_com(request.destination, request.checkin, request.checkout, request.guests),
            # scrape_hotels_com(request.destination, request.checkin, request.checkout, request.guests),
            return_exceptions=True
        )
        
        # Combinar resultados
        all_results = []
        for result_set in results:
            if isinstance(result_set, list):
                all_results.extend(result_set)
        
        # Calcular estadísticas
        prices = [r.price_per_night for r in all_results if r.price_per_night > 0]
        lowest_price = min(prices) if prices else None
        average_price = sum(prices) / len(prices) if prices else None
        
        return PriceComparison(
            destination=request.destination,
            checkin=request.checkin,
            checkout=request.checkout,
            nights=nights,
            results=all_results,
            lowest_price=round(lowest_price, 2) if lowest_price else None,
            average_price=round(average_price, 2) if average_price else None,
            timestamp=datetime.now().isoformat()
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Formato de fecha inválido: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener precios: {str(e)}")


@app.get("/api/destinations")
async def get_destinations():
    """Lista de destinos disponibles"""
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
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
