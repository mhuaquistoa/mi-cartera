"""Llama una vez al asesor con el portafolio de ejemplo. Uso: python -m tests.smoke_advisor"""
import json
import sys

from dotenv import load_dotenv

from src import advisor, analysis, data, knowledge, settings as S

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()
import pandas as pd

pos = pd.DataFrame({"activo": [S.DEPOSIT, S.CASH_USD, "BAP", "NVDA", "SPY"],
                    "monto": [15000.0, 2000.0, 1500.0, 2500.0, 1000.0],
                    "moneda": ["PEN", "USD", "USD", "USD", "USD"]})
px, _ = data.prices(list(S.CANDIDATES) + ["BAP", "NVDA"])
fx, _ = data.fx_history()
rates, _ = data.rates()
res = analysis.analyze(pos, px, fx, rates, rates["referencia"], "Moderado")
out = advisor.diagnose(res["resumen"], knowledge.load())
print(json.dumps({k: v for k, v in out.items() if k != "fuentes"}, ensure_ascii=False, indent=1))
