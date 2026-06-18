"""Configuração de testes — garante um DATABASE_URL inócuo no ambiente.

Os testes unitários não tocam o banco real (a engine é substituída por
monkeypatch); este default só evita falha de validação ao instanciar Settings.
"""

import os

os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://test:test@localhost:5432/test"
)
