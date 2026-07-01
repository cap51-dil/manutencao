"""Normalização de credenciais GCP para service account."""

from __future__ import annotations

from typing import Any


def normalizar_credenciais_gcp(credenciais: dict[str, Any]) -> dict[str, Any]:
    """
    Ajusta private_key para o formato PEM esperado pelo google-auth.

    Problemas comuns ao colar no secrets.toml ou no Streamlit Cloud:
    - \\n literal em vez de quebra de linha
    - chave em uma única linha
    - placeholder "..." ainda não substituído
    """
    creds = dict(credenciais)
    key = creds.get("private_key")

    if not key or not isinstance(key, str):
        raise ValueError(
            "Campo 'private_key' ausente em [gcp_service_account]. "
            "Copie o valor completo do JSON da service account."
        )

    key = key.strip().strip('"').strip("'")

    if key in {"...", "…"} or "BEGIN PRIVATE KEY" not in key:
        raise ValueError(
            "private_key inválida ou ainda é placeholder. "
            "Abra o JSON baixado no GCP e copie o campo private_key inteiro, "
            "incluindo -----BEGIN PRIVATE KEY----- e -----END PRIVATE KEY-----."
        )

    if "\\n" in key:
        key = key.replace("\\n", "\n")

    if key.count("\n") < 2:
        key = (
            key.replace("-----BEGIN PRIVATE KEY-----", "-----BEGIN PRIVATE KEY-----\n")
            .replace("-----END PRIVATE KEY-----", "\n-----END PRIVATE KEY-----\n")
            .strip()
            + "\n"
        )

    if not key.startswith("-----BEGIN PRIVATE KEY-----"):
        raise ValueError(
            "private_key deve começar com -----BEGIN PRIVATE KEY-----. "
            "Veja: https://cryptography.io/en/latest/faq/#why-can-t-i-import-my-pem-file"
        )

    creds["private_key"] = key
    return creds
