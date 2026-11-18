"""Guarda una respuesta real del asesor para el portafolio de ejemplo.

La versión pública muestra este archivo en lugar de llamar al LLM.
Uso: python -m scripts.make_example_advice   (necesita DEEPSEEK_API_KEY en .env)
"""
import json

import pandas as pd
from dotenv import load_dotenv

from src import advisor, analysis, data, knowledge, settings as S

if __name__ == "__main__":
    load_dotenv()
    pos = pd.DataFrame({"activo": [S.DEPOSIT, S.CASH_USD, "BAP", "NVDA", "SPY"],
                        "monto": [15000.0, 2000.0, 1500.0, 2500.0, 1000.0],
                        "moneda": ["PEN", "USD", "USD", "USD", "USD"]})
    px, _ = data.prices(list(S.CANDIDATES) + ["BAP", "NVDA"])
    fx, _ = data.fx_history()
    rates, _ = data.rates()
    res = analysis.analyze(pos, px, fx, rates, rates["referencia"], "Moderado")
    out = advisor.diagnose(res["resumen"], knowledge.load())
    S.EXAMPLE_ADVICE.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("guardado", S.EXAMPLE_ADVICE, "| costo US$", round(out["costo_usd"], 5))
