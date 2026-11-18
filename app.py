"""Interfaz de MiCartera. La lógica vive en src/; aquí solo se muestra."""
import json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

from src import advisor, analysis, data, knowledge, settings as S

load_dotenv()
st.set_page_config(page_title="MiCartera", page_icon="📊", layout="wide")

NAMES = {**S.CANDIDATES, **S.SPECIAL}
EXAMPLE = pd.DataFrame({
    "activo": [S.DEPOSIT, S.CASH_USD, "BAP", "NVDA", "SPY"],
    "monto": [15000.0, 2000.0, 1500.0, 2500.0, 1000.0],
    "moneda": ["PEN", "USD", "USD", "USD", "USD"],
})


@st.cache_data(ttl=3600, show_spinner=False)
def load_market(tickers: tuple[str, ...]):
    prices, src_px = data.prices(list(tickers))
    fx, src_fx = data.fx_history()
    rates, src_r = data.rates()
    return prices, fx, rates, {"Precios": src_px, "Tipo de cambio": src_fx, "Tasas": src_r}


@st.cache_data(show_spinner=False)
def load_chunks():
    return knowledge.load()


def pct(x, d=1):
    return "—" if x is None or pd.isna(x) else f"{x:+.{d}%}" if d else f"{x:.0%}"


def label(a: str) -> str:
    return f"{a} · {NAMES[a]}" if a in NAMES else a


st.title("📊 MiCartera")
st.caption("Diagnostica tu portafolio en soles, compáralo con el S&P 500 y mira una alternativa para tu nivel de riesgo. "
           "Herramienta educativa: no es asesoría financiera.")

with st.sidebar:
    st.header("Tu portafolio")
    st.write("Escribe cada activo y cuánto tienes hoy. Usa el *ticker* de Yahoo Finance (SPY, BAP, AAPL), "
             f"`{S.DEPOSIT}` para depósitos en soles y `{S.CASH_USD}` para dólares en efectivo.")
    positions = st.data_editor(
        EXAMPLE, num_rows="dynamic", hide_index=True, key="pos",
        column_config={
            "activo": st.column_config.TextColumn("Activo", required=True),
            "monto": st.column_config.NumberColumn("Monto", min_value=0.0, format="%.0f", required=True),
            "moneda": st.column_config.SelectboxColumn("Moneda", options=["PEN", "USD"], required=True),
        })
    profile = st.radio("Tu nivel de riesgo", list(S.PROFILES), index=1, horizontal=True)
    deposit_rate_box = st.empty()

positions = positions.dropna()
positions = positions[positions["monto"] > 0].copy()
positions["activo"] = positions["activo"].str.strip().str.upper()
if positions.empty:
    st.warning("Agrega al menos un activo con monto mayor que cero.")
    st.stop()

user_tickers = [a for a in positions["activo"] if a not in S.SPECIAL]
with st.spinner("Trayendo precios, tipo de cambio y tasas…"):
    prices, fx, rates, sources = load_market(tuple(sorted(set(user_tickers) | set(S.CANDIDATES))))

missing = [t for t in user_tickers if t not in prices.columns or prices[t].dropna().empty]
if missing:
    st.error(f"No encontré precios para: {', '.join(missing)}. Revisa el ticker en Yahoo Finance.")
    st.stop()

deposit_rate = deposit_rate_box.number_input(
    "Tasa de tu depósito en soles (% anual)", 0.0, 15.0, float(rates["referencia"]), 0.25,
    help=f"Por defecto, la tasa de referencia del BCRP ({rates['referencia']} %). "
         f"La tasa pasiva promedio de los bancos es {rates['pasiva_soles']:.2f} %.")

res = analysis.analyze(positions, prices, fx, rates, deposit_rate, profile)
R, niveles = res["resumen"], res["niveles"]
total_pen = float((positions["monto"] * positions["moneda"].map({"USD": fx.iloc[-1], "PEN": 1.0})).sum())

tab_diag, tab_sug, tab_riesgo, tab_asesor, tab_datos = st.tabs(
    ["Diagnóstico", "Portafolio sugerido", "Niveles de riesgo", "Asesor", "Datos y método"])

