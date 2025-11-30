/**
 * UVC Backend Integration - Real-time Price Checker
 * Conecta el frontend con el API de Python para precios en tiempo real
 * NOW: Añadido soporte para cache estático `prices-cache.json` para carga instantánea sin backend.
 */

// Configuración del backend
const BACKEND_CONFIG = {
  // Detectar si estamos en GitHub Pages para modo 'static'
  isGithubPages: (typeof window !== 'undefined') ? /github\.io$/.test(window.location.hostname) : false,
  // Base primaria (ej. backend FastAPI) si no es GitHub Pages y existe URL
  apiUrlPrimary: (typeof window !== 'undefined' && window.UVC_BACKEND_URL && window.UVC_BACKEND_URL.trim() !== '' && !/github\.io$/.test(window.location.hostname))
    ? window.UVC_BACKEND_URL.trim()
    : null,
  // Fallback Netlify Functions cuando NO es GitHub Pages
  apiUrlFallback: (typeof window !== 'undefined' && !/github\.io$/.test(window.location.hostname))
    ? window.location.origin + '/.netlify/functions'
    : null,
  endpoints: {
    checkPrices: '/check-prices'
  },
  timeout: 20000,
  retries: 2,
  // En GitHub Pages = static, en Netlify = hybrid
  mode: (typeof window !== 'undefined' && /github\.io$/.test(window.location.hostname)) ? 'static' : 'hybrid'
};

function resolveApiUrl(){
  if (BACKEND_CONFIG.isGithubPages || BACKEND_CONFIG.mode === 'static') return null;
  return BACKEND_CONFIG.apiUrlPrimary || BACKEND_CONFIG.apiUrlFallback;
}

// ==== LECTURA DE CACHE ESTÁTICO ====
async function loadPricesCache(){
  try {
    const resp = await fetch('prices-cache.json', {cache:'no-store'});
    if(!resp.ok) return null;
    return await resp.json();
  } catch(e){
    return null;
  }
}

function findCachedEntry(cache, destination, checkin, checkout){
  if(!cache || !Array.isArray(cache.entries)) return null;
  const destLower = destination.toLowerCase();
  // Match por destino (fechas opcional si no existen en entrada)
  return cache.entries.find(e => e.destination.toLowerCase() === destLower);
}

function formatCacheEntry(entry){
  // Adaptar estructura para UI
  return {
    destination: entry.destination,
    checkin: entry.checkin || '',
    checkout: entry.checkout || '',
    nights: entry.nights || 0,
    timestamp: entry.generated_at || new Date().toISOString(),
    prices: {
      booking: entry.sources?.booking?.price || 0,
      expedia: entry.sources?.expedia?.price || 0,
      hotels: entry.sources?.hotels?.price || 0,
      despegar: entry.sources?.despegar?.price || 0
    },
    hotels: [],
    lowestPrice: entry.metrics?.lowest_price || 0,
    averagePrice: entry.metrics?.average_price || 0
  };
}

/**
 * Verificar si el backend está disponible
 */
async function checkBackendHealth() {
  try {
    const api = resolveApiUrl();
    if(!api) return false;
    const response = await fetch(`${api}/`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    });
    
    if (response.ok) {
      const data = await response.json();
      console.log('✅ Backend conectado:', data);
      return true;
    }
    return false;
  } catch (error) {
    console.warn('⚠️ Backend no disponible, usando datos simulados');
    return false;
  }
}

/**
 * Obtener precios en tiempo real del backend
 */
async function getRealTimePrices(destination, checkin, checkout, guests = 2, rooms = 1) {
  // En GitHub Pages o modo estático, no realizar llamadas dinámicas
  if (BACKEND_CONFIG.isGithubPages || BACKEND_CONFIG.mode === 'static' || !resolveApiUrl()) {
    throw new Error('Modo estático: sin backend disponible');
  }
  try {
    let url = `${resolveApiUrl()}${BACKEND_CONFIG.endpoints.checkPrices}`;
    
    const requestBody = {
      destination,
      checkin,
      checkout,
      guests,
      rooms
    };
    
    console.log('🔍 Buscando precios reales...', requestBody);
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify(requestBody),
      signal: AbortSignal.timeout(BACKEND_CONFIG.timeout)
    });
    
    if (!response.ok) {
      // Intentar fallback si era primary
      if (url.includes(BACKEND_CONFIG.apiUrlPrimary)) {
        console.warn('Primario falló, intentando fallback Netlify Functions');
        url = `${BACKEND_CONFIG.apiUrlFallback}${BACKEND_CONFIG.endpoints.checkPrices}`;
        const fallbackResp = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
          body: JSON.stringify(requestBody),
          signal: AbortSignal.timeout(BACKEND_CONFIG.timeout)
        });
        if (!fallbackResp.ok) {
          throw new Error('Fallback también falló');
        }
        const dataFb = await fallbackResp.json();
        console.log('✅ Precios obtenidos (fallback):', dataFb);
        return dataFb;
      } else {
        const error = await response.json().catch(()=>({detail:'Error desconocido'}));
        throw new Error(error.detail || 'Error al obtener precios');
      }
    }
    
    const data = await response.json();
    console.log('✅ Precios obtenidos:', data);
    
    return data;
    
  } catch (error) {
    console.error('❌ Error al obtener precios reales:', error);
    throw error;
  }
}

