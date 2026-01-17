import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from utils import get_eodhd_data
from strategy import apply_hedging_logic

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Kriterion Quant | FX Hedging",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2rem;
        font-weight: 600;
    }
    .main-header p {
        color: #b8d4e8;
        margin: 0.5rem 0 0 0;
        font-size: 1rem;
    }
    
    /* Metric cards */
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 1.2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-left: 4px solid #2d5a87;
        height: 100%;
    }
    .metric-card.bull {
        border-left-color: #10b981;
        background: linear-gradient(135deg, #ecfdf5 0%, #ffffff 100%);
    }
    .metric-card.bear {
        border-left-color: #ef4444;
        background: linear-gradient(135deg, #fef2f2 0%, #ffffff 100%);
    }
    .metric-label {
        font-size: 0.85rem;
        color: #6b7280;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1f2937;
        margin: 0.3rem 0;
    }
    .metric-delta {
        font-size: 0.9rem;
        color: #6b7280;
    }
    .metric-delta.positive { color: #10b981; }
    .metric-delta.negative { color: #ef4444; }
    
    /* Status badge */
    .status-badge {
        display: inline-block;
        padding: 0.5rem 1.2rem;
        border-radius: 25px;
        font-weight: 600;
        font-size: 1rem;
        margin-top: 0.5rem;
    }
    .status-badge.hedged {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        color: #b91c1c;
        border: 2px solid #f87171;
    }
    .status-badge.unhedged {
        background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
        color: #047857;
        border: 2px solid #34d399;
    }
    
    /* Section divider */
    .section-divider {
        height: 2px;
        background: linear-gradient(90deg, transparent, #e5e7eb, transparent);
        margin: 2rem 0;
    }
    
    /* Chart container */
    .chart-container {
        background: white;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: #f8fafc;
        border-radius: 8px;
        font-weight: 600;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3a5f 0%, #0f172a 100%);
    }
    [data-testid="stSidebar"] .stMarkdown {
        color: white;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: white;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 1.5rem;
        color: #6b7280;
        font-size: 0.85rem;
        border-top: 1px solid #e5e7eb;
        margin-top: 2rem;
    }
    .footer a {
        color: #2d5a87;
        text-decoration: none;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("""
<div class="main-header">
    <h1>🛡️ Kriterion Quant - FX Hedging Dashboard</h1>
    <p>Copertura Dinamica EUR/USD | Strategia SMA 200 + Hysteresis Buffer</p>
</div>
""", unsafe_allow_html=True)

# Caricamento Dati (Cache per evitare chiamate API continue)
@st.cache_data(ttl=3600)
def load_data():
    raw_df = get_eodhd_data("EURUSD.FOREX")
    processed_df = apply_hedging_logic(raw_df)
    return processed_df

try:
    df = load_data()
    
    # Ultimi dati
    last_row = df.iloc[-1]
    prev_row = df.iloc[-2]
    price_change = last_row['Close'] - prev_row['Close']
    price_change_pct = (price_change / prev_row['Close']) * 100
    
    # --- METRICHE PRINCIPALI ---
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        delta_class = "positive" if price_change >= 0 else "negative"
        delta_sign = "+" if price_change >= 0 else ""
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">💶 EUR/USD Spot</div>
            <div class="metric-value">{last_row['Close']:.4f}</div>
            <div class="metric-delta {delta_class}">{delta_sign}{price_change:.4f} ({delta_sign}{price_change_pct:.2f}%)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        sma_diff = last_row['Close'] - last_row['SMA200']
        sma_diff_pct = (sma_diff / last_row['SMA200']) * 100
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">📊 SMA 200</div>
            <div class="metric-value">{last_row['SMA200']:.4f}</div>
            <div class="metric-delta">Distanza: {sma_diff_pct:+.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        is_bear = last_row['State'] == "BEAR"
        card_class = "bear" if is_bear else "bull"
        badge_class = "hedged" if is_bear else "unhedged"
        badge_text = "🔴 HEDGED" if is_bear else "🟢 UNHEDGED"
        st.markdown(f"""
        <div class="metric-card {card_class}">
            <div class="metric-label">📡 Stato Copertura</div>
            <div class="status-badge {badge_class}">{badge_text}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col4:
        if last_row['State'] == 'BULL':
            dist = last_row['Close'] - last_row['Lower_Band']
            buffer_msg = f"Buffer → Bear: {dist:.4f}"
        else:
            dist = last_row['Upper_Band'] - last_row['Close']
            buffer_msg = f"Buffer → Bull: {dist:.4f}"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">📐 Distanza Banda</div>
            <div class="metric-value">{last_row['Distance_Pct']:.2f}%</div>
            <div class="metric-delta">{buffer_msg}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # --- GRAFICO INTERATTIVO (PLOTLY) ---
    st.markdown("### 📈 Analisi Storica e Segnali")
    
    # Creiamo subplot con indicatore di distanza
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.75, 0.25],
        subplot_titles=("EUR/USD con Bande di Isteresi", "Distanza % dalla SMA 200")
    )

    # Banda di isteresi (area colorata)
    fig.add_trace(go.Scatter(
        x=df.index.tolist() + df.index.tolist()[::-1],
        y=df['Upper_Band'].tolist() + df['Lower_Band'].tolist()[::-1],
        fill='toself',
        fillcolor='rgba(45, 90, 135, 0.1)',
        line=dict(color='rgba(0,0,0,0)'),
        name='Buffer Zone (±1%)',
        hoverinfo='skip',
        showlegend=True
    ), row=1, col=1)

    # Banda superiore
    fig.add_trace(go.Scatter(
        x=df.index, y=df['Upper_Band'],
        mode='lines', name='Upper Band (+1%)',
        line=dict(color='rgba(16, 185, 129, 0.6)', width=1, dash='dot'),
        hovertemplate='Upper: %{y:.4f}<extra></extra>'
    ), row=1, col=1)
    
    # Banda inferiore
    fig.add_trace(go.Scatter(
        x=df.index, y=df['Lower_Band'],
        mode='lines', name='Lower Band (-1%)',
        line=dict(color='rgba(239, 68, 68, 0.6)', width=1, dash='dot'),
        hovertemplate='Lower: %{y:.4f}<extra></extra>'
    ), row=1, col=1)

    # SMA 200
    fig.add_trace(go.Scatter(
        x=df.index, y=df['SMA200'],
        mode='lines', name='SMA 200',
        line=dict(color='#f59e0b', width=2),
        hovertemplate='SMA200: %{y:.4f}<extra></extra>'
    ), row=1, col=1)

    # Prezzo EUR/USD
    fig.add_trace(go.Scatter(
        x=df.index, y=df['Close'],
        mode='lines', name='EUR/USD',
        line=dict(color='#1e3a5f', width=1.5),
        hovertemplate='Spot: %{y:.4f}<extra></extra>'
    ), row=1, col=1)
    
    # Marker per cambi di stato
    hedge_entries = df[df['Action'] == 'OPEN_HEDGE']
    hedge_exits = df[df['Action'] == 'CLOSE_HEDGE']
    
    fig.add_trace(go.Scatter(
        x=hedge_entries.index, y=hedge_entries['Close'],
        mode='markers', name='🔴 Entry Hedge',
        marker=dict(color='#ef4444', size=12, symbol='triangle-down', 
                   line=dict(color='white', width=2)),
        hovertemplate='OPEN HEDGE<br>%{x}<br>Price: %{y:.4f}<extra></extra>'
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=hedge_exits.index, y=hedge_exits['Close'],
        mode='markers', name='🟢 Exit Hedge',
        marker=dict(color='#10b981', size=12, symbol='triangle-up',
                   line=dict(color='white', width=2)),
        hovertemplate='CLOSE HEDGE<br>%{x}<br>Price: %{y:.4f}<extra></extra>'
    ), row=1, col=1)

    # Subplot: Distanza percentuale
    colors = ['#ef4444' if x < -1 else '#10b981' if x > 1 else '#6b7280' for x in df['Distance_Pct']]
    fig.add_trace(go.Bar(
        x=df.index, y=df['Distance_Pct'],
        marker_color=colors,
        name='Distanza %',
        showlegend=False,
        hovertemplate='Distanza: %{y:.2f}%<extra></extra>'
    ), row=2, col=1)
    
    # Linee di riferimento sul subplot
    fig.add_hline(y=1, line_dash="dash", line_color="#10b981", line_width=1, row=2, col=1)
    fig.add_hline(y=-1, line_dash="dash", line_color="#ef4444", line_width=1, row=2, col=1)
    fig.add_hline(y=0, line_color="#9ca3af", line_width=1, row=2, col=1)

    fig.update_layout(
        height=700,
        template="plotly_white",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.8)"
        ),
        margin=dict(l=60, r=40, t=80, b=40),
        font=dict(family="Inter, sans-serif")
    )
    
    fig.update_xaxes(title_text="", row=1, col=1)
    fig.update_xaxes(title_text="Data", row=2, col=1)
    fig.update_yaxes(title_text="Prezzo", row=1, col=1)
    fig.update_yaxes(title_text="Distanza %", row=2, col=1)
    
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- RIQUADRO LOGICA STRATEGICA ---
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    
    with st.expander("📘 Logica di Copertura — Protocollo Kriterion", expanded=False):
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.markdown("""
            #### 🎯 Obiettivo
            Proteggere il portafoglio (Asset USA) dal rischio cambio in regime di debolezza strutturale del Dollaro.
            
            #### 📐 Indicatori
            - **Core:** Media Mobile Semplice 200 giorni
            - **Filtro:** Isteresi ±1% per evitare whipsaw
            """)
        
        with col_b:
            st.markdown("""
            #### ⚡ Regole Operative
            
            | Regime | Condizione | Azione |
            |--------|------------|--------|
            | 🟢 BULL | Price > SMA+1% | Unhedged |
            | 🔴 BEAR | Price < SMA-1% | Collar attivo |
            | ⚪ BUFFER | Tra le bande | Hold stato |
            """)
        
        st.markdown("""
        ---
        #### 🛡️ Struttura Collar (in regime BEAR)
        - **Buy Put EUR/USD** — Delta 0.25 (protezione downside)  
        - **Sell Call EUR/USD** — Delta 0.35 (finanziamento premio)
        """)
    
    # --- STATISTICHE AGGIUNTIVE ---
    with st.expander("📊 Statistiche Strategia", expanded=False):
        total_signals = len(df[df['Action'] != 'HOLD'])
        hedge_days = len(df[df['State'] == 'BEAR'])
        unhedged_days = len(df[df['State'] == 'BULL'])
        
        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
        stat_col1.metric("Segnali Totali", total_signals)
        stat_col2.metric("Giorni Hedged", hedge_days)
        stat_col3.metric("Giorni Unhedged", unhedged_days)
        stat_col4.metric("% Tempo Hedged", f"{(hedge_days/(hedge_days+unhedged_days))*100:.1f}%")

except Exception as e:
    st.error(f"⚠️ Si è verificato un errore nel caricamento dei dati: {e}")

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <h2 style="color: white; margin-bottom: 0.5rem;">🛡️ Kriterion Quant</h2>
        <p style="color: #94a3b8; font-size: 0.9rem;">FX Hedging System</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("#### ⚙️ Configurazione")
    st.info("📡 Dati: **EODHD APIs**")
    st.info(f"🕐 Ultimo refresh:\n{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    st.markdown("---")
    
    st.markdown("#### 📚 Risorse")
    st.markdown("""
    - [📖 Documentazione](https://kriterionquant.com)
    - [💬 Canale Telegram](https://t.me/kriterionquant)
    - [📧 Supporto](mailto:support@kriterionquant.com)
    """)
    
    st.markdown("---")
    
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0; color: #64748b; font-size: 0.8rem;">
        © 2025 Kriterion Quant<br>
        Tutti i diritti riservati
    </div>
    """, unsafe_allow_html=True)

# --- FOOTER ---
st.markdown("""
<div class="footer">
    <strong>Kriterion Quant</strong> — Finanza Quantitativa Accessibile<br>
    <a href="https://kriterionquant.com" target="_blank">kriterionquant.com</a> | 
    I segnali non costituiscono consulenza finanziaria.
</div>
""", unsafe_allow_html=True)