with tab_diag:
    a, sp = R["actual"], R["sp500"]
    c = st.columns(5)
    c[0].metric("Valor total", f"S/ {total_pen:,.0f}")
    c[1].metric("Retorno anual", pct(a["retorno"]), f"{(a['retorno'] - sp['retorno']) * 100:+.1f} pts vs S&P 500")
    c[2].metric("Volatilidad anual", pct(a["volatilidad"], 1).lstrip("+"))
    c[3].metric("Peor caída", pct(a["peor_caida"]))
    c[4].metric("Depende del dólar", pct(R["exposicion_dolar"], 0))
    st.caption(f"Medido en soles, del {R['periodo']}, con los pesos que tienes hoy.")

    left, right = st.columns([1, 2])
    w = res["pesos"]
    left.plotly_chart(px.pie(values=w.values, names=[label(i) for i in w.index], hole=0.5,
                             title="En qué está tu plata"), width="stretch")
    curves = pd.DataFrame({
        "Tu portafolio": (1 + res["r_actual"]).cumprod(),
        "S&P 500": (1 + res["r_bench"]).cumprod(),
        "Depósito en soles": (1 + res["rets"][S.DEPOSIT]).cumprod(),
    }) * 100
    right.plotly_chart(px.line(curves, title="Cómo habrían crecido S/ 100",
                               labels={"value": "Soles", "index": "", "variable": ""}), width="stretch")

    conc = R["concentracion"]
    st.info(f"Tu activo más grande es **{label(conc['mayor'])}** con {conc['peso_mayor']:.0%}. "
            f"Tu portafolio se comporta como si tuviera **{conc['activos_efectivos']:.1f} activos** de igual tamaño. "
            f"Por cada 1 % que se mueve el S&P 500, el tuyo se mueve {R['beta_vs_sp500']:.2f} %.")

    corr, top = res["correlaciones"], res["par_mas_correlacionado"]
    if top:
        st.subheader("¿Tus activos se mueven juntos?")
        names = [NAMES.get(a, a) if a in S.SPECIAL else a for a in corr.index]
        left, right = st.columns([3, 2])
        left.plotly_chart(
            px.imshow(corr.values, x=names, y=names, zmin=-1, zmax=1, color_continuous_scale="RdBu_r",
                      text_auto=".2f", aspect="auto", labels={"color": "Correlación"})
            .update_layout(title="Correlación entre tus activos (retornos diarios en soles)"), width="stretch")
        level = "alta" if top["correlacion"] > 0.7 else "media" if top["correlacion"] > 0.4 else "baja"
        right.markdown(
            f"**{S.SPECIAL.get(top['a'], top['a'])}** y **{S.SPECIAL.get(top['b'], top['b'])}** son los que más se mueven juntos: correlación de "
            f"**{top['correlacion']:.2f}** ({level}). El promedio entre todos tus pares es {top['promedio']:.2f}.\n\n"
            "- Cerca de **1**: suben y bajan a la vez; tener los dos diversifica poco.\n"
            "- Cerca de **0**: se mueven por separado; juntos reducen el riesgo.\n"
            "- **Negativa**: cuando uno cae, el otro tiende a subir.\n\n"
            "El depósito en soles no aparece porque su retorno no cambia día a día.")

with tab_sug:
    ws = res["pesos_sugeridos"]
    ws = ws[ws > 0].sort_values()
    oos = R["prueba_fuera_de_muestra"]
    st.subheader(f"Alternativa para un perfil {profile.lower()}")
    st.write("Busca el mayor retorno esperado para ese nivel de riesgo, con tus activos y un grupo de ETFs. "
             f"Ningún activo de mercado pasa de {S.MAX_WEIGHT:.0%}.")
    left, right = st.columns([1, 2])
    left.plotly_chart(go.Figure(go.Bar(x=ws.values, y=[label(i) for i in ws.index], orientation="h",
                                       text=[f"{v:.0%}" for v in ws.values]))
                      .update_layout(title="Pesos sugeridos", xaxis_tickformat=".0%"), width="stretch")
    test = res["test"]
    from src.metrics import portfolio_returns
    curves = pd.DataFrame({
        "Sugerido": (1 + portfolio_returns(test, res["pesos_sugeridos"])).cumprod(),
        "S&P 500": (1 + test[S.BENCHMARK]).cumprod(),
        "Tu portafolio": (1 + portfolio_returns(test, res["pesos"])).cumprod(),
    }) * 100
    right.plotly_chart(px.line(curves, title="Prueba en un periodo que el modelo no vio (S/ 100 al inicio)",
                               labels={"value": "Soles", "index": "", "variable": ""}), width="stretch")
    diff = oos["sugerido"]["retorno"] - oos["sp500"]["retorno"]
    verdict = "le ganó al" if diff > 0 else "quedó por debajo del"
    box = st.success if diff > 0 else st.warning
    box(f"En la prueba ({oos['periodo']}), el portafolio sugerido rindió {pct(oos['sugerido']['retorno'])} anual y "
        f"**{verdict} S&P 500** ({pct(oos['sp500']['retorno'])}), con una volatilidad de "
        f"{oos['sugerido']['volatilidad']:.1%} frente a {oos['sp500']['volatilidad']:.1%}.")
    st.caption("Los pesos se calcularon solo con el primer 70 % de los datos. Un resultado pasado no garantiza el futuro.")

