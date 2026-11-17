"""Une datos, métricas, optimizador y escenarios. No conoce la interfaz."""
import pandas as pd

from . import metrics as M, optimize, scenarios, settings as S


def analyze(positions: pd.DataFrame, px: pd.DataFrame, fx: pd.Series, rates: dict,
            deposit_rate: float, profile: str) -> dict:
    """positions: columnas activo, monto, moneda. Devuelve todo lo que muestra la app."""
    rf = rates["referencia"]
    rets = M.returns_in_pen(px, fx, deposit_rate).dropna(axis=1, how="all")
    rets = rets.dropna()   # ventana común a todos los activos
    w = M.weights_from_positions(positions, float(fx.iloc[-1]))

    r_now = M.portfolio_returns(rets, w)
    bench = rets[S.BENCHMARK]
    train, test = optimize.split(rets)
    suggested = optimize.profiles(train)

    def block(weights: pd.Series, sample: pd.DataFrame) -> dict:
        return M.stats(M.portfolio_returns(sample, weights), rf)

    levels = []
    for name, ws in {"Tu portafolio": w, **suggested, "S&P 500": pd.Series({S.BENCHMARK: 1.0})}.items():
        full = block(ws, rets)
        levels.append({"Portafolio": name, **full, "retorno_prueba": block(ws, test)["retorno"]})

    w_sug = suggested[profile]
    return {
        "rets": rets, "pesos": w, "pesos_sugeridos": w_sug, "sugeridos": suggested,
        "r_actual": r_now, "r_bench": bench, "test": test,
        "niveles": pd.DataFrame(levels),
        "escenarios_actual": scenarios.run(w, rets),
        "escenarios_sugerido": scenarios.run(w_sug, rets),
        "resumen": {
            "moneda": "soles",
            "periodo": f"{rets.index[0].date()} a {rets.index[-1].date()}",
            "pesos_actuales": _named(w),
            "actual": _r(M.stats(r_now, rf)),
            "sp500": _r(M.stats(bench, rf)),
            "deposito_tasa_anual": deposit_rate / 100,
            "beta_vs_sp500": round(M.beta(r_now, bench), 2),
            "concentracion": _r({**M.concentration(w), "mayor": _name(M.concentration(w)["mayor"])}),
            "exposicion_dolar": round(M.usd_exposure(w), 3),
            "perfil_elegido": profile,
            "pesos_sugeridos": _named(w_sug),
            "sugerido": _r(block(w_sug, rets)),
            "prueba_fuera_de_muestra": {
                "periodo": f"{test.index[0].date()} a {test.index[-1].date()}",
                "sugerido": _r(block(w_sug, test)),
                "sp500": _r(M.stats(test[S.BENCHMARK], rf)),
                "actual": _r(block(w, test)),
            },
        },
    }


def _r(d: dict) -> dict:
    return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in d.items()}


def _name(asset: str) -> str:
    """Nombre legible, para que el LLM no confunda los códigos internos."""
    return S.SPECIAL.get(asset, asset)


def _named(w: pd.Series) -> dict:
    return {_name(k): round(float(v), 3) for k, v in w.items() if v > 0}
