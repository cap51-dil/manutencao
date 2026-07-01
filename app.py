"""Painel Streamlit — Plataforma de Dados APS 5.1."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from utils.branding import injetar_estilos
from utils.clean import carregar_planilha_local, limpar_planilha
from utils.dashboard import render_dashboard
from utils.secrets_cfg import exibir_erro_config_ausente, ler_config_secrets


@st.cache_data(show_spinner="Carregando dados...")
def carregar_dados(
    servico: str,
    planilha: str,
    folder_id: str,
    padrao_nome: str | None,
    caminho_local: str | None,
    usar_local: bool,
    _versao: int,
):
    if usar_local:
        if not caminho_local:
            raise FileNotFoundError(
                f"Planilha local não configurada para '{planilha}' em [locais.{servico}]."
            )
        caminho = Path(caminho_local)
        if not caminho.exists():
            raise FileNotFoundError(
                f"Planilha local não encontrada: {caminho_local}. "
                "Use o Drive ou coloque o arquivo na raiz do projeto."
            )
        raw = carregar_planilha_local(str(caminho))
        meta = {
            "nome": caminho.name,
            "modificado_em": caminho.stat().st_mtime,
            "file_id": "local",
        }
    else:
        try:
            from utils.drive import carregar_planilha
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError(
                "Dependências do Google Drive não instaladas. "
                "Ative o ambiente virtual e rode: pip install -r requirements.txt"
            ) from exc
        credenciais = dict(st.secrets["gcp_service_account"])
        raw, meta = carregar_planilha(credenciais, folder_id, padrao_nome)

    df = limpar_planilha(raw, servico, planilha)
    return df, meta


def _ler_config_secrets():
    try:
        return ler_config_secrets()
    except StreamlitSecretNotFoundError as exc:
        st.error("Não foi possível ler os Secrets do app.")
        st.exception(exc)
        st.markdown(
            "No **Streamlit Cloud → Settings → Secrets**, confira:\n"
            "- grupos com acento entre aspas: `[planilhas.\"Manutenção\"]`\n"
            "- `private_key` em bloco multilinha (modelo em `.streamlit/secrets.toml.example`)"
        )
        st.stop()


def main() -> None:
    st.set_page_config(
        page_title="APS 5.1 — Dados",
        layout="wide",
    )
    injetar_estilos()

    # Primeira execução rápida: ajuda o health check do Streamlit Cloud a concluir.
    if "boot_ok" not in st.session_state:
        st.session_state.boot_ok = True
        st.rerun()

    if "versao_cache" not in st.session_state:
        st.session_state.versao_cache = 0

    servicos, planilhas_cfg, locais_cfg = _ler_config_secrets()

    if not servicos:
        exibir_erro_config_ausente()
        st.stop()

    with st.sidebar:
        st.header("Configurações")
        servico = st.selectbox("Serviço", options=list(servicos.keys()))
        folder_id = servicos[servico]

        planilhas_servico = dict(planilhas_cfg.get(servico, {}))
        if not planilhas_servico:
            st.error(f"Nenhuma planilha em [planilhas.\"{servico}\"] nos Secrets.")
            st.stop()

        planilha = st.selectbox("Planilha", options=list(planilhas_servico.keys()))
        padrao_nome = planilhas_servico[planilha]
        caminho_local = dict(locais_cfg.get(servico, {})).get(planilha)

        usar_local = st.checkbox(
            "Usar planilha local (dev)",
            value=not _tem_credenciais_gcp() and bool(caminho_local),
            disabled=not caminho_local,
            help=(
                "Lê o arquivo .xlsx na raiz do projeto, sem acessar o Drive. "
                "Disponível apenas para planilhas com entrada em [locais]."
            ),
        )

        if st.button("Atualizar dados", type="primary"):
            st.cache_data.clear()
            st.session_state.versao_cache += 1
            st.rerun()

    try:
        with st.spinner("Carregando dados do Drive…"):
            df, meta = carregar_dados(
                servico=servico,
                planilha=planilha,
                folder_id=folder_id,
                padrao_nome=padrao_nome,
                caminho_local=caminho_local,
                usar_local=usar_local,
                _versao=st.session_state.versao_cache,
            )
    except Exception as exc:
        msg = str(exc)
        if "PEM" in msg or "private_key" in msg.lower():
            st.error(f"Erro ao carregar dados: {exc}")
            st.info(
                "A `private_key` nos Secrets provavelmente está mal formatada. "
                "Use o formato multilinha do `.streamlit/secrets.toml.example` "
                "ou garanta que `\\n` no JSON virou quebra de linha real. "
                "[Documentação PEM](https://cryptography.io/en/latest/faq/#why-can-t-i-import-my-pem-file)"
            )
        else:
            st.error(f"Erro ao carregar dados: {exc}")
        st.stop()

    with st.sidebar:
        st.divider()
        st.caption("Fonte dos dados")
        st.write(f"**Arquivo:** {meta['nome']}")
        modificado = meta["modificado_em"]
        if isinstance(modificado, (int, float)):
            modificado = datetime.fromtimestamp(modificado).strftime("%d/%m/%Y %H:%M")
        st.write(f"**Modificado:** {modificado}")

        with st.expander("Debug"):
            st.write(f"Linhas: {len(df)} | Colunas: {len(df.columns)}")
            st.dataframe(df.head(5))

    render_dashboard(df, servico, planilha)


def _tem_credenciais_gcp() -> bool:
    try:
        creds = st.secrets.get("gcp_service_account", {})
        return bool(creds.get("client_email") and creds.get("private_key"))
    except Exception:
        return False


main()
