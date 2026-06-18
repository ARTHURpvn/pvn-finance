"""Cofre de credenciais — cifragem em repouso (ADR-005 / NFR-001).

Cifra o segredo do agregador com Fernet (AES-128 + HMAC). A chave vive
em variável de ambiente, separada do banco. O segredo NUNCA é logado."""

from cryptography.fernet import Fernet


class CredentialVault:
    """Cifra/decifra segredos do agregador para `connections.encrypted_secret`."""

    def __init__(self, key: str) -> None:
        # Fernet valida o formato da chave; chave inválida levanta ValueError.
        self._fernet = Fernet(key.encode() if isinstance(key, str) else key)

    def encrypt(self, plaintext: str) -> bytes:
        """Cifra um segredo. Retorna o token Fernet (bytes) para persistir."""
        return self._fernet.encrypt(plaintext.encode())

    def decrypt(self, token: bytes) -> str:
        """Decifra um token. Levanta cryptography.fernet.InvalidToken se a
        chave estiver errada ou o token for adulterado."""
        return self._fernet.decrypt(token).decode()
