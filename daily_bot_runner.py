from utils import get_eodhd_data, send_telegram_message
from strategy import apply_hedging_logic
import pandas as pd
from datetime import datetime

def run_daily_check():
    print("Avvio controllo giornaliero segnali Kriterion...")
    
    # 1. Scarica Dati
    try:
        df = get_eodhd_data("EURUSD.FOREX")
    except Exception as e:
        print(f"Errore download dati: {e}")
        send_telegram_message(f"⚠️ Kriterion Bot Error: Impossibile scaricare dati EODHD. {e}")
        return

    # 2. Applica Logica
    processed_df = apply_hedging_logic(df)
    last_row = processed_df.iloc[-1]
    
    # 3. Costruisci Messaggio
    date_str = last_row.name.strftime('%Y-%m-%d')
    spot = last_row['Close']
    sma = last_row['SMA200']
    state = last_row['State']
    action = last_row['Action']
    
    # Icone
    icon = "🔴" if state == "BEAR" else "🟢"
    action_text = ""
    
    if action == "OPEN_HEDGE":
        action_text = "\n🚨 **SEGNALE OPERATIVO: ATTIVARE COPERTURA (COLLAR)** 🚨"
    elif action == "CLOSE_HEDGE":
        action_text = "\n✅ **SEGNALE OPERATIVO: RIMUOVERE COPERTURA** ✅"
    else:
        action_text = "\n💤 Nessuna azione richiesta (Hold State)."

    message = (
        f"🛡️ **Kriterion Quant - FX Report** 🛡️\n"
        f"📅 Data: {date_str}\n\n"
        f"💶 Spot EUR/USD: **{spot:.4f}**\n"
        f"📉 SMA 200: {sma:.4f}\n"
        f"📊 Stato Attuale: {icon} **{state}**\n"
        f"{action_text}\n\n"
        f"[Dashboard Link](https://tua-app-streamlit.streamlit.app)"
    )
    
    # 4. Invia Telegram
    success = send_telegram_message(message)
    if success:
        print("Messaggio Telegram inviato con successo.")
    else:
        print("Errore invio messaggio Telegram.")

if __name__ == "__main__":
    run_daily_check()
