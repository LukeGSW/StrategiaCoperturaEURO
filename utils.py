import os
import requests
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

# Funzione per recuperare i secrets in modo ibrido (Streamlit o OS Environment)
def get_secret(key):
    # Prova a prendere da Streamlit Secrets (se siamo in app)
    try:
        return st.secrets[key]
    except (FileNotFoundError, AttributeError, KeyError):
        # Altrimenti prova da variabili d'ambiente (se siamo in GitHub Actions)
        return os.environ.get(key)

def get_eodhd_data(ticker="EURUSD.FOREX", days=2000):
    """
    Scarica i dati storici da EODHD.
    ticker: es. 'EURUSD.FOREX'
    """
    api_key = get_secret("EODHD_API_KEY")
    if not api_key:
        raise ValueError("EODHD_API_KEY non trovata nei secrets.")

    base_url = f"https://eodhd.com/api/eod/{ticker}"
    params = {
        "api_token": api_key,
        "fmt": "json",
        "order": "a", # ascendente
        "from": (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    }

    response = requests.get(base_url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        # EODHD restituisce 'close', 'adjusted_close', etc.
        # Nel forex close e adjusted sono solitamente uguali, usiamo adjusted per sicurezza
        df = df.rename(columns={"adjusted_close": "Close", "close": "Close_Raw"})
        return df[['Close', 'high', 'low', 'open', 'volume']]
    else:
        raise ConnectionError(f"Errore API EODHD: {response.status_code} - {response.text}")

def send_telegram_message(message):
    """
    Invia un messaggio al bot Telegram configurato.
    """
    bot_token = get_secret("TELEGRAM_BOT_TOKEN")
    chat_id = get_secret("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        print("Telegram Token o Chat ID mancanti.")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, json=payload)
        return response.status_code == 200
    except Exception as e:
        print(f"Errore invio Telegram: {e}")
        return False