/**
 * Formatear datos del backend para el price checker
 */
function formatBackendPrices(backendData) {
  const formatted = {
    destination: backendData.destination,
    checkin: backendData.checkin,
    checkout: backendData.checkout,
    nights: backendData.nights,
    timestamp: backendData.timestamp,
    prices: {
      booking: 0,
      expedia: 0,
      hotels: 0,
      despegar: 0
    },
    hotels: [],
    lowestPrice: backendData.lowest_price,
    averagePrice: backendData.average_price
  };
  
  // Parsear resultados por fuente
  backendData.results.forEach(result => {
    const source = result.source.toLowerCase();
    
    if (source.includes('booking')) {
      formatted.prices.booking = result.price_per_night;
      formatted.hotels.push({
        name: result.hotel_name,
        source: 'Booking.com',
        price: result.price_per_night,
        url: result.url
      });
    } else if (source.includes('expedia')) {
      formatted.prices.expedia = result.price_per_night;
      formatted.hotels.push({
        name: result.hotel_name,
        source: 'Expedia',
        price: result.price_per_night,
        url: result.url
      });
    } else if (source.includes('hotels')) {
      formatted.prices.hotels = result.price_per_night;
      formatted.hotels.push({
        name: result.hotel_name,
        source: 'Hotels.com',
        price: result.price_per_night,
        url: result.url
      });
    }
  });
  
  return formatted;
}

/**
 * Actualizar el price checker panel con datos reales
 */
async function updatePriceCheckerWithRealData(destination, checkin, checkout) {
  const loadingIndicator = document.getElementById('pc-last-updated');
  
  try {
    // Mostrar estado de carga
    if (loadingIndicator) {
      loadingIndicator.innerHTML = '🔄 Buscando precios en tiempo real...';
    }

    // 1. Intentar cache estático primero para respuesta instantánea
    const cache = await loadPricesCache();
    const cachedEntry = findCachedEntry(cache, destination, checkin, checkout);
    let formattedCached = null;
    if(cachedEntry){
      formattedCached = formatCacheEntry(cachedEntry);
      updatePriceCheckerUI(formattedCached);
      if (loadingIndicator) {
        loadingIndicator.innerHTML = '⚡ Precios rápidos (cache) • Actualizando...';
      }
    }
    
    // En modo estático, no intentar backend; ya mostramos cache
    if (BACKEND_CONFIG.isGithubPages || BACKEND_CONFIG.mode === 'static') {
      if (loadingIndicator) {
        loadingIndicator.innerHTML = '⚡ Modo estático (cache)';
      }
      return formattedCached;
    }

    // Si hay backend disponible, intentar precios reales
    if (resolveApiUrl()) {
      const backendData = await getRealTimePrices(destination, checkin, checkout);
      const formattedPrices = formatBackendPrices(backendData);
      updatePriceCheckerUI(formattedPrices);
      if (loadingIndicator) {
        const lastUpdate = new Date(backendData.timestamp);
        const timeStr = lastUpdate.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' });
        loadingIndicator.innerHTML = `✅ Actualizado ${timeStr} • Precios en vivo`;
      }
      return formattedPrices;
    }
    return formattedCached;
    
  } catch (error) {
    console.error('Error actualizando precios:', error);
    if (loadingIndicator) {
      loadingIndicator.innerHTML = BACKEND_CONFIG.isGithubPages ? '⚡ Sólo cache disponible' : '⚠️ Error backend • usando cache';
    }
    return formattedCached;
  }
}

/**
 * Actualizar UI del price checker con precios formateados
 */
function updatePriceCheckerUI(priceData) {
  // Actualizar precios en los elementos del DOM
  const bookingEl = document.querySelector('[data-price-target="booking"]');
  const expediaEl = document.querySelector('[data-price-target="expedia"]');
  const despegarEl = document.querySelector('[data-price-target="despegar"]');
  
  if (bookingEl && priceData.prices.booking > 0) {
    bookingEl.textContent = `$${priceData.prices.booking.toFixed(0)}`;
  }
  
  if (expediaEl && priceData.prices.expedia > 0) {
    expediaEl.textContent = `$${priceData.prices.expedia.toFixed(0)}`;
  }
  
  if (despegarEl && priceData.prices.despegar > 0) {
    despegarEl.textContent = `$${priceData.prices.despegar.toFixed(0)}`;
  }
  
  // Calcular y mostrar precio UVC (con descuento)
  const avgPublicPrice = priceData.averagePrice || 
    (priceData.prices.booking + priceData.prices.expedia) / 2;
  
  const uvcDiscount = 0.35; // 35% descuento
  const uvcPrice = avgPublicPrice * (1 - uvcDiscount);
  
  const uvcEl = document.querySelector('[data-price-target="uvc"]');
  if (uvcEl) {
    uvcEl.textContent = `$${uvcPrice.toFixed(0)}`;
  }
  
  // Actualizar savings
  const savingsEl = document.querySelector('[data-savings-target="0"]');
  if (savingsEl && priceData.lowestPrice) {
    const savings = priceData.lowestPrice - uvcPrice;
    savingsEl.textContent = `Ahorra $${savings.toFixed(0)} por noche`;
  }
}

