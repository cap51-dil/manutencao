"""Painel Streamlit — Plataforma de Dados APS 5.1."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import streamlit as st

from utils.clean import carregar_planilha_local, limpar_planilha
from utils.dashboard import render_dashboard
from utils.drive import carregar_planilha_setor

PLANILHA_LOCAL = "Cópia de STATUS CÂMARAS DE VACINA 2026 - AP 5.1.xlsx"


@st.cache_data(show_spinner="Carregando dados...")
def carregar_dados(
    setor: str,
    folder_id: str,
    padrao_nome: str | None,
    usar_local: bool,
    _versao: int,
):
    if usar_local:
        caminho = Path(PLANILHA_LOCAL)
        if not caminho.exists():
            raise FileNotFoundError(
                f"Planilha local não encontrada: {PLANILHA_LOCAL}. "
                "Use o Drive ou coloque o arquivo na raiz do projeto."
            )
        raw = carregar_planilha_local(str(caminho))
        meta = {
            "nome": caminho.name,
            "modificado_em": caminho.stat().st_mtime,
            "file_id": "local",
        }
    else:
        credenciais = dict(st.secrets["gcp_service_account"])
        raw, meta = carregar_planilha_setor(credenciais, folder_id, padrao_nome)

    df = limpar_planilha(raw, setor)
    return df, meta


def main() -> None:
    st.set_page_config(page_title="APS 5.1 — Dados", layout="wide")

    if "versao_cache" not in st.session_state:
        st.session_state.versao_cache = 0

    setores = dict(st.secrets.get("setores", {}))
    arquivos = dict(st.secrets.get("arquivos", {}))

    if not setores:
        st.error("Nenhum setor configurado em [setores] no secrets.toml.")
        st.stop()

    with st.sidebar:
        st.header("Configurações")
        setor = st.selectbox("Setor", options=list(setores.keys()))
        folder_id = setores[setor]
        padrao_nome = arquivos.get(setor)

        usar_local = st.checkbox(
            "Usar planilha local (dev)",
            value=not _tem_credenciais_gcp(),
            help="Lê o arquivo .xlsx na raiz do projeto, sem acessar o Drive.",
        )

        if st.button("Atualizar dados", type="primary"):
            st.cache_data.clear()
            st.session_state.versao_cache += 1
            st.rerun()

    try:
        df, meta = carregar_dados(
            setor=setor,
            folder_id=folder_id,
            padrao_nome=padrao_nome,
            usar_local=usar_local,
            _versao=st.session_state.versao_cache,
        )
    except Exception as exc:
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

    render_dashboard(df, setor)


def _tem_credenciais_gcp() -> bool:
    try:
        creds = st.secrets.get("gcp_service_account", {})
        return bool(creds.get("client_email") and creds.get("private_key"))
    except Exception:
        return False


if __name__ == "__main__":
    main()
