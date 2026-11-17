"""Convierte los PDF de conocimiento/ en data/knowledge/chunks.json.

Uso: python -m scripts.build_knowledge
"""
from src import knowledge

if __name__ == "__main__":
    print(knowledge.build(), "fragmentos")
