"""Dispatcher de limpeza por setor."""

from __future__ import annotations

from cleaners.camaras_vacina import limpar as limpar_camaras_vacina

CLEANERS = {
    "Manutenção — Câmaras de Vacina": limpar_camaras_vacina,
}


def limpar_planilha(conteudo: bytes, setor: str):
    """Dispatcher para o cleaner do setor."""
    if setor not in CLEANERS:
        raise ValueError(f"Setor '{setor}' sem cleaner configurado.")
    return CLEANERS[setor](conteudo)


def carregar_planilha_local(caminho: str) -> bytes:
    """Lê arquivo local (modo dev/offline)."""
    with open(caminho, "rb") as f:
        return f.read()
