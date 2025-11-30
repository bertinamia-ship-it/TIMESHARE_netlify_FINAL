exports.handler = async (event) => {
  try {
    const body = event.body ? JSON.parse(event.body) : {};
    const destination = body.destination || 'Cancun';
    const checkin = body.checkin || '2025-06-01';
    const checkout = body.checkout || '2025-06-05';
    const guests = body.guests || 2;
    const rooms = body.rooms || 1;

    const checkinDate = new Date(checkin);
    const checkoutDate = new Date(checkout);
    const nights = Math.max(1, Math.round((checkoutDate - checkinDate) / (1000*60*60*24)) );

    const base = 150;
    const mock = [
      {
        source: 'Booking.com',
        hotel_name: `Dreams Resort - ${destination}`,
        price_per_night: +(base * 1.10).toFixed(2),
        total_price: +(base * 1.10 * nights).toFixed(2),
        currency: 'USD',
        url: `https://booking.com/search?dest=${encodeURIComponent(destination)}`,
        last_updated: new Date().toISOString()
      },
      {
        source: 'Hotels.com',
        hotel_name: `Secrets Resort - ${destination}`,
        price_per_night: +(base * 1.15).toFixed(2),
        total_price: +(base * 1.15 * nights).toFixed(2),
        currency: 'USD',
        url: `https://hotels.com/search?dest=${encodeURIComponent(destination)}`,
        last_updated: new Date().toISOString()
      },
      {
        source: 'Expedia',
        hotel_name: `Breathless Resort - ${destination}`,
        price_per_night: +(base * 0.95).toFixed(2),
        total_price: +(base * 0.95 * nights).toFixed(2),
        currency: 'USD',
        url: `https://expedia.com/search?dest=${encodeURIComponent(destination)}`,
        last_updated: new Date().toISOString()
      }
    ];

    const prices = mock.map(m => m.price_per_night);
    const lowest = Math.min(...prices);
    const avg = prices.reduce((a,b)=>a+b,0)/prices.length;

    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
      body: JSON.stringify({
        destination,
        checkin,
        checkout,
        nights,
        results: mock,
        lowest_price: +lowest.toFixed(2),
        average_price: +avg.toFixed(2),
        timestamp: new Date().toISOString()
      })
    };
  } catch (e) {
    return { statusCode: 500, body: JSON.stringify({ error: 'Function error', detail: e.message }) };
  }
};
