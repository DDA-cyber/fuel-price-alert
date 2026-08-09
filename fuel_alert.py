import os
import json
import requests

from config import CITY, FUEL_TYPE, PRICE_LIMIT


# ==============================
# CONFIGURARE INTERNĂ
# ==============================

DATA_FILE = "fuel_data.json"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

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
# ISTORIC
# ==============================

def load_previous_price():

    if not os.path.exists(DATA_FILE):
        return None

    try:

        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        return data.get("last_price")

    except Exception:

        return None


def save_current_price(price):

    data = {
        "last_price": price
    }

    with open(DATA_FILE, "w", encoding="utf-8") as file:

        json.dump(
            data,
            file,
            indent=4
        )


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

    previous_price = load_previous_price()

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
            "ℹ️ Nu există încă un "
            "preț anterior."
        )

        save_current_price(
            current_price
        )

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
    # SALVĂM PREȚUL
    # ==============================

    save_current_price(
        current_price
    )


# ==============================
# START
# ==============================

if __name__ == "__main__":
    main()
