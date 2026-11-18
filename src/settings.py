"""Parámetros del producto en un solo lugar."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / "data" / "snapshot"
KNOWLEDGE = ROOT / "data" / "knowledge" / "chunks.json"
EXAMPLE_ADVICE = ROOT / "data" / "example_advice.json"   # respuesta real del asesor, para la versión pública

YEARS = 5
TRADING_DAYS = 252
BENCHMARK = "SPY"  # ETF que replica el S&P 500

# Activos que el optimizador puede proponer además de los del usuario.
CANDIDATES = {
    "SPY": "S&P 500 (EE. UU.)",
    "QQQ": "Nasdaq 100 (tecnología)",
    "VEA": "Acciones de países desarrollados",
    "VWO": "Acciones de mercados emergentes",
    "EPU": "Acciones peruanas (MSCI Perú)",
    "BND": "Bonos de EE. UU.",
    "GLD": "Oro",
}
DEPOSIT = "DEPOSITO_PEN"
CASH_USD = "DOLARES"
SPECIAL = {DEPOSIT: "Depósito a plazo en soles", CASH_USD: "Dólares en efectivo"}

# BCRPData: códigos de series.
BCRP_URL = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api/{code}/json/{start}/{end}"
BCRP_FX = "PD04640PD"         # tipo de cambio venta, diario
BCRP_REF_RATE = "PD12301MD"   # tasa de referencia, diaria
BCRP_TIPMN = "PN07816NM"      # tasa pasiva promedio en soles, mensual

# Optimizador.
MAX_WEIGHT = 0.35             # tope por activo de mercado
SHRINK = 0.5                  # cuánto se acerca cada retorno histórico al promedio
TRAIN_SHARE = 0.7             # el 30 % final se reserva para probar la propuesta
PROFILES = {                  # volatilidad objetivo, como múltiplo de la del S&P 500
    "Conservador": 0.5,
    "Moderado": 0.85,
    "Agresivo": 1.15,
}

# LLM.
LLM_BASE_URL = "https://api.deepseek.com"
LLM_MODEL = "deepseek-flash"
LLM_PRICE_IN, LLM_PRICE_OUT = 0.30, 1.20   # USD por millón de tokens, horario pico
TOP_K = 4
