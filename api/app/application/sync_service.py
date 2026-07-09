"""SyncService — orquestra a sincronização de uma conexão.

Fluxo: consent check (RN-03) → fetch via Port (com backoff) → normalização
(RN-01) → dedupe (RN-05) → persistência atômica por conta → atualização de
status/last_sync_at → sync_logs (NFR-004/009)."""

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

from app.application.categorization_service import CategorizationService
from app.application.normalization import normalize_transaction
from app.application.retry import with_retry
from app.domain.account import AccountType
from app.domain.connection import (
    ConnectionStatus,
    connection_status_from_item,
)
from app.domain.dedupe import dedupe_by_provider_id
from app.ports.financial_data_port import (
    AggregatorError,
    FinancialDataPort,
)
from app.ports.repositories import (
    AccountRepository,
    ConnectionRepository,
    InvestmentRepository,
    SyncLogRepository,
    TransactionRepository,
)


class ConnectionNotFound(Exception):
    """Conexão inexistente ou de outro usuário."""


class SyncFailed(Exception):
    """Falha irrecuperável durante a sincronização."""


@dataclass(frozen=True, slots=True)
class SyncResult:
    status: str
    imported: int


class SyncService:
    def __init__(
        self,
        *,
        adapter: FinancialDataPort,
        connections: ConnectionRepository,
        accounts: AccountRepository,
        transactions: TransactionRepository,
        sync_logs: SyncLogRepository,
        categorization: CategorizationService | None = None,
        investments: InvestmentRepository | None = None,
        base_delay: float = 0.5,
    ) -> None:
        self._adapter = adapter
        self._connections = connections
        self._accounts = accounts
        self._transactions = transactions
        self._sync_logs = sync_logs
        self._categorization = categorization
        self._investments = investments
        self._base_delay = base_delay

    def sync(self, *, connection_id: UUID, user_id: UUID) -> SyncResult:
        connection = self._connections.get(connection_id, user_id)
        if connection is None:
            raise ConnectionNotFound

        now = datetime.now(UTC)

        # RN-03: consentimento expirado (localmente conhecido) → requer_reauth.
        if connection.is_consent_expired(now):
            self._connections.set_status(
                connection.id, ConnectionStatus.REQUER_REAUTH
            )
            return SyncResult(status=ConnectionStatus.REQUER_REAUTH.value, imported=0)

        # RN-03: lê o estado real do item no agregador (LOGIN_ERROR, MFA,
        # consentimento expirado no provedor). Estados terminais não-OK abortam
        # a sync; estados em progresso/desconhecidos (None) seguem o fluxo.
        item_status = self._item_status(connection.provider_item_id, now)
        if item_status in (ConnectionStatus.REQUER_REAUTH, ConnectionStatus.ERRO):
            self._connections.set_status(connection.id, item_status)
            return SyncResult(status=item_status.value, imported=0)

        # Sync incremental: busca só o que mudou desde o último sync (RN — só a
        # primeira carga baixa o histórico todo). Overlap de 1 dia recupera
        # transações que chegaram atrasadas/pendentes com data anterior.
        since = (
            (connection.last_sync_at - timedelta(days=1)).date()
            if connection.last_sync_at is not None
            else None
        )

        log_id = self._sync_logs.start(connection.id)
        try:
            imported = self._do_sync(
                connection_id=connection.id,
                user_id=user_id,
                provider_item_id=connection.provider_item_id,
                since=since,
            )
        except AggregatorError as exc:
            self._connections.set_status(connection.id, ConnectionStatus.ERRO)
            self._sync_logs.finish(log_id, status="erro", error=str(exc)[:1000])
            raise SyncFailed(str(exc)) from exc

        self._connections.mark_synced(
            connection.id, now, status=ConnectionStatus.ATIVA
        )
        self._sync_logs.finish(log_id, status="success")
        return SyncResult(status=ConnectionStatus.ATIVA.value, imported=imported)

    def _item_status(
        self, provider_item_id: str, now: datetime
    ) -> ConnectionStatus | None:
        """Lê o item no agregador e mapeia para o status da conexão (RN-03).

        Falha de leitura não aborta a sync (retorna None): o fetch seguinte
        tratará o erro. Estado em progresso/desconhecido também retorna None."""
        try:
            item = with_retry(
                lambda: self._adapter.fetch_item(provider_item_id=provider_item_id),
                base_delay=self._base_delay,
            )
        except AggregatorError:
            return None
        return connection_status_from_item(
            item.status, consent_expires_at=item.consent_expires_at, now=now
        )

    def _sync_investments(
        self, *, connection_id: UUID, user_id: UUID, provider_item_id: str
    ) -> None:
        """Busca e persiste os investimentos da conexão (compõem o patrimônio)."""
        if self._investments is None:
            return
        provider_investments = with_retry(
            lambda: self._adapter.fetch_investments(
                provider_item_id=provider_item_id
            ),
            base_delay=self._base_delay,
        )
        for provider_investment in provider_investments:
            self._investments.upsert(
                user_id=user_id,
                connection_id=connection_id,
                provider_investment=provider_investment,
            )

    def _do_sync(
        self,
        *,
        connection_id: UUID,
        user_id: UUID,
        provider_item_id: str,
        since: date | None = None,
    ) -> int:
        provider_accounts = with_retry(
            lambda: self._adapter.fetch_accounts(provider_item_id=provider_item_id),
            base_delay=self._base_delay,
        )
        self._sync_investments(
            connection_id=connection_id,
            user_id=user_id,
            provider_item_id=provider_item_id,
        )
        categorizer = (
            self._categorization.build_for_user(user_id)
            if self._categorization is not None
            else None
        )
        imported = 0
        for provider_account in provider_accounts:
            account = self._accounts.upsert(
                user_id=user_id,
                connection_id=connection_id,
                provider_account=provider_account,
            )
            provider_txs = with_retry(
                lambda pa=provider_account: self._adapter.fetch_transactions(
                    provider_item_id=provider_item_id,
                    provider_account_id=pa.provider_account_id,
                    since=since,
                ),
                base_delay=self._base_delay,
            )
            raw_by_id = {
                pt.provider_transaction_id: pt.raw for pt in provider_txs
            }
            is_credit_card = account.type == AccountType.CREDIT_CARD
            domain_txs = [
                normalize_transaction(
                    pt,
                    user_id=user_id,
                    account_id=account.id,
                    transaction_id=uuid4(),
                    category_id=(
                        categorizer(pt.description, pt.provider_category)
                        if categorizer is not None
                        else None
                    ),
                    is_credit_card=is_credit_card,
                )
                for pt in provider_txs
            ]
            # Dedup intra-lote (RN-05): a resposta do provedor pode repetir ids.
            # O dedup contra o que já existe é garantido no banco (ON CONFLICT).
            fresh = dedupe_by_provider_id(domain_txs)
            items = [
                (tx, raw_by_id.get(tx.provider_transaction_id)) for tx in fresh
            ]
            imported += self._transactions.add_many(connection_id, items)
        return imported
