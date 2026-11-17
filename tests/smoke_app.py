"""Prueba de humo: corre la app completa con datos reales. Uso: python tests/smoke_app.py"""
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

sys.stdout.reconfigure(encoding="utf-8")
at = AppTest.from_file(str(Path(__file__).parent.parent / "app.py"), default_timeout=120).run()
print("exceptions:", [e.value for e in at.exception])
print("errors:", [e.value for e in at.error], "warnings:", [w.value for w in at.warning])
for m in at.metric:
    print(m.label, "|", m.value, "|", m.delta)
for x in list(at.info) + list(at.success):
    print(x.value[:400])
for d in at.dataframe:
    print(d.value.round(3).to_string()[:1500])
assert not at.exception and not at.error
