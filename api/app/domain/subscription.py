"""Assinaturas recorrentes — detecção a partir das transações.

Não é uma entidade persistida: uma assinatura é *derivada* das transações
(cobranças recorrentes do mesmo serviço). O Pluggy não entrega ``merchant``
no sandbox, então casamos o serviço pela descrição (catálogo curado) e pela
categoria do agregador (streaming). Lógica pura, sem I/O — testável."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date as date_type
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Brand:
    """Serviço de assinatura conhecido: nome exibido, logo (slug) e cor."""

    name: str
    slug: str  # nome do asset de logo no frontend (public/subs/<slug>.svg)
    color: str  # cor da marca (fallback do avatar quando não há logo)
    pattern: re.Pattern[str]


def _b(name: str, slug: str, color: str, regex: str) -> Brand:
    return Brand(name, slug, color, re.compile(regex, re.IGNORECASE))


#: Catálogo curado. A ordem importa: o primeiro que casar vence (mais
#: específico antes do mais genérico).
CATALOG: tuple[Brand, ...] = (
    _b("Netflix", "netflix", "#E50914", r"netflix"),
    _b("Spotify", "spotify", "#1DB954", r"spotify"),
    _b("YouTube Premium", "youtube", "#FF0000", r"youtube"),
    _b("Disney+", "disneyplus", "#113CCF", r"disney"),
    _b("HBO Max", "hbomax", "#7B2BF9", r"hbo\s?max|\bhbo\b"),
    _b("Amazon Prime", "amazonprime", "#00A8E1", r"amazon\s?prime|prime\s?video"),
    _b("Paramount+", "paramountplus", "#0064FF", r"paramount"),
    _b("Globoplay", "globoplay", "#F5001E", r"globoplay"),
    _b("Deezer", "deezer", "#A238FF", r"deezer"),
    _b("Apple", "apple", "#111111", r"apple\.?com|itunes|\bapple\b"),
    _b("Google", "google", "#4285F4", r"google"),
    _b("Microsoft", "microsoft", "#00A4EF", r"microsoft|xbox"),
)

#: Categorias do Pluggy que, por si só, indicam assinatura recorrente.
STREAMING_CATEGORIES = frozenset(
    {"video streaming", "music streaming", "streaming"}
)

#: Mínimo de meses distintos para tratar como assinatura recorrente (filtra
#: cobranças pontuais).
_MIN_MONTHS = 2


@dataclass(frozen=True, slots=True)
class Charge:
    """Uma cobrança candidata (transação de saída, não-transferência)."""

    date: date_type
    amount: Decimal  # negativo (saída); usamos o valor absoluto
    description: str
    provider_category: str | None


@dataclass(frozen=True, slots=True)
class Subscription:
    """Assinatura detectada, com o valor mensal (última cobrança)."""

    name: str
    slug: str
    color: str
    monthly_amount: Decimal  # valor absoluto da cobrança mais recente
    occurrences: int
    months: int  # meses distintos em que apareceu
    last_date: date_type
    category: str | None


def match_brand(description: str, provider_category: str | None) -> Brand | None:
    """Retorna a marca do catálogo que casa com a descrição, ou ``None``.

    Se a categoria do Pluggy for de streaming mas nenhum nome do catálogo
    casar, ainda assim não inventamos marca — retorna ``None`` (o chamador
    pode optar por um genérico via :func:`detect`)."""
    for brand in CATALOG:
        if brand.pattern.search(description):
            return brand
    return None


def _is_candidate(charge: Charge) -> bool:
    cat = (charge.provider_category or "").strip().lower()
    return cat in STREAMING_CATEGORIES or match_brand(
        charge.description, charge.provider_category
    ) is not None


def detect(charges: Iterable[Charge]) -> list[Subscription]:
    """Agrupa cobranças por serviço e devolve as que recorrem em ≥2 meses.

    O valor mensal é o da cobrança mais recente (planos mudam de preço)."""
    buckets: dict[str, dict] = {}
    for c in charges:
        brand = match_brand(c.description, c.provider_category)
        if brand is not None:
            key = brand.slug
            name, slug, color = brand.name, brand.slug, brand.color
        else:
            cat = (c.provider_category or "").strip().lower()
            if cat not in STREAMING_CATEGORIES:
                continue  # nem marca conhecida nem categoria de streaming
            # Categoria de streaming sem marca no catálogo: agrupa pela própria
            # descrição bruta como um serviço genérico.
            key = f"cat:{c.description.strip().lower()[:40]}"
            name, slug, color = c.description.strip()[:40] or "Assinatura", "", "#6B7280"

        b = buckets.get(key)
        if b is None:
            b = {
                "name": name,
                "slug": slug,
                "color": color,
                "occurrences": 0,
                "months": set(),
                "last_date": c.date,
                "last_amount": abs(c.amount),
                "category": c.provider_category,
            }
            buckets[key] = b
        b["occurrences"] += 1
        b["months"].add((c.date.year, c.date.month))
        if c.date >= b["last_date"]:
            b["last_date"] = c.date
            b["last_amount"] = abs(c.amount)

    subs = [
        Subscription(
            name=b["name"],
            slug=b["slug"],
            color=b["color"],
            monthly_amount=b["last_amount"],
            occurrences=b["occurrences"],
            months=len(b["months"]),
            last_date=b["last_date"],
            category=b["category"],
        )
        for b in buckets.values()
        if len(b["months"]) >= _MIN_MONTHS
    ]
    subs.sort(key=lambda s: s.monthly_amount, reverse=True)
    return subs


def monthly_total(subscriptions: Iterable[Subscription]) -> Decimal:
    """Soma o custo mensal estimado (última cobrança de cada assinatura)."""
    return sum((s.monthly_amount for s in subscriptions), Decimal("0"))
