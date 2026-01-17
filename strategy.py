import pandas as pd
import numpy as np

def apply_hedging_logic(df, buffer_pct=0.01):
    """
    Applica la logica SMA 200 + Hysteresis Buffer.
    Restituisce il DF arricchito con colonne 'State', 'Action', 'Regime'.
    """
    df = df.copy()
    
    # 1. Calcolo Indicatori
    df['SMA200'] = df['Close'].rolling(window=200).mean()
    df['Upper_Band'] = df['SMA200'] * (1 + buffer_pct)
    df['Lower_Band'] = df['SMA200'] * (1 - buffer_pct)
    
    # Rimuoviamo i NaN iniziali
    df.dropna(subset=['SMA200'], inplace=True)
    
    # 2. Logica a Stati (State Machine) vettoriale (iterativa per stato)
    # Dobbiamo iterare perché lo stato al tempo T dipende dallo stato al tempo T-1
    states = []
    actions = []
    
    # Stato Iniziale (Assunto basandosi solo sulla posizione rispetto alla SMA pura)
    current_state = 'BULL' if df['Close'].iloc[0] > df['SMA200'].iloc[0] else 'BEAR'
    
    for index, row in df.iterrows():
        close = row['Close']
        upper = row['Upper_Band']
        lower = row['Lower_Band']
        
        previous_state = current_state
        
        # Logica di Transizione
        if current_state == 'BULL':
            if close < lower:
                current_state = 'BEAR'
        elif current_state == 'BEAR':
            if close > upper:
                current_state = 'BULL'
        
        states.append(current_state)
        
        # Determina Azione (Solo se cambia lo stato)
        if current_state != previous_state:
            if current_state == 'BEAR':
                actions.append("OPEN_HEDGE") # Entrata in copertura
            else:
                actions.append("CLOSE_HEDGE") # Uscita copertura
        else:
            actions.append("HOLD") # Nessun cambiamento
            
    df['State'] = states
    df['Action'] = actions
    
    # Arricchimento per visualizzazione
    df['Distance_Pct'] = ((df['Close'] - df['SMA200']) / df['SMA200']) * 100
    
    return df
