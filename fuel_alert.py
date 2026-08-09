import os
import json
import requests
from datetime import datetime, timezone

from config import CITY, FUEL_TYPE, PRICE_LIMIT


# ==============================
# CONFIGURARE INTERNĂ
# ==============================

DATA_FILE = "fuel_data.json"

# Numărul maxim de verificări păstrate în istoric
MAX_HISTORY = 500

# Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# API PretCarburant
API_URL = "https://pretcarburant.ro/api/v1/preturi"


# ==============================
# PREȚ CARBURANT
# ==============================

def get_fuel_price():

    response = requests.get(API_URL, timeout=20)
    response.raise_for_status()

    data = response.json()

    if data.get("status") != "ok":
        raise Exception("API-ul a returnat o eroare.")

    for city in data.get("rezultate", []):

        if city.get("oras", "").lower() == CITY.lower():

            price = city.get(FUEL_TYPE)

            if price is None:
                raise Exception(
                    f"Nu am găsit carburantul: {FUEL_TYPE}"
                )

            return float(price)

    raise Exception(
        f"Nu am găsit orașul {CITY}."
    )


# ==============================
# CITIRE DATE
# ==============================

def load_data():

    if not os.path.exists(DATA_FILE):
        return {
            "last_price": None,
            "history": []
        }

    try:

        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        # Compatibilitate cu fișierul vechi
        if "last_price" not in data:
            data["last_price"] = None

        if "history" not in data:
            data["history"] = []

        return data

    except Exception:

        return {
            "last_price": None,
            "history": []
        }


# ==============================
# SALVARE DATE
# ==============================

def save_data(data):

    with open(DATA_FILE, "w", encoding="utf-8") as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )


# ==============================
# ADAUGĂ ÎN ISTORIC
# ==============================

def add_history(data, price):

    timestamp = datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%d %H:%M:%S UTC")

    entry = {
        "timestamp": timestamp,
        "city": CITY,
        "fuel_type": FUEL_TYPE,
        "price": price
    }

    data["history"].append(entry)

    # Păstrăm doar ultimele MAX_HISTORY înregistrări
    data["history"] = data["history"][-MAX_HISTORY:]

    # Actualizăm ultimul preț
    data["last_price"] = price


# ==============================
# TELEGRAM
# ==============================

def send_telegram(message):

    if not TELEGRAM_TOKEN:
        raise Exception(
            "Lipsește TELEGRAM_TOKEN."
        )

    if not CHAT_ID:
        raise Exception(
            "Lipsește CHAT_ID."
        )

    url = (
        f"https://api.telegram.org/bot"
        f"{TELEGRAM_TOKEN}/sendMessage"
    )

    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }

    response = requests.post(
        url,
        data=payload,
        timeout=20
    )

    response.raise_for_status()


# ==============================
# PROGRAM PRINCIPAL
# ==============================

def main():

    print("⛽ Verific prețul carburantului...")

    current_price = get_fuel_price()

    data = load_data()

    previous_price = data.get("last_price")

    print(f"📍 Oraș: {CITY}")
    print(f"⛽ Carburant: {FUEL_TYPE}")
    print(
        f"💰 Preț actual: "
        f"{current_price:.2f} lei/L"
    )
    print(
        f"🔔 Prag: "
        f"{PRICE_LIMIT:.2f} lei/L"
    )

    # ==============================
    # PRIMA RULARE
    # ==============================

    if previous_price is None:

        print(
            "ℹ️ Prima verificare."
        )

        add_history(
            data,
            current_price
        )

        save_data(data)

        if current_price <= PRICE_LIMIT:

            message = (
                "⛽ ALERTĂ PREȚ CARBURANT\n\n"
                f"📍 {CITY}\n"
                f"⛽ {FUEL_TYPE.capitalize()}\n\n"
                f"💰 Preț: "
                f"{current_price:.2f} lei/L\n"
                f"🔔 Prag: "
                f"{PRICE_LIMIT:.2f} lei/L\n\n"
                "✅ Prețul este sub "
                "pragul stabilit!"
            )

            send_telegram(message)

        return

    # ==============================
    # PREȚ NESCHIMBAT
    # ==============================

    if current_price == previous_price:

        print(
            "➡️ Prețul nu s-a schimbat."
        )

        # Chiar dacă prețul nu s-a schimbat,
        # păstrăm verificarea în istoric.
        add_history(
            data,
            current_price
        )

        save_data(data)

        return

    # ==============================
    # PREȚ SCĂZUT
    # ==============================

    if current_price < previous_price:

        difference = (
            previous_price - current_price
        )

        message = (
            "📉 PREȚ CARBURANT "
            "ÎN SCĂDERE\n\n"
            f"📍 {CITY}\n"
            f"⛽ {FUEL_TYPE.capitalize()}\n\n"
            f"💰 Preț nou: "
            f"{current_price:.2f} lei/L\n"
            f"⬇️ Scădere: "
            f"{difference:.2f} lei/L\n"
            f"📊 Preț anterior: "
            f"{previous_price:.2f} lei/L"
        )

        if current_price <= PRICE_LIMIT:

            message += (
                f"\n\n🔔 Prag atins: "
                f"{PRICE_LIMIT:.2f} lei/L"
            )

        send_telegram(message)

        print(
            "📱 Notificare de scădere trimisă."
        )

    # ==============================
    # PREȚ CRESCUT
    # ==============================

    elif current_price > previous_price:

        difference = (
            current_price - previous_price
        )

        message = (
            "📈 PREȚ CARBURANT "
            "ÎN CREȘTERE\n\n"
            f"📍 {CITY}\n"
            f"⛽ {FUEL_TYPE.capitalize()}\n\n"
            f"💰 Preț nou: "
            f"{current_price:.2f} lei/L\n"
            f"⬆️ Creștere: "
            f"{difference:.2f} lei/L\n"
            f"📊 Preț anterior: "
            f"{previous_price:.2f} lei/L"
        )

        send_telegram(message)

        print(
            "📱 Notificare de creștere trimisă."
        )

    # ==============================
    # SALVĂM ÎN ISTORIC
    # ==============================

    add_history(
        data,
        current_price
    )

    save_data(data)

    print(
        f"💾 Istoric actualizat: "
        f"{len(data['history'])} înregistrări."
    )


# ==============================
# START
# ==============================

if __name__ == "__main__":
    main()
