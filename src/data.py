"""Datos de mercado: precios (Yahoo Finance) y series del BCRP, con copia local de respaldo."""
import json
from datetime import date, timedelta

import pandas as pd
import requests

from . import settings as S

MONTHS = {"Ene": 1, "Feb": 2, "Mar": 3, "Abr": 4, "May": 5, "Jun": 6,
          "Jul": 7, "Ago": 8, "Set": 9, "Sep": 9, "Oct": 10, "Nov": 11, "Dic": 12}


def _parse_period(name: str) -> pd.Timestamp:
    """'30.Oct.26' (diaria) o 'Oct.2026' (mensual) -> fecha."""
    parts = name.split(".")
    if len(parts) == 3:
        return pd.Timestamp(2000 + int(parts[2]), MONTHS[parts[1]], int(parts[0]))
    return pd.Timestamp(int(parts[1]), MONTHS[parts[0]], 1)


def bcrp_series(code: str, start: str, end: str) -> pd.Series:
    """Serie del BCRP; los días sin dato ('n.d.') se descartan."""
    r = requests.get(S.BCRP_URL.format(code=code, start=start, end=end), timeout=20)
    r.raise_for_status()
    rows = {}
    for p in r.json()["periods"]:
        try:
            rows[_parse_period(p["name"])] = float(p["values"][0])
        except ValueError:
            continue
    return pd.Series(rows, name=code).sort_index()


def _window(years: int = S.YEARS):
    end = date.today()
    return (end - timedelta(days=365 * years + 10)).isoformat(), end.isoformat()


def fx_history() -> tuple[pd.Series, str]:
    """Soles por dólar, diario. Devuelve (serie, fuente)."""
    try:
        s = bcrp_series(S.BCRP_FX, *_window())
        if len(s) > 200:
            return s, "BCRP en vivo"
    except Exception:
        pass
    s = pd.read_csv(S.SNAPSHOT / "fx.csv", index_col=0, parse_dates=True).iloc[:, 0]
    return s, "copia local"


def rates() -> tuple[dict, str]:
    """Tasa de referencia y tasa pasiva promedio en soles (% anual)."""
    try:
        start = (date.today() - timedelta(days=120)).isoformat()
        ref = bcrp_series(S.BCRP_REF_RATE, start, date.today().isoformat())
        tip = bcrp_series(S.BCRP_TIPMN, start[:7], date.today().isoformat()[:7])
        return {"referencia": float(ref.iloc[-1]), "pasiva_soles": float(tip.iloc[-1]),
                "fecha": str(ref.index[-1].date())}, "BCRP en vivo"
    except Exception:
        return json.loads((S.SNAPSHOT / "rates.json").read_text()), "copia local"


def prices(tickers: list[str]) -> tuple[pd.DataFrame, str]:
    """Precios de cierre ajustados en dólares. Si Yahoo falla, usa la copia local."""
    tickers = sorted(set(tickers))
    try:
        import yfinance as yf
        px = yf.download(tickers, period=f"{S.YEARS}y", auto_adjust=True, progress=False)["Close"]
        px = px.dropna(how="all").ffill()
        if len(px) > 200 and not px.iloc[-1].isna().all():
            return px, "Yahoo Finance en vivo"
    except Exception:
        pass
    snap = pd.read_csv(S.SNAPSHOT / "prices.csv", index_col=0, parse_dates=True)
    return snap[[t for t in tickers if t in snap.columns]], "copia local"
