import numpy as np
import pandas as pd

from src import knowledge, metrics as M, optimize, settings as S


def _rets(n=600, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2022-01-03", periods=n)
    df = pd.DataFrame({
        "SPY": rng.normal(0.0005, 0.010, n),
        "BND": rng.normal(0.0001, 0.003, n),
        "QQQ": rng.normal(0.0006, 0.014, n),
    }, index=idx)
    df[S.DEPOSIT] = 1.04 ** (1 / 252) - 1
    return df


def test_weights_convert_usd_to_pen():
    pos = pd.DataFrame({"activo": ["SPY", S.DEPOSIT], "monto": [1000.0, 4000.0], "moneda": ["USD", "PEN"]})
    w = M.weights_from_positions(pos, fx_now=4.0)
    assert w["SPY"] == 0.5 and abs(w.sum() - 1) < 1e-12


def test_max_drawdown_known_path():
    r = pd.Series([0.10, -0.50, 0.20])
    assert abs(M.max_drawdown(r) + 0.50) < 1e-12


def test_deposit_has_no_dollar_exposure():
    assert M.usd_exposure(pd.Series({S.DEPOSIT: 0.7, "SPY": 0.3})) == 0.3


def test_optimizer_respects_constraints():
    rets = _rets()
    for name, w in optimize.profiles(rets).items():
        assert abs(w.sum() - 1) < 1e-6 and (w >= 0).all()
        assert w.drop(S.DEPOSIT).max() <= S.MAX_WEIGHT + 1e-3, name


def test_riskier_profile_has_more_volatility():
    rets = _rets()
    p = optimize.profiles(rets)
    vol = {k: M.portfolio_returns(rets, w).std() for k, w in p.items()}
    assert vol["Conservador"] < vol["Moderado"] <= vol["Agresivo"] + 1e-9


def test_bm25_finds_the_relevant_chunk():
    chunks = [
        {"id": "a:p1:c0", "doc": "a", "pagina": 1, "texto": "La diversificación reduce el riesgo del portafolio."},
        {"id": "b:p3:c0", "doc": "b", "pagina": 3, "texto": "El tipo de cambio afecta a quien ahorra en dólares."},
    ]
    assert knowledge.search("tipo de cambio y dólares", chunks)[0]["id"] == "b:p3:c0"
    assert knowledge.search("xyz", chunks) == []
