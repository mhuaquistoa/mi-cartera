"""Portafolio sugerido: máximo retorno esperado para un nivel de riesgo dado."""
import numpy as np
import pandas as pd
from scipy.optimize import minimize

from . import settings as S


def expected_returns(rets: pd.DataFrame) -> pd.Series:
    """Media histórica anualizada, acercada al promedio de todos los activos.

    Los retornos pasados son un estimador muy ruidoso; sin este ajuste el
    optimizador apuesta todo al activo que más subió.
    """
    mu = rets.mean() * S.TRADING_DAYS
    risky = mu.drop(labels=[S.DEPOSIT], errors="ignore")
    shrunk = S.SHRINK * risky.mean() + (1 - S.SHRINK) * risky
    mu.loc[shrunk.index] = shrunk
    return mu


def solve(mu: pd.Series, cov: pd.DataFrame, target_vol: float) -> pd.Series:
    """Maximiza mu·w con volatilidad <= target_vol, sin ventas en corto y con tope por activo."""
    n = len(mu)
    bounds = [(0, 1.0 if a in (S.DEPOSIT, S.CASH_USD) else S.MAX_WEIGHT) for a in mu.index]
    cons = [
        {"type": "eq", "fun": lambda w: w.sum() - 1},
        {"type": "ineq", "fun": lambda w: target_vol ** 2 - w @ cov.values @ w},
    ]
    x0 = np.full(n, 1 / n)
    res = minimize(lambda w: -(mu.values @ w), x0, bounds=bounds, constraints=cons, method="SLSQP")
    w = pd.Series(np.clip(res.x, 0, None), index=mu.index)
    w[w < 0.005] = 0
    return w / w.sum()


def split(rets: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Entrenamiento (primer 70 %) y prueba (30 % final, nunca visto por el optimizador)."""
    cut = int(len(rets) * S.TRAIN_SHARE)
    return rets.iloc[:cut], rets.iloc[cut:]


def profiles(rets_train: pd.DataFrame) -> dict[str, pd.Series]:
    """Un portafolio por perfil de riesgo, calculado solo con el periodo de entrenamiento."""
    mu = expected_returns(rets_train)
    cov = rets_train.cov() * S.TRADING_DAYS
    bench_vol = float(np.sqrt(cov.loc[S.BENCHMARK, S.BENCHMARK]))
    return {name: solve(mu, cov, mult * bench_vol) for name, mult in S.PROFILES.items()}
