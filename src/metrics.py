"""Métricas del portafolio. Todo se mide en soles, que es la moneda del usuario."""
import numpy as np
import pandas as pd

from . import settings as S


def returns_in_pen(px_usd: pd.DataFrame, fx: pd.Series, deposit_rate: float) -> pd.DataFrame:
    """Retornos diarios en soles de cada activo, más depósito y dólares en efectivo."""
    fx = fx.reindex(px_usd.index).ffill().bfill()
    rets = px_usd.mul(fx, axis=0).pct_change()
    rets[S.CASH_USD] = fx.pct_change()
    rets[S.DEPOSIT] = (1 + deposit_rate / 100) ** (1 / S.TRADING_DAYS) - 1
    return rets.iloc[1:]


def weights_from_positions(positions: pd.DataFrame, fx_now: float) -> pd.Series:
    """positions: columnas activo, monto, moneda. Devuelve pesos sobre el valor en soles."""
    pen = positions["monto"] * np.where(positions["moneda"] == "USD", fx_now, 1.0)
    w = pd.Series(pen.values, index=positions["activo"]).groupby(level=0).sum()
    return w / w.sum()


def portfolio_returns(rets: pd.DataFrame, w: pd.Series) -> pd.Series:
    """Portafolio con pesos fijos (rebalanceo diario). Solo usa fechas con todos los activos."""
    sub = rets[list(w.index)].dropna()
    return sub @ w.values


def max_drawdown(r: pd.Series) -> float:
    curve = (1 + r).cumprod()
    return float((curve / curve.cummax() - 1).min())


def stats(r: pd.Series, rf: float) -> dict:
    """rf en % anual. Retorno y volatilidad anualizados, Sharpe, peor caída y VaR mensual."""
    n = len(r)
    cagr = float((1 + r).prod() ** (S.TRADING_DAYS / n) - 1)
    vol = float(r.std() * np.sqrt(S.TRADING_DAYS))
    monthly = (1 + r).rolling(21).apply(np.prod, raw=True).dropna() - 1
    return {
        "retorno": cagr,
        "volatilidad": vol,
        "sharpe": (cagr - rf / 100) / vol if vol > 1e-9 else float("nan"),
        "peor_caida": max_drawdown(r),
        "var_mensual_95": float(monthly.quantile(0.05)) if len(monthly) else float("nan"),
        "peor_mes": float(monthly.min()) if len(monthly) else float("nan"),
    }


def beta(r: pd.Series, bench: pd.Series) -> float:
    df = pd.concat([r, bench], axis=1).dropna()
    var = df.iloc[:, 1].var()
    return float(df.iloc[:, 0].cov(df.iloc[:, 1]) / var) if var > 0 else 0.0


def concentration(w: pd.Series) -> dict:
    """HHI y número efectivo de activos (1 / HHI)."""
    hhi = float((w ** 2).sum())
    return {"hhi": hhi, "activos_efectivos": 1 / hhi, "mayor": w.idxmax(), "peso_mayor": float(w.max())}


def usd_exposure(w: pd.Series) -> float:
    """Parte del portafolio cuyo valor en soles depende del dólar."""
    return float(w.drop(labels=[S.DEPOSIT], errors="ignore").sum())
