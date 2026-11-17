"""Guarda una copia local de precios, tipo de cambio y tasas.

La app la usa solo si Yahoo Finance o el BCRP no responden.
Uso: python -m scripts.update_snapshot
"""
import json

from src import data, settings as S

EXTRA = ["VOO", "BAP", "SCCO", "BVN", "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "TSLA", "KO", "IFS"]

if __name__ == "__main__":
    S.SNAPSHOT.mkdir(parents=True, exist_ok=True)
    px, src_px = data.prices(list(S.CANDIDATES) + EXTRA)
    fx, src_fx = data.fx_history()
    rates, src_r = data.rates()
    assert "en vivo" in src_px and "en vivo" in src_fx and "en vivo" in src_r, "una fuente no respondió"
    px.round(4).to_csv(S.SNAPSHOT / "prices.csv")
    fx.to_csv(S.SNAPSHOT / "fx.csv")
    (S.SNAPSHOT / "rates.json").write_text(json.dumps(rates))
    print(px.shape, len(fx), rates)
