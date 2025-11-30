#!/usr/bin/env python3
"""
Generador de cache de precios estáticos para TIMESHARE.

Objetivo: evitar scraping en vivo costoso. Este script simula/consulta
fuentes externas (placeholder) y produce un archivo JSON compacto que
el frontend carga inmediatamente (`prices-cache.json`).

IMPORTANTE:
- No realizar scraping agresivo a Google u otros comparadores: puede violar TOS.
- Para datos reales usar APIs oficiales, afiliados (Booking Partner API),
  o servicios de terceros (SerpAPI, ZenRows, ScrapingBee) con moderación.
- Ejecutar este script en un cron cada X minutos/horas y commitear cambios.

Uso manual:
python scripts/update_prices.py --dest Cancun --checkin 2025-06-01 --checkout 2025-06-05

Para generar todas las entradas definidas en CONFIG_PRESETS:
python scripts/update_prices.py --all
"""
from __future__ import annotations
import json
import random
import argparse
from datetime import datetime
from pathlib import Path

OUTPUT_FILE = Path(__file__).parent.parent / 'prices-cache.json'

# Preconfiguraciones de destinos frecuentes
CONFIG_PRESETS = [
    {
        "destination": "Cancun",
        "checkin": "2025-06-01",
        "checkout": "2025-06-05"
    },
    {
        "destination": "Cabo San Lucas",
        "checkin": "2025-06-10",
        "checkout": "2025-06-14"
    },
    {
        "destination": "Punta Cana",
        "checkin": "2025-07-01",
        "checkout": "2025-07-06"
    }
]

# Márgenes relativos para cada fuente para simular dispersión
SOURCE_VARIATION = {
    "booking": (0.97, 1.05),
    "expedia": (0.95, 1.03),
    "hotels": (0.98, 1.06),
    "despegar": (0.96, 1.04)
}

BASE_PRICE_BY_DEST = {
    "cancun": 180,
    "cabo san lucas": 210,
    "punta cana": 160
}

CURRENCY = "USD"


def compute_nights(checkin: str, checkout: str) -> int:
    ci = datetime.fromisoformat(checkin)
    co = datetime.fromisoformat(checkout)
    return (co - ci).days


def generate_prices_for_destination(dest: str, checkin: str, checkout: str) -> dict:
    base = BASE_PRICE_BY_DEST.get(dest.lower(), 190)
    nights = compute_nights(checkin, checkout)

    sources_block = {}
    collected_prices = []

    for name, (low_factor, high_factor) in SOURCE_VARIATION.items():
        price = round(base * random.uniform(low_factor, high_factor))
        sources_block[name] = {"price": price, "currency": CURRENCY}
        collected_prices.append(price)

    lowest = min(collected_prices)
    avg = round(sum(collected_prices) / len(collected_prices), 2)

    return {
        "destination": dest,
        "checkin": checkin,
        "checkout": checkout,
        "nights": nights,
        "sources": sources_block,
        "metrics": {
            "lowest_price": lowest,
            "average_price": avg
        }
    }


def build_cache(entries: list[dict]) -> dict:
    return {
        "generated_at": datetime.utcnow().isoformat(timespec='seconds') + 'Z',
        "entries": entries
    }


def write_cache(cache: dict):
    with OUTPUT_FILE.open('w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    print(f"✅ Cache actualizado: {OUTPUT_FILE}")


def parse_args():
    p = argparse.ArgumentParser(description="Generar prices-cache.json")
    p.add_argument('--all', action='store_true', help='Generar todas las preconfiguraciones')
    p.add_argument('--dest', type=str, help='Destino único')
    p.add_argument('--checkin', type=str, help='Fecha check-in (YYYY-MM-DD)')
    p.add_argument('--checkout', type=str, help='Fecha check-out (YYYY-MM-DD)')
    return p.parse_args()


def main():
    args = parse_args()

    entries = []
    if args.all:
        for preset in CONFIG_PRESETS:
            entries.append(generate_prices_for_destination(preset['destination'], preset['checkin'], preset['checkout']))
    else:
        if not (args.dest and args.checkin and args.checkout):
            print("⚠️ Debes proporcionar --dest --checkin --checkout o usar --all")
            return
        entries.append(generate_prices_for_destination(args.dest, args.checkin, args.checkout))

    cache = build_cache(entries)
    write_cache(cache)


if __name__ == '__main__':
    main()
