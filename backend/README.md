# UVC Price Checker Backend

Backend en Python para price checking en tiempo real de hoteles y resorts.

## 🚀 Setup

### 1. Instalar dependencias

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

### 3. Ejecutar servidor de desarrollo

```bash
python main.py
```

O con uvicorn directamente:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

El API estará disponible en: `http://localhost:8000`

## 📡 Endpoints

### Health Check
```
GET /
```

### Comparar Precios
```
POST /api/check-prices
Content-Type: application/json

{
  "destination": "Cancun",
  "checkin": "2025-06-01",
  "checkout": "2025-06-05",
  "guests": 2,
  "rooms": 1
}
```

### Destinos Disponibles
```
GET /api/destinations
```

## 🔧 Desarrollo

### Estructura del proyecto

```
backend/
├── main.py              # FastAPI app principal
├── requirements.txt     # Dependencies
├── .env.example        # Template de environment vars
├── README.md           # Esta documentación
└── scrapers/           # (futuro) Scrapers modulares
    ├── booking.py
    ├── hotels.py
    └── expedia.py
```

### Testing local

```bash
# Ver documentación interactiva
open http://localhost:8000/docs

# Test con curl
curl -X POST http://localhost:8000/api/check-prices \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "Cancun",
    "checkin": "2025-06-01",
    "checkout": "2025-06-05",
    "guests": 2
  }'
```

## 🌐 Deploy

### Opción 1: Render.com (Recomendado - Free tier)

1. Crear cuenta en [Render.com](https://render.com)
2. New > Web Service
3. Conectar este repo
4. Configurar:
   - Build Command: `pip install -r backend/requirements.txt`
   - Start Command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. Deploy!

### Opción 2: Railway.app

1. Crear cuenta en [Railway.app](https://railway.app)
2. New Project > Deploy from GitHub
3. Seleccionar este repo
4. Railway detectará Python automáticamente

### Opción 3: Heroku

```bash
# Crear Procfile en /backend
echo "web: uvicorn main:app --host 0.0.0.0 --port \$PORT" > Procfile

# Deploy
heroku create uvc-price-checker
git subtree push --prefix backend heroku main
```

## 🔗 Integración con Frontend

Una vez deployado, actualiza el frontend para usar tu API:

```javascript
// En index.html, actualizar la función de price checking
async function checkRealPrices(destination, checkin, checkout, guests) {
  const response = await fetch('https://tu-backend.render.com/api/check-prices', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ destination, checkin, checkout, guests })
  });
  
  const data = await response.json();
  return data;
}
```

## ⚠️ Notas Importantes

### Web Scraping Legal
- Los scrapers actuales son básicos y pueden necesitar ajustes
- Considera usar APIs oficiales cuando sea posible:
  - [Booking.com Affiliate API](https://www.booking.com/affiliate-program/v2/index.html)
  - [Expedia Partner Solutions](https://developer.expedia.com/)
  - [Hotels.com API](https://developer.hotels.com/)

### Anti-Bot Protection
Sitios como Booking y Hotels tienen protección anti-bot. Soluciones:

1. **Proxies rotativos**: ScraperAPI, Bright Data
2. **Playwright**: Navegador headless más sofisticado
3. **APIs oficiales**: Mejor opción a largo plazo

### Rate Limiting
- Implementa delays entre requests
- Usa cache para no repetir búsquedas
- Considera Redis para cache distribuido

## 📈 Próximos Pasos

- [ ] Implementar scrapers reales con Playwright
- [ ] Agregar cache con Redis
- [ ] Implementar rate limiting
- [ ] Agregar más comparadores (Kayak, TripAdvisor)
- [ ] Sistema de notificaciones cuando bajen precios
- [ ] Dashboard de analytics

## 🛠️ Tech Stack

- **FastAPI**: Framework web moderno y rápido
- **Pydantic**: Validación de datos
- **BeautifulSoup4**: HTML parsing
- **httpx**: HTTP client asíncrono
- **Selenium/Playwright**: Navegación headless (opcional)
