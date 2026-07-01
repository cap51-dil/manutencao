"""Leitura de configuração a partir dos Secrets do Streamlit."""

from __future__ import annotations

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

_BLOCO_SERVICOS_EXEMPLO = """\
[servicos]
"Manutenção" = "ID_DA_PASTA_NO_DRIVE"

[planilhas."Manutenção"]
"Câmaras de Vacina" = "STATUS CÂMARAS DE VACINA"
"Serviços Prioritários" = "SERVIÇOS PRIORITÁRIOS"

[branding]
logo = "branco"
"""


def _dict_secrets(chave: str) -> dict:
    valor = st.secrets.get(chave, {})
    return dict(valor) if valor else {}


def _planilhas_de_arquivos_legacy(arquivos: dict) -> dict:
    """Converte [arquivos] antigo: 'Serviço — Planilha' → planilhas aninhadas."""
    planilhas: dict[str, dict[str, str]] = {}
    for chave, padrao in arquivos.items():
        texto = str(chave)
        if " — " in texto:
            servico, planilha = texto.split(" — ", 1)
        else:
            servico, planilha = texto, texto
        planilhas.setdefault(servico, {})[planilha] = padrao
    return planilhas


def ler_config_secrets() -> tuple[dict, dict, dict]:
    """
    Retorna (servicos, planilhas, locais).
    Aceita nomes legados: [setores] e [arquivos].
  """
    try:
        servicos = _dict_secrets("servicos") or _dict_secrets("setores")
        planilhas_cfg = _dict_secrets("planilhas")
        if not planilhas_cfg:
            planilhas_cfg = _planilhas_de_arquivos_legacy(_dict_secrets("arquivos"))
        locais_cfg = _dict_secrets("locais")
        return servicos, planilhas_cfg, locais_cfg
    except StreamlitSecretNotFoundError:
        raise


def chaves_secrets_visiveis() -> list[str]:
    try:
        return sorted(st.secrets.keys())
    except Exception:
        return []


def exibir_erro_config_ausente() -> None:
    chaves = chaves_secrets_visiveis()
    st.error("Nenhum serviço configurado em [servicos] nos Secrets.")
    st.markdown(
        "No **Streamlit Cloud → Settings → Secrets**, cole **o arquivo inteiro** "
        "(não só `[gcp_service_account]`). Use o modelo `.streamlit/secrets.toml.example`."
    )
    if chaves:
        st.warning(f"Chaves encontradas nos Secrets: {', '.join(f'`{c}`' for c in chaves)}")
        if "gcp_service_account" in chaves and "servicos" not in chaves:
            st.info("Falta a seção `[servicos]` e `[planilhas.\"Manutenção\"]`.")
    st.code(_BLOCO_SERVICOS_EXEMPLO, language="toml")
