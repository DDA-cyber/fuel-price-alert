import os
import requests

# ==============================
# CONFIGURARE
# ==============================

CITY = "Timisoara"
FUEL_TYPE = "motorina"

# Trimite alerta dacă prețul este egal sau mai mic decât această valoare
PRICE_LIMIT = 9.80

# Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# API PretCarburant.ro
API_URL = "https://pretcarburant.ro/api/v1/preturi"


# ==============================
# FUNCȚII
# ==============================

def get_fuel_price():
    """Obține prețul carburantului pentru Timișoara."""

    response = requests.get(API_URL, timeout=20)
    response.raise_for_status()

    data = response.json()

    if data.get("status") != "ok":
        raise Exception("API-ul PretCarburant.ro a returnat o eroare.")

    for city in data.get("rezultate", []):
        if city.get("oras", "").lower() == CITY.lower():
            price = city.get(FUEL_TYPE)

            if price is None:
                raise Exception(
                    f"Nu am găsit tipul de carburant: {FUEL_TYPE}"
                )

            return price

    raise Exception(f"Nu am găsit orașul {CITY} în răspunsul API.")


def send_telegram(message):
    """Trimite mesajul prin Telegram."""

    if not TELEGRAM_TOKEN:
        raise Exception("Lipsește TELEGRAM_TOKEN.")

    if not CHAT_ID:
        raise Exception("Lipsește CHAT_ID.")

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

    price = get_fuel_price()

    print(f"📍 {CITY}")
    print(f"⛽ {FUEL_TYPE}")
    print(f"💰 Preț: {price:.2f} lei/L")
    print(f"🔔 Prag: {PRICE_LIMIT:.2f} lei/L")

    if price <= PRICE_LIMIT:

        message = (
            "⛽ ALERTĂ CARBURANT\n\n"
            f"📍 {CITY}\n"
            f"⛽ {FUEL_TYPE.capitalize()}\n\n"
            f"💰 Preț actual: {price:.2f} lei/L\n"
            f"🔔 Pragul tău: {PRICE_LIMIT:.2f} lei/L\n\n"
            "✅ Prețul a coborât sub prag!"
        )

        send_telegram(message)

        print("📱 Alerta a fost trimisă pe Telegram.")

    else:
        print("ℹ️ Prețul este peste prag. Nu trimit alertă.")


if __name__ == "__main__":
    main()
