from utils import get_eodhd_data, send_telegram_message
from strategy import apply_hedging_logic
import pandas as pd
from datetime import datetime

def format_number(value, decimals=4):
    """Formatta un numero con separatore migliaia e decimali specificati."""
    return f"{value:,.{decimals}f}"

def get_trend_arrow(current, previous):
    """Restituisce freccia trend basata sul confronto."""
    if current > previous:
        return "↗️"
    elif current < previous:
        return "↘️"
    else:
        return "➡️"

def build_telegram_message(last_row, prev_row, df):
    """
    Costruisce un messaggio Telegram formattato professionalmente.
    """
    date_str = last_row.name.strftime('%A, %d %B %Y')
    spot = last_row['Close']
    prev_spot = prev_row['Close']
    sma = last_row['SMA200']
    state = last_row['State']
    action = last_row['Action']
    distance_pct = last_row['Distance_Pct']
    upper_band = last_row['Upper_Band']
    lower_band = last_row['Lower_Band']
    
    # Calcoli
    daily_change = spot - prev_spot
    daily_change_pct = (daily_change / prev_spot) * 100
    trend_arrow = get_trend_arrow(spot, prev_spot)
    change_sign = "+" if daily_change >= 0 else ""
    
    # Header
    header = "━━━━━━━━━━━━━━━━━━━━━━\n"
    header += "🛡️  *KRITERION QUANT*\n"
    header += "      FX Hedging Report\n"
    header += "━━━━━━━━━━━━━━━━━━━━━━"
    
    # Data
    date_section = f"\n📅 *{date_str}*\n"
    
    # Sezione Mercato
    market_section = "\n┌─────────────────────┐\n"
    market_section += "│     📊 *MERCATO*         │\n"
    market_section += "└─────────────────────┘\n\n"
    market_section += f"💶 *EUR/USD Spot:*  `{format_number(spot)}`\n"
    market_section += f"      {trend_arrow} {change_sign}{format_number(daily_change)} ({change_sign}{daily_change_pct:.2f}%)\n\n"
    market_section += f"📈 *SMA 200:*  `{format_number(sma)}`\n"
    market_section += f"📐 *Distanza:*  `{distance_pct:+.2f}%`\n"
    
    # Sezione Bande
    bands_section = "\n┌─────────────────────┐\n"
    bands_section += "│   📏 *BANDE ISTERESI*   │\n"
    bands_section += "└─────────────────────┘\n\n"
    bands_section += f"🟢 Upper (+1%): `{format_number(upper_band)}`\n"
    bands_section += f"🔴 Lower (-1%):  `{format_number(lower_band)}`\n"
    
    # Sezione Stato
    state_section = "\n┌─────────────────────┐\n"
    state_section += "│     📡 *STATO*            │\n"
    state_section += "└─────────────────────┘\n\n"
    
    if state == "BEAR":
        state_section += "🔴 *Regime: BEAR*\n"
        state_section += "🛡️ Status: *HEDGED*\n"
        buffer_to_bull = upper_band - spot
        state_section += f"📍 Buffer → Bull: `{format_number(buffer_to_bull)}`"
    else:
        state_section += "🟢 *Regime: BULL*\n"
        state_section += "💤 Status: *UNHEDGED*\n"
        buffer_to_bear = spot - lower_band
        state_section += f"📍 Buffer → Bear: `{format_number(buffer_to_bear)}`"
    
    # Sezione Azione
    action_section = "\n\n"
    action_section += "═══════════════════════\n"
    
    if action == "OPEN_HEDGE":
        action_section += "🚨 *SEGNALE: ATTIVARE COPERTURA* 🚨\n"
        action_section += "═══════════════════════\n\n"
        action_section += "Eseguire struttura *COLLAR*:\n\n"
        action_section += "   🔹 *BUY PUT* EUR/USD\n"
        action_section += "       Delta: 0.25\n"
        action_section += "       Scopo: Protezione downside\n\n"
        action_section += "   🔸 *SELL CALL* EUR/USD\n"
        action_section += "       Delta: 0.35\n"
        action_section += "       Scopo: Finanziamento premio\n"
    elif action == "CLOSE_HEDGE":
        action_section += "✅ *SEGNALE: RIMUOVERE COPERTURA* ✅\n"
        action_section += "═══════════════════════\n\n"
        action_section += "   📌 Chiudere posizioni opzionali\n"
        action_section += "   📌 Tornare in stato *Unhedged*\n"
    else:
        if state == "BEAR":
            action_section += "🛡️ *NESSUN SEGNALE*\n"
            action_section += "═══════════════════════\n\n"
            action_section += "   ↳ Mantenere copertura attiva\n"
            action_section += "   ↳ Collar in essere\n"
        else:
            action_section += "💤 *NESSUN SEGNALE*\n"
            action_section += "═══════════════════════\n\n"
            action_section += "   ↳ Rimanere unhedged\n"
            action_section += "   ↳ Nessuna azione richiesta\n"
    
    # Footer con statistiche rapide
    hedge_days = len(df[df['State'] == 'BEAR'])
    total_days = len(df)
    hedge_pct = (hedge_days / total_days) * 100
    
    footer = "\n\n━━━━━━━━━━━━━━━━━━━━━━\n"
    footer += f"📊 _Storico: {hedge_pct:.1f}% tempo hedged_\n"
    footer += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Link Dashboard
    dashboard_link = "https://strategiacoperturaeuro-k6pduahqzjxoqtc47alrqr.streamlit.app/"
    footer += f"🔗 [Dashboard Interattiva]({dashboard_link})\n\n"
    footer += "_Kriterion Quant — Finanza Quantitativa Accessibile_"
    
    # Composizione finale
    message = header + date_section + market_section + bands_section + state_section + action_section + footer
    
    return message


def run_daily_check():
    print("=" * 50)
    print("Kriterion Quant - FX Hedging Bot")
    print(f"Avvio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # 1. Scarica Dati
    try:
        print("\n📡 Download dati EODHD...")
        df = get_eodhd_data("EURUSD.FOREX")
        print(f"   ✓ Scaricati {len(df)} record")
    except Exception as e:
        print(f"   ✗ Errore download: {e}")
        error_msg = (
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "⚠️ *KRITERION QUANT*\n"
            "      System Alert\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"❌ Errore download dati EODHD\n\n"
            f"```{str(e)[:200]}```\n\n"
            "_Verificare API key e connessione_"
        )
        send_telegram_message(error_msg)
        return

    # 2. Applica Logica
    print("\n🔧 Elaborazione strategia...")
    processed_df = apply_hedging_logic(df)
    last_row = processed_df.iloc[-1]
    prev_row = processed_df.iloc[-2]
    
    print(f"   ✓ Stato attuale: {last_row['State']}")
    print(f"   ✓ Azione: {last_row['Action']}")
    
    # 3. Costruisci Messaggio
    print("\n📝 Composizione messaggio...")
    message = build_telegram_message(last_row, prev_row, processed_df)
    
    # 4. Invia Telegram
    print("\n📤 Invio Telegram...")
    success = send_telegram_message(message)
    
    if success:
        print("   ✓ Messaggio inviato con successo")
    else:
        print("   ✗ Errore invio messaggio")
    
    print("\n" + "=" * 50)
    print("Esecuzione completata")
    print("=" * 50)


if __name__ == "__main__":
    run_daily_check()
