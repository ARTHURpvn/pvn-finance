"""Logging estruturado simples (NFR-009) — sem PII/segredos.

Convenção: mensagens em ``evento chave=valor``; logar apenas ids (UUID),
contagens e status — nunca email, descrição, valor ou segredo."""

import logging

_CONFIGURED = False


def setup_logging(level: int = logging.INFO) -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
