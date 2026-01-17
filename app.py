import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime  # <--- CORREZIONE: Import aggiunto qui
from utils import get_eodhd_data
from strategy import apply_hedging_logic

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Kriterion Quant | FX Hedging",
    page_icon="🛡️",
    layout="wide"
)

# --- HEADER E LOGICA ---
st.title("🛡️ Kriterion Quant - FX Hedging Dashboard")
st.markdown("### Copertura Dinamica EUR/USD (SMA 200 + Hysteresis)")

# Caricamento Dati (Cache per evitare chiamate API continue)
@st.cache_data(ttl=3600) # Aggiorna ogni ora
def load_data():
    raw_df = get_eodhd_data("EURUSD.FOREX")
    processed_df = apply_hedging_logic(raw_df)
    return processed_df

try:
    df = load_data()
    
    # Ultimi dati
    last_row = df.iloc[-1]
    prev_row = df.iloc[-2]
    
    # --- METRICHE PRINCIPALI ---
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("EUR/USD Spot", f"{last_row['Close']:.4f}", f"{(last_row['Close'] - prev_row['Close']):.4f}")
    
    with col2:
        st.metric("SMA 200", f"{last_row['SMA200']:.4f}")
        
    with col3:
        state_color = "red" if last_row['State'] == "BEAR" else "green"
        status_icon = "🔴 HEDGED" if last_row['State'] == "BEAR" else "🟢 UNHEDGED"
        st.markdown(f"**Stato Copertura:**")
        st.markdown(f"<h3 style='color: {state_color}; margin-top: -15px;'>{status_icon}</h3>", unsafe_allow_html=True)
        
    with col4:
        # Distanza dal cambio stato
        if last_row['State'] == 'BULL':
            dist = last_row['Close'] - last_row['Lower_Band']
            msg = f"Buffer to Bear: {dist:.4f}"
        else:
            dist = last_row['Upper_Band'] - last_row['Close']
            msg = f"Buffer to Bull: {dist:.4f}"
        st.metric("Distanza Banda Attivazione", f"{last_row['Distance_Pct']:.2f}%", msg)

    st.markdown("---")

    # --- GRAFICO INTERATTIVO (PLOTLY) ---
    st.subheader("Analisi Storica e Segnali")
    
    fig = go.Figure()

    # Candele (o Linea) Prezzo
    fig.add_trace(go.Scatter(
        x=df.index, y=df['Close'],
        mode='lines', name='EURUSD Spot',
        line=dict(color='black', width=1)
    ))

    # SMA 200
    fig.add_trace(go.Scatter(
        x=df.index, y=df['SMA200'],
        mode='lines', name='SMA 200',
        line=dict(color='orange', width=2, dash='dash')
    ))
    
    # Aggiungiamo Marker per i cambi di stato (Action)
    hedge_entries = df[df['Action'] == 'OPEN_HEDGE']
    hedge_exits = df[df['Action'] == 'CLOSE_HEDGE']
    
    fig.add_trace(go.Scatter(
        x=hedge_entries.index, y=hedge_entries['Close'],
        mode='markers', name='Entry Hedge (Sell Put/Buy Call)',
        marker=dict(color='red', size=10, symbol='triangle-down')
    ))
    
    fig.add_trace(go.Scatter(
        x=hedge_exits.index, y=hedge_exits['Close'],
        mode='markers', name='Exit Hedge (Unhedged)',
        marker=dict(color='green', size=10, symbol='triangle-up')
    ))

    fig.update_layout(
        height=600,
        xaxis_title="Data",
        yaxis_title="Prezzo",
        template="plotly_white",
        hovermode="x unified"
    )
    
    # CORREZIONE WARNING:
    # Se vuoi eliminare il warning rosso nel log, usa width="stretch" (per le versioni nuove di Streamlit)
    # Altrimenti use_container_width=True funziona ancora ma genera l'avviso.
    # Qui usiamo la versione compatibile col warning:
    st.plotly_chart(fig, use_container_width=True)

    # --- RIQUADRO LOGICA STRATEGICA ---
    st.markdown("---")
    with st.expander("📘 Logica di Copertura (Protocollo Kriterion)", expanded=True):
        st.markdown("""
        **Strategia: Trend Following Dinamico con Isteresi**
        
        L'obiettivo è proteggere il portafoglio (Asset USA) dal rischio cambio (Deprezzamento USD / Apprezzamento EUR) solo quando il trend è strutturalmente negativo per il Dollaro.
        
        * **Indicatore Core:** Media Mobile Semplice a 200 Giorni (SMA 200).
        * **Filtro Isteresi (Buffer 1%):** Serve a evitare falsi segnali in fasi laterali.
        
        **Regole Operative:**
        1.  **Regime BULL (Unhedged):**
            * Condizione: Prezzo > (SMA 200 + 1%).
            * Azione: Nessuna copertura. Lasciamo correre i profitti valutari (USD Forte).
        2.  **Regime BEAR (Hedged):**
            * Condizione: Prezzo < (SMA 200 - 1%).
            * Azione: Attivazione **Collar**.
                * *Buy Put EUR/USD* (Delta 0.25) per protezione downside.
                * *Sell Call EUR/USD* (Delta 0.35) per finanziare il costo.
        3.  **Buffer Zone (Hold):**
            * Se il prezzo è tra le due bande (+/- 1%), si mantiene lo stato precedente senza fare trading.
        """)

except Exception as e:
    st.error(f"Si è verificato un errore nel caricamento dei dati: {e}")

# Sidebar con info tecniche
st.sidebar.title("Configurazione")
st.sidebar.info("Dati forniti da **EODHD APIs**")
# Questa riga ora funzionerà perché abbiamo importato datetime in alto
st.sidebar.text(f"Ultimo aggiornamento:\n{datetime.now().strftime('%Y-%m-%d %H:%M')}")
