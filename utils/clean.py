"""Dispatcher de limpeza por serviço e planilha."""

from __future__ import annotations

from cleaners.acesso_mais_seguro import limpar as limpar_acesso_mais_seguro
from cleaners.camaras_vacina import limpar as limpar_camaras_vacina
from cleaners.chamados_cap import limpar as limpar_chamados_cap
from cleaners.equipamentos_prioritarios import limpar as limpar_equipamentos_prioritarios
from cleaners.extintores import limpar as limpar_extintores
from cleaners.falta_agua import limpar as limpar_falta_agua
from cleaners.falta_energia import limpar as limpar_falta_energia
from cleaners.odonto_equipamentos import limpar as limpar_odonto_equipamentos
from cleaners.servicos_prioritarios import limpar as limpar_servicos_prioritarios

CLEANERS: dict[tuple[str, str], object] = {
    ("Manutenção", "Câmaras de Vacina"): limpar_camaras_vacina,
    ("Manutenção", "Serviços Prioritários"): limpar_servicos_prioritarios,
    ("Manutenção", "Acesso Mais Seguro"): limpar_acesso_mais_seguro,
    ("Manutenção", "Chamados CAP"): limpar_chamados_cap,
    ("Manutenção", "Extintores"): limpar_extintores,
    ("Manutenção", "Equipamentos Prioritários"): limpar_equipamentos_prioritarios,
    ("Manutenção", "Falta de Energia"): limpar_falta_energia,
    ("Manutenção", "Falta de Água"): limpar_falta_agua,
    ("Manutenção", "Odonto"): limpar_odonto_equipamentos,
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
