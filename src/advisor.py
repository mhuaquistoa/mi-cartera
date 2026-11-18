"""Asesor: el LLM explica los números ya calculados y cita la base de conocimiento.

El LLM no calcula nada. Recibe las métricas y los fragmentos recuperados, y
devuelve un JSON con forma fija. Las citas que no correspondan a un fragmento
entregado se eliminan.
"""
import json
import os

from . import knowledge, settings as S

SYSTEM = """Eres un analista de inversiones que explica en español claro, para un inversionista peruano no experto.
Reglas:
- Usa SOLO las cifras del bloque DATOS. No inventes ni recalcules números.
- Apoya cada recomendación en un fragmento de FUENTES cuando alguno aplique, citando su id exacto. Si ninguno aplica, deja "cita" en null.
- No prometas rentabilidad. Esto es educativo, no asesoría financiera personalizada.
Responde SOLO con un JSON con esta forma:
{"resumen": "2 o 3 frases",
 "hallazgos": [{"titulo": "...", "explicacion": "..."}],
 "recomendaciones": [{"accion": "...", "por_que": "...", "cita": "id del fragmento o null"}],
 "comparacion_sp500": "1 o 2 frases sobre el portafolio sugerido frente al S&P 500, con lo que pasó en el periodo de prueba"}
Da 3 hallazgos y 3 recomendaciones."""


def api_key() -> str | None:
    key = os.getenv("DEEPSEEK_API_KEY")
    if not key:
        try:
            import streamlit as st
            key = st.secrets.get("DEEPSEEK_API_KEY")
        except Exception:
            key = None
    return key or None


def _secret(name: str) -> str | None:
    value = os.getenv(name)
    if not value:
        try:
            import streamlit as st
            value = st.secrets.get(name)
        except Exception:
            value = None
    return value or None


def unlocked(entered: str) -> bool:
    """Compara el código escrito con ADVISOR_CODE. Sin código configurado, nadie entra.

    El Asesor gasta saldo de la clave del LLM; con la app pública, el código evita
    que un visitante lo use.
    """
    import hmac
    expected = _secret("ADVISOR_CODE")
    return bool(expected) and hmac.compare_digest(entered.encode(), expected.encode())


def query_for(datos: dict) -> str:
    """Consulta para la base de conocimiento, armada con lo que más pesa en el diagnóstico."""
    terms = ["diversificación", "riesgo", "portafolio", "rentabilidad"]
    if datos["concentracion"]["peso_mayor"] > 0.4:
        terms += ["concentración", "un solo activo"]
    if datos["exposicion_dolar"] > 0.6:
        terms += ["tipo de cambio", "riesgo cambiario", "dólar"]
    if datos["actual"]["volatilidad"] > datos["sp500"]["volatilidad"]:
        terms += ["volatilidad", "perfil de riesgo", "tolerancia"]
    else:
        terms += ["renta fija", "depósitos", "inflación", "largo plazo"]
    return " ".join(terms)


def diagnose(datos: dict, chunks: list[dict]) -> dict:
    """Devuelve el diagnóstico estructurado, las fuentes usadas y el costo de la llamada."""
    from openai import OpenAI
    fuentes = knowledge.search(query_for(datos), chunks)
    user = "DATOS:\n" + json.dumps(datos, ensure_ascii=False) + "\n\nFUENTES:\n" + (
        "\n".join(f"[{f['id']}] ({f['doc']}, p. {f['pagina']}) {f['texto']}" for f in fuentes) or "(sin fuentes)")
    client = OpenAI(api_key=api_key(), base_url=S.LLM_BASE_URL)
    resp = client.chat.completions.create(
        model=S.LLM_MODEL, temperature=0.2, max_tokens=1200,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}],
        extra_body={"thinking": {"type": "disabled"}},
    )
    out = json.loads(resp.choices[0].message.content)
    by_id = {f["id"]: f for f in fuentes}
    for rec in out.get("recomendaciones", []):
        rec["cita"] = by_id.get(rec.get("cita"))   # cita inexistente -> None
    u = resp.usage
    out["costo_usd"] = (u.prompt_tokens * S.LLM_PRICE_IN + u.completion_tokens * S.LLM_PRICE_OUT) / 1e6
    out["fuentes"] = fuentes
    return out
