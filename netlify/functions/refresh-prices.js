// Netlify Function: refresh-prices
// Genera precios simulados bajo autenticación de token.
// NOTA: No persiste cambios en el sitio estático; sólo devuelve JSON dinámico.

const PRESETS = [
  { destination: 'Cancun', checkin: '2025-06-01', checkout: '2025-06-05' },
  { destination: 'Cabo San Lucas', checkin: '2025-06-10', checkout: '2025-06-14' },
  { destination: 'Punta Cana', checkin: '2025-07-01', checkout: '2025-07-06' }
];

const SOURCE_VARIATION = {
  booking: [0.97, 1.05],
  expedia: [0.95, 1.03],
  hotels: [0.98, 1.06],
  despegar: [0.96, 1.04]
};

const BASE_PRICE_BY_DEST = {
  'cancun': 180,
  'cabo san lucas': 210,
  'punta cana': 160
};

function nights(checkin, checkout){
  const ci = new Date(checkin);
  const co = new Date(checkout);
  return Math.round((co - ci)/(1000*60*60*24));
}

function generateEntry(dest, checkin, checkout){
  const base = BASE_PRICE_BY_DEST[dest.toLowerCase()] || 190;
  const values = [];
  const sources = {};
  for(const [name, range] of Object.entries(SOURCE_VARIATION)){
    const price = Math.round(base * (range[0] + (Math.random()*(range[1]-range[0]))));
    sources[name] = { price, currency: 'USD' };
    values.push(price);
  }
  const lowest = Math.min(...values);
  const avg = +(values.reduce((a,b)=>a+b,0)/values.length).toFixed(2);
  return {
    destination: dest,
    checkin,
    checkout,
    nights: nights(checkin, checkout),
    sources,
    metrics: {
      lowest_price: lowest,
      average_price: avg
    }
  };
}

exports.handler = async (event) => {
  const auth = event.headers['authorization'] || event.headers['Authorization'];
  const expected = process.env.REFRESH_TOKEN;

  if(!expected){
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'Missing REFRESH_TOKEN env var' })
    };
  }

  if(!auth || !auth.startsWith('Bearer ')){
    return { statusCode: 401, body: JSON.stringify({ error: 'Missing Bearer token' }) };
  }

  const provided = auth.substring('Bearer '.length).trim();
  if(provided !== expected){
    return { statusCode: 403, body: JSON.stringify({ error: 'Invalid token' }) };
  }

  let body; 
  try { body = event.body ? JSON.parse(event.body) : {}; } catch { body = {}; }
  const { destination, checkin, checkout, all = false } = body;

  let entries = [];
  if(all){
    entries = PRESETS.map(p => generateEntry(p.destination, p.checkin, p.checkout));
  } else if(destination && checkin && checkout){
    entries.push(generateEntry(destination, checkin, checkout));
  } else {
    // default: all presets
    entries = PRESETS.map(p => generateEntry(p.destination, p.checkin, p.checkout));
  }

  const payload = {
    generated_at: new Date().toISOString(),
    entries,
    source: 'refresh-function',
    count: entries.length
  };

  return {
    statusCode: 200,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  };
};
