"""Qué le pasaría al portafolio en distintos escenarios."""
import pandas as pd

from . import settings as S
from .metrics import beta, portfolio_returns, usd_exposure

BEAR_2022 = ("2022-01-03", "2022-10-14")   # caída simultánea de acciones y bonos


def run(w: pd.Series, rets: pd.DataFrame) -> pd.DataFrame:
    r = portfolio_returns(rets, w)
    b = beta(r, rets[S.BENCHMARK])
    usd = usd_exposure(w)
    window = r.loc[BEAR_2022[0]:BEAR_2022[1]]
    rows = [
        ("Caída de 2022 (lo que pasó de enero a octubre)", float((1 + window).prod() - 1) if len(window) else None,
         "Retornos reales del periodo con estos pesos"),
        ("Mercado global −20 %", b * -0.20, f"Sensibilidad al S&P 500 (beta {b:.2f})"),
        ("Mercado global −35 % (como marzo de 2020)", b * -0.35, f"Sensibilidad al S&P 500 (beta {b:.2f})"),
        ("El dólar sube 10 %", usd * 0.10, f"{usd:.0%} del portafolio depende del dólar"),
        ("El dólar baja 10 %", usd * -0.10, f"{usd:.0%} del portafolio depende del dólar"),
    ]
    return pd.DataFrame(rows, columns=["Escenario", "Impacto", "Cómo se calcula"])