with tab_riesgo:
    st.subheader("El mismo dinero, en distintos niveles de riesgo")
    show = niveles.rename(columns={
        "retorno": "Retorno anual", "volatilidad": "Volatilidad", "sharpe": "Sharpe", "peor_caida": "Peor caída",
        "var_mensual_95": "Mes malo (1 de cada 20)", "peor_mes": "Peor mes", "retorno_prueba": "Retorno en la prueba"})
    fmt = {k: "{:+.1%}" for k in show.columns if k not in ("Portafolio", "Sharpe")} | {"Sharpe": "{:.2f}"}
    st.dataframe(show.style.format(fmt), hide_index=True, width="stretch")
    st.plotly_chart(px.scatter(show, x="Volatilidad", y="Retorno anual", text="Portafolio", size_max=18)
                    .update_traces(textposition="top center", marker_size=14)
                    .update_layout(title="Riesgo y retorno", xaxis_tickformat=".0%", yaxis_tickformat=".0%"),
                    width="stretch")
    st.subheader("Qué pasaría en cada escenario")
    esc = res["escenarios_actual"].merge(res["escenarios_sugerido"][["Escenario", "Impacto"]],
                                         on="Escenario", suffixes=(" · tu portafolio", f" · {profile.lower()}"))
    esc["En soles (tu portafolio)"] = esc["Impacto · tu portafolio"] * total_pen
    cols = ["Escenario", "Impacto · tu portafolio", "En soles (tu portafolio)", f"Impacto · {profile.lower()}", "Cómo se calcula"]
    st.dataframe(esc[cols].style.format({cols[1]: "{:+.1%}", cols[2]: "S/ {:+,.0f}", cols[3]: "{:+.1%}"}, na_rep="—"),
                 hide_index=True, width="stretch")

with tab_asesor:
    chunks = load_chunks()
    st.subheader("Explicación del diagnóstico")
    st.caption(f"Un LLM explica los números de las otras pestañas y se apoya en la base de conocimiento "
               f"({len(chunks)} fragmentos de {len({c['doc'] for c in chunks})} documentos). No calcula nada.")
    if not st.session_state.get("asesor_ok"):
        code = st.text_input("Código de acceso del Asesor", type="password",
                             help="El Asesor usa un modelo de pago. En la versión pública solo lo usa el autor.")
        if code and st.session_state.get("intentos", 0) >= 5:
            st.error("Demasiados intentos. Recarga la página.")
        elif code and advisor.unlocked(code):
            st.session_state["asesor_ok"] = True
            st.rerun()
        elif code:
            st.session_state["intentos"] = st.session_state.get("intentos", 0) + 1
            st.error("Código incorrecto.")
        st.info("El Asesor está bloqueado en la versión pública. El resto de la app funciona completo. "
                "Abajo, un ejemplo de lo que responde.")
    elif not advisor.api_key():
        st.warning("Falta la clave DEEPSEEK_API_KEY (en .env o en los secrets del despliegue).")
    elif st.button("Explícame mi portafolio", type="primary"):
        try:
            with st.spinner("Redactando…"):
                st.session_state["diag"] = advisor.diagnose(R, chunks)
        except Exception as e:
            st.error(f"El asesor no respondió ({type(e).__name__}). Las demás pestañas no dependen de él.")
    out = st.session_state.get("diag")
    if not out and not st.session_state.get("asesor_ok") and S.EXAMPLE_ADVICE.exists():
        out = json.loads(S.EXAMPLE_ADVICE.read_text(encoding="utf-8"))
        st.caption("Ejemplo con un portafolio de muestra (depósito de S/ 15 000, dólares, BAP, NVDA y SPY), "
                   "no con el que escribiste a la izquierda.")
    if out:
        st.write(out.get("resumen", ""))
        left, right = st.columns(2)
        left.markdown("#### Lo que encontré")
        for h in out.get("hallazgos", []):
            left.markdown(f"**{h.get('titulo', '')}.** {h.get('explicacion', '')}")
        right.markdown("#### Qué podrías hacer")
        for r in out.get("recomendaciones", []):
            cita = r.get("cita")
            ref = f" *(Fuente: {cita['doc']}, p. {cita['pagina']})*" if cita else ""
            right.markdown(f"**{r.get('accion', '')}.** {r.get('por_que', '')}{ref}")
        st.markdown(f"**Frente al S&P 500:** {out.get('comparacion_sp500', '')}")
        with st.expander("Fragmentos consultados"):
            for f in out["fuentes"]:
                st.markdown(f"**{f['doc']}, p. {f['pagina']}** — {f['texto']}")
            if not out["fuentes"]:
                st.write("La base de conocimiento está vacía o no tenía nada relevante.")
        st.caption(f"Costo de esta explicación: US$ {out['costo_usd']:.5f}")

with tab_datos:
    st.subheader("De dónde salen los datos")
    st.table(pd.DataFrame({"Fuente usada ahora": sources}))
    st.write(f"Tipo de cambio de hoy: S/ {fx.iloc[-1]:.3f} por dólar. Tasa de referencia del BCRP: "
             f"{rates['referencia']} % (dato del {rates['fecha']}).")
    st.markdown(
        "- **Moneda:** todo se convierte a soles con el tipo de cambio diario del BCRP.\n"
        "- **Retornos:** precios ajustados por dividendos, con los pesos de hoy mantenidos fijos.\n"
        "- **Portafolio sugerido:** máximo retorno esperado con volatilidad limitada a una fracción de la del S&P 500 "
        f"({', '.join(f'{k} {v:.0%}' for k, v in S.PROFILES.items())}), sin ventas en corto.\n"
        "- **Prueba:** los pesos se calculan con el primer 70 % del periodo y se evalúan en el 30 % final.\n"
        "- **Límites:** se asume que los tickers cotizan en dólares; no incluye comisiones ni impuestos; "
        "cinco años de historia no cubren todas las crisis.")
