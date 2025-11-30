# Configuración de API Keys para Precios Reales

## ¿Por qué necesitamos API keys?

El price checker ahora obtiene precios **reales** de Booking.com, Expedia y Hotels.com/Despegar usando sus APIs oficiales. Esto garantiza que los precios coincidan exactamente con lo que ves en Google Travel.

## Paso 1: Crear cuenta en RapidAPI

1. Ve a https://rapidapi.com/
2. Crea una cuenta gratis
3. Verifica tu email

## Paso 2: Suscribirte a las APIs

### Booking.com API
1. Busca "Booking.com API" en RapidAPI
2. Selecciona el plan **GRATUITO** (permite hasta 500 requests/mes)
3. Click en "Subscribe to Test"

### Hotels.com Provider API
1. Busca "Hotels.com Provider" en RapidAPI
2. Selecciona el plan **GRATUITO** (permite hasta 500 requests/mes)
3. Click en "Subscribe to Test"

## Paso 3: Obtener tu API Key

1. Ve a tu Dashboard en RapidAPI
2. Copia tu **X-RapidAPI-Key** (aparece en la sección "Security")

## Paso 4: Configurar en Railway

1. Abre tu proyecto en Railway
2. Ve a la pestaña "Variables"
3. Agrega una nueva variable:
   - **Name**: `RAPIDAPI_KEY`
   - **Value**: tu API key de RapidAPI
4. Click en "Add" y luego "Deploy"

## Paso 5: Verificar que funciona

1. Espera a que Railway despliegue (1-2 minutos)
2. Abre el price checker en tu sitio
3. Click en "Actualizar Precios"
4. Los precios ahora deben coincidir con Google Travel

## Notas

- **Plan Gratuito**: 500 requests/mes por API es suficiente para demos
- **Precios reales**: Los precios se actualizan cada vez que das click en "Actualizar"
- **Caché**: Los precios se cachean 10 minutos para no gastar requests
- **Fallback**: Si las APIs fallan, se usan precios de ejemplo (mock)

## Troubleshooting

### "Precios no coinciden"
- Verifica que agregaste `RAPIDAPI_KEY` en Railway
- Verifica que te suscribiste a ambas APIs en RapidAPI
- Revisa los logs de Railway para ver errores

### "Rate limit exceeded"
- Alcanzaste el límite de 500 requests/mes
- Espera al siguiente mes o actualiza a plan pagado

### "API key invalid"
- Verifica que copiaste la key completa
- Verifica que no hay espacios al inicio/final
