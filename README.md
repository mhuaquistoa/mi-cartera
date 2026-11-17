# MiCartera

Diagnóstico de portafolios para el inversionista peruano: mide tu portafolio en soles,
lo compara con el S&P 500 y con un depósito, y propone una alternativa para tu nivel de riesgo.

README completo en construcción (se completa antes de la presentación).

## Cómo correrlo

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # y pon tu DEEPSEEK_API_KEY
streamlit run app.py
```

## Estructura

| Carpeta | Qué contiene |
|---|---|
| `app.py` | Interfaz (Streamlit). Solo muestra; no calcula. |
| `src/` | Lógica: datos, métricas, optimizador, escenarios, base de conocimiento, asesor. |
| `scripts/` | Tareas que se corren a mano: copia de datos y construcción del conocimiento. |
| `data/snapshot/` | Copia local de precios, tipo de cambio y tasas, por si las fuentes fallan. |
| `data/knowledge/` | Manual de criterios de inversión que usa el asesor. |
| `conocimiento/` | PDF fuente (locales, no se suben). |
| `docs/research/` | Notas de conversaciones con usuarios. |
| `docs/img/` | Capturas y diagramas. |
| `tests/` | Pruebas unitarias y de humo. |
