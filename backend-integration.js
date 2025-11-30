/**
 * UVC Backend Integration - Real-time Price Checker
 * Conecta el frontend con el API de Python para precios en tiempo real
 */

// Configuración del backend
const BACKEND_CONFIG = {
  // Base primaria (Render) y fallback (Netlify Functions)
  apiUrlPrimary: (typeof window !== 'undefined' && window.UVC_BACKEND_URL)
    ? window.UVC_BACKEND_URL
    : 'http://localhost:8000',
  apiUrlFallback: (typeof window !== 'undefined')
    ? window.location.origin + '/.netlify/functions'
    : 'http://localhost:8888/.netlify/functions',
  endpoints: {
    checkPrices: '/check-prices', // en funciones Netlify no usamos /api
  },
  timeout: 20000,
  retries: 2
};

function resolveApiUrl(){
  return BACKEND_CONFIG.apiUrlPrimary || BACKEND_CONFIG.apiUrlFallback;
}

/**
 * Verificar si el backend está disponible
 */
async function checkBackendHealth() {
  try {
    const response = await fetch(`${BACKEND_CONFIG.apiUrl}/`, {
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
    
    // Obtener precios reales
    const backendData = await getRealTimePrices(destination, checkin, checkout);
    const formattedPrices = formatBackendPrices(backendData);
    
    // Actualizar UI con precios reales
    updatePriceCheckerUI(formattedPrices);
    
    // Actualizar timestamp
    if (loadingIndicator) {
      const lastUpdate = new Date(backendData.timestamp);
      const timeStr = lastUpdate.toLocaleTimeString('es-MX', { 
        hour: '2-digit', 
        minute: '2-digit' 
      });
      loadingIndicator.innerHTML = `✅ Actualizado ${timeStr} • Precios en vivo`;
    }
    
    return formattedPrices;
    
  } catch (error) {
    console.error('Error actualizando precios:', error);
    
    if (loadingIndicator) {
      loadingIndicator.innerHTML = '⚠️ Error al obtener precios • Usando datos simulados';
    }
    
    // Fallback a datos simulados
    return null;
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
  });
}

// Exportar funciones para uso global
if (typeof window !== 'undefined') {
  window.UVCBackend = {
    getRealTimePrices,
    updatePriceCheckerWithRealData,
    checkBackendHealth,
    formatBackendPrices,
    config: BACKEND_CONFIG
  };
}
