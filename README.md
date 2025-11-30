# UVC Sales Pitch App - Real-Time Price Checker

Aplicación web para presentaciones de ventas de Unlimited Vacation Club con price checker en tiempo real.

## 🎯 Características

- ✅ Presentación de 3 columnas (UVC, Worldwide Exchange, Travel Agency)
- ✅ Price checker con comparación en vivo
- ✅ Backend en Python para precios en tiempo real
- ✅ Sistema de analytics de ventas
- ✅ Multiidioma (Español/English)
- ✅ Responsive (iPad Pro, laptops, desktop, móviles)
- ✅ Modo admin con PIN

## 🚀 Quick Start

### Frontend (Website)

La app ya está deployada en Netlify y lista para usar.

### Backend (Price Checker Real-Time)

#### 1. Instalar dependencias

```bash
cd backend
pip install -r requirements.txt
```

#### 2. Ejecutar servidor local

```bash
python main.py
```

El servidor correrá en: `http://localhost:8000`

#### 3. Probar la integración

1. Abre la app en tu navegador
2. Click en el botón "Price Checker" 
3. Click en el botón "Actualizar" (↻)
4. Verás el indicador "🔄 Buscando precios..." mientras busca

## 📱 Cómo Funciona

### Sin backend (modo fallback)
- Click en "Actualizar" → Simula variación de precios (±5%)
- Muestra "Datos simulados" en el timestamp

### Con backend corriendo
- Click en "Actualizar" → Hace request al API Python
- Obtiene precios reales de Booking, Hotels.com, Expedia
- Actualiza el UI con precios en vivo
- Muestra "Precios en vivo" con timestamp real

## 🌐 Deploy del Backend

### Opción 1: Render.com (GRATIS)

1. Sube el código a GitHub
2. Ve a [render.com](https://render.com)
3. New → Web Service
4. Conecta tu repo
5. Configuración:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

6. Una vez deployado, actualiza la URL en `backend-integration.js`:
   ```javascript
   const BACKEND_CONFIG = {
     apiUrl: 'https://tu-backend.onrender.com',  // ← Cambia esto
     // ...
   };
   ```

### Opción 2: Railway.app

Similar a Render, detecta Python automáticamente.

## 📊 Estado Actual del Backend

**Datos simulados (mock)**: El backend actualmente retorna precios simulados porque los scrapers reales requieren:
- APIs oficiales de Booking/Expedia (requieren registro)
- O scrapers con Playwright + proxies (más complejo)

Para implementar precios 100% reales, ver `backend/README.md`.

## 🔧 Configuración

### Variables de entorno (backend)

Copia `.env.example` a `.env` y configura:

```bash
API_HOST=0.0.0.0
API_PORT=8000
ALLOWED_ORIGINS=https://tu-app.netlify.app
```

### PIN de Admin

Edita en `index.html` (línea ~5300):
```javascript
const correctPin = '1234';  // ← Cambia esto
```

## 📱 Uso de la App

1. **Home Screen**: Click "Iniciar presentación"
2. **Price Checker**: Botón en utility bar (esquina superior derecha)
3. **Admin**: Desbloquea con PIN para editar precios
4. **Analytics**: Registra wins/losses, ve métricas

## 🎨 Responsive

- **iPad Pro 10"**: Prioridad, 3 columnas, full-width
- **Laptops/Desktop**: Layout optimizado con max-width
- **Móviles**: Single column, botones grandes, touch-friendly

## 📝 Archivos Principales

```
TIMESHARE_netlify_FINAL-main/
├── index.html                  # App principal (todo en uno)
├── backend-integration.js      # Integración con API Python
├── QUICKSTART.md              # Guía rápida
├── README.md                  # Este archivo
└── backend/
    ├── main.py                # FastAPI server
    ├── requirements.txt       # Dependencies
    └── README.md              # Docs del backend
```

## 🐛 Troubleshooting

### "Error al obtener precios"
- ¿El backend está corriendo? → `python backend/main.py`
- Revisa la consola del navegador (F12) para ver el error exacto

### CORS error
- Verifica que `ALLOWED_ORIGINS` incluya tu dominio
- O usa `allow_origins=["*"]` en desarrollo

### Precios no actualizan
- Click en F12 → Network tab
- Busca el request a `/api/check-prices`
- Revisa la respuesta

## 📞 Soporte

Para issues o preguntas sobre el backend, revisa:
- `backend/README.md` - Documentación completa
- `QUICKSTART.md` - Setup paso a paso
- API docs en vivo: `http://localhost:8000/docs`

## 🎯 Próximos Pasos

- [ ] Implementar scrapers reales con APIs oficiales
- [ ] Agregar cache con Redis
- [ ] Sistema de notificaciones
- [ ] Dashboard de analytics mejorado
- [ ] Export de reportes en PDF

---

**Versión**: 1.0  
**Última actualización**: Noviembre 2025
