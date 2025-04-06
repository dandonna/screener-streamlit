
import yfinance as yf
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import ta  # Librairie stable

tickers = ["BN.PA", "AI.PA", "ENGI.PA", "ORA.PA", "TTE.PA", "DG.PA", "CS.PA"]

def plot_macd(df):
    macd = ta.trend.macd(df['Close'])
    signal = ta.trend.macd_signal(df['Close'])
    hist = macd - signal

    fig, ax = plt.subplots(figsize=(2, 1))
    ax.bar(df.index, hist, color=["green" if h > 0 else "red" for h in hist], width=1)
    ax.plot(df.index, macd, color="black", linewidth=1)
    ax.plot(df.index, signal, color="blue", linewidth=1)
    ax.axis("off")
    buf = BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()

st.title("📊 Screener Technique Multi-actifs")

table = []

for ticker in tickers:
    try:
        data = yf.download(ticker, period="6mo", interval="1d")
        if data.empty or not all(col in data.columns for col in ["Close", "High", "Low"]):
            st.error(f"Erreur pour {ticker} : données manquantes ou corrompues")
            continue

        data_h4 = yf.download(ticker, period="30d", interval="4h")
        data_2d = yf.download(ticker, period="3mo", interval="2d")
        data_w = data.copy()
        data_w.index = pd.to_datetime(data_w.index)

        close = data["Close"].iloc[-1]

        last_month = data.resample('M').agg({'High': 'max', 'Low': 'min', 'Close': 'last'}).iloc[-2]
        pivot = (last_month.High + last_month.Low + last_month.Close) / 3
        r1 = (2 * pivot) - last_month.Low
        s1 = (2 * pivot) - last_month.High

        if close > r1:
            pos = "> R1"
            ecart = (close - r1) / r1 * 100
        elif close < s1:
            pos = "< S1"
            ecart = (close - s1) / s1 * 100
        else:
            pos = "≈ Pivot"
            ecart = (close - pivot) / pivot * 100

        weekly = data_w.resample("W").last()
        mm50 = ta.trend.sma_indicator(weekly['Close'], window=50)
        pente = "🔺" if mm50.iloc[-1] > mm50.iloc[-2] else "🔻" if mm50.iloc[-1] < mm50.iloc[-2] else "➡️"

        ema13_h4 = ta.trend.ema_indicator(data_h4['Close'], window=13)
        ema25_h4 = ta.trend.ema_indicator(data_h4['Close'], window=25)
        ema_h4 = "🔺" if ema13_h4.iloc[-1] > ema25_h4.iloc[-1] else "🔻"

        ema13_2d = ta.trend.ema_indicator(data_2d['Close'], window=13)
        ema25_2d = ta.trend.ema_indicator(data_2d['Close'], window=25)
        ema_2d = "🔺" if ema13_2d.iloc[-1] > ema25_2d.iloc[-1] else "🔻"

        rsi = ta.momentum.rsi(data['Close']).iloc[-1]

        macd_img = plot_macd(data.tail(60))
        macd_html = f'<img src="data:image/png;base64,{macd_img}" width="100"/>'

        table.append({
            "Ticker": ticker.replace(".PA", ""),
            "Position Pivot": pos,
            "Écart %": f"{ecart:.2f}%",
            "MM50W": pente,
            "EMA H4": ema_h4,
            "EMA 2D": ema_2d,
            "RSI (D)": f"{rsi:.1f}",
            "MACD (D)": macd_html
        })

    except Exception as e:
        st.error(f"Erreur pour {ticker} : {e}")

df_display = pd.DataFrame(table)
if "MACD (D)" in df_display.columns:
    df_display["MACD (D)"] = df_display["MACD (D)"].apply(lambda x: st.markdown(x, unsafe_allow_html=True))
    st.dataframe(df_display.drop(columns=["MACD (D)"]))
else:
    st.dataframe(df_display)
