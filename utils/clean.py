"""Dispatcher de limpeza por serviço e planilha."""

from __future__ import annotations

from cleaners.camaras_vacina import limpar as limpar_camaras_vacina
from cleaners.servicos_prioritarios import limpar as limpar_servicos_prioritarios

CLEANERS: dict[tuple[str, str], object] = {
    ("Manutenção", "Câmaras de Vacina"): limpar_camaras_vacina,
    ("Manutenção", "Serviços Prioritários"): limpar_servicos_prioritarios,
}


def limpar_planilha(conteudo: bytes, servico: str, planilha: str):
    """Dispatcher para o cleaner da planilha dentro do serviço."""
    chave = (servico, planilha)
    if chave not in CLEANERS:
        raise ValueError(
            f"Planilha '{planilha}' do serviço '{servico}' sem cleaner configurado."
        )
    return CLEANERS[chave](conteudo)


def carregar_planilha_local(caminho: str) -> bytes:
    """Lê arquivo local (modo dev/offline)."""
    with open(caminho, "rb") as f:
        return f.read()