/**
 * Inicializar conexión con backend al cargar la página
 */
async function initBackendConnection() {
  const isAvailable = await checkBackendHealth();
  
  if (isAvailable) {
    console.log('🚀 Backend listo para price checking en tiempo real');
    
    // Opcional: Precargar precios para destinos populares
    const popularDestinations = ['Cancun', 'Cabo San Lucas', 'Punta Cana'];
    
    // Puedes implementar precarga aquí si lo deseas
  } else {
    console.log('📊 Usando datos simulados para price checker');
  }
}

/**
 * Ejemplo de uso desde el frontend
 */
async function exampleUsage() {
  // Cuando el usuario abre el price checker:
  const checkin = '2025-06-01';
  const checkout = '2025-06-05';
  const destination = 'Cancun';
  
  try {
    const prices = await updatePriceCheckerWithRealData(destination, checkin, checkout);
    
    if (prices) {
      console.log('Precios actualizados:', prices);
      // Los precios ya están en el UI
    }
  } catch (error) {
    console.error('Error:', error);
    // Fallback a datos simulados
  }
}

// Auto-inicializar cuando cargue la página
if (typeof window !== 'undefined') {
  window.addEventListener('DOMContentLoaded', () => {
    initBackendConnection();
    // Botón refrescar sólo cache
    const cacheBtn = document.getElementById('pc-cache-refresh-btn');
    if(cacheBtn){
      cacheBtn.addEventListener('click', () => {
        const destEl = document.querySelector('[data-destination-target]');
        const destination = destEl ? destEl.textContent.trim() : 'Cancun';
        refreshCacheOnly(destination);
      });
    }
  });
}

// Exportar funciones para uso global
if (typeof window !== 'undefined') {
  window.UVCBackend = {
    getRealTimePrices,
    updatePriceCheckerWithRealData,
    checkBackendHealth,
    formatBackendPrices,
    loadPricesCache,
    findCachedEntry,
    config: BACKEND_CONFIG
  };
}

// === Función manual para recargar cache sin backend ===
async function refreshCacheOnly(destination){
  const cacheInfo = document.getElementById('pc-cache-info');
  if(cacheInfo) cacheInfo.textContent = 'Cache: cargando…';
  const cache = await loadPricesCache();
  if(!cache){
    if(cacheInfo) cacheInfo.textContent = 'Cache: no disponible';
    return;
  }
  const entry = findCachedEntry(cache, destination, '', '');
  if(!entry){
    if(cacheInfo) cacheInfo.textContent = 'Cache: sin entrada destino';
    return;
  }
  const formatted = formatCacheEntry(entry);
  updatePriceCheckerUI(formatted);
  if(cacheInfo){
    const gen = cache.generated_at || formatted.timestamp;
    cacheInfo.textContent = 'Cache: ' + gen.replace('T',' ').replace('Z',' UTC');
  }
  const lastUpdatedEl = document.getElementById('pc-last-updated');
  if(lastUpdatedEl){
    lastUpdatedEl.textContent = '⚡ Mostrando datos de cache';
  }
}

// === ADMIN: solicitar precios frescos vía función protegida ===
async function refreshPricesAdmin(token, opts){
  const url = '/.netlify/functions/refresh-prices';
  const body = {
    all: opts?.all || false,
    destination: opts?.destination || undefined,
    checkin: opts?.checkin || undefined,
    checkout: opts?.checkout || undefined
  };
  const resp = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + token
    },
    body: JSON.stringify(body)
  });
  if(!resp.ok){
    const txt = await resp.text();
    throw new Error('Refresh error: ' + txt);
  }
  const data = await resp.json();
  // Tomar primera entrada para UI si aplica
  if(data.entries && data.entries.length){
    const entry = data.entries[0];
    const formatted = formatCacheEntry(entry);
    updatePriceCheckerUI(formatted);
    const lastUpdatedEl = document.getElementById('pc-last-updated');
    if(lastUpdatedEl){
      lastUpdatedEl.textContent = '✅ Refrescado (admin)';
    }
  }
  return data;
}

if (typeof window !== 'undefined' && window.UVCBackend){
  window.UVCBackend.refreshPricesAdmin = refreshPricesAdmin;
}
