# 🚀 Quick Start Guide - Backend Python

## Setup rápido (5 minutos)

### 1. Instalar Python y dependencias

```bash
# Navegar al directorio backend
cd /Users/alexis/Desktop/Alexis/TIMESHARE_netlify_FINAL-main/backend

# Crear entorno virtual (recomendado)
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate  # En Mac/Linux

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Ejecutar el servidor

```bash
# Desde /backend
python main.py
```

Deberías ver:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### 3. Probar que funciona

Abre en tu navegador:
- http://localhost:8000 → Verás mensaje "online"
- http://localhost:8000/docs → Documentación interactiva

### 4. Test con tu frontend

1. Abre otro terminal
2. Navega a tu proyecto: `cd /Users/alexis/Desktop/Alexis/TIMESHARE_netlify_FINAL-main`
3. Inicia un servidor local:
   ```bash
   python3 -m http.server 3000
   ```
4. Abre http://localhost:3000
5. Abre la consola del navegador (F12)
6. Prueba el API:
   ```javascript
   // En la consola del navegador
   await UVCBackend.getRealTimePrices('Cancun', '2025-06-01', '2025-06-05')
   ```

## 📱 Integrar con tu app actual

### Opción 1: Script tag (más fácil)

Agrega al `<head>` de tu `index.html`:

```html
<!-- Backend Integration -->
<script src="backend-integration.js"></script>
```

Luego en tu código JavaScript existente, puedes llamar:

```javascript
// Cuando abran el price checker
async function openPriceChecker() {
  const destination = 'Cancun';
  const checkin = '2025-06-01';
  const checkout = '2025-06-05';
  
  // Esto actualizará automáticamente el UI
  await window.UVCBackend.updatePriceCheckerWithRealData(
    destination, 
    checkin, 
    checkout
  );
  
  // Abrir el panel
  document.getElementById('price-checker-panel').classList.add('active');
}
```

### Opción 2: Inline (sin archivo separado)

Copia el contenido de `backend-integration.js` directamente en tu `<script>` existente en `index.html`.

## 🌐 Deploy del Backend

### Render.com (GRATIS - Recomendado)

1. Sube tu código a GitHub
2. Ve a https://render.com
3. "New" → "Web Service"
4. Conecta tu repo
5. Configuración:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Click "Create Web Service"

Recibirás una URL como: `https://uvc-backend-xyz.onrender.com`

### Actualizar frontend con URL de producción

En `backend-integration.js` línea 10:

```javascript
const BACKEND_CONFIG = {
  apiUrl: 'https://uvc-backend-xyz.onrender.com',  // ← Tu URL de Render
  // ...
};
```

## ⚡ Testing rápido

### Test 1: Backend funciona
```bash
curl http://localhost:8000/
```

Respuesta esperada:
```json
{"status":"online","service":"UVC Price Checker API","version":"1.0.0"}
```

### Test 2: Buscar precios
```bash
curl -X POST http://localhost:8000/api/check-prices \
  -H "Content-Type: application/json" \
  -d '{
    "destination": "Cancun",
    "checkin": "2025-06-01",
    "checkout": "2025-06-05",
    "guests": 2
  }'
```

### Test 3: Desde navegador

Abre la consola (F12) en tu app y ejecuta:

```javascript
fetch('http://localhost:8000/api/check-prices', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    destination: 'Cancun',
    checkin: '2025-06-01',
    checkout: '2025-06-05',
    guests: 2
  })
})
.then(r => r.json())
.then(data => console.log('✅ Precios:', data))
```

## 🐛 Troubleshooting

### Error: CORS
Si ves error de CORS, verifica que tu backend tenga:
```python
allow_origins=["*"]  # En main.py línea 17
```

### Error: Connection refused
- ¿El backend está corriendo? → `python main.py`
- ¿Está en puerto 8000? → http://localhost:8000

### Precios no aparecen
1. Abre consola del navegador (F12)
2. Ve a tab "Network"
3. Busca el request a `/api/check-prices`
4. Revisa la respuesta

## 📊 Datos actuales

Por ahora el backend devuelve **datos simulados** (mock data) porque los scrapers reales necesitan:
1. Proxies para evitar bloqueos
2. APIs oficiales de Booking/Expedia
3. Playwright para navegación headless

### Próximos pasos para precios reales:

1. **Opción fácil**: Usar APIs oficiales
   - Booking Affiliate API
   - Expedia Partner API
   - Requieren registro pero son estables

2. **Opción scraping**: Implementar con Playwright
   - Más complejo pero flexible
   - Requiere proxies rotativos ($)
   - Ver `backend/README.md` para detalles

## 🎯 Resultado final

Una vez integrado:
- ✅ Click en "Price Checker" → Fetch automático de precios
- ✅ Indicador "🔄 Buscando precios..."
- ✅ Actualización en vivo del UI
- ✅ Timestamp real
- ✅ Fallback a datos simulados si falla

¿Listo para probarlo? 🚀
