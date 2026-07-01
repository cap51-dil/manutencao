"""Componentes de dashboard por planilha."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.branding import render_cabecalho

_STATUS_OPERACIONAL = {"Operacional", "Operacional c/ restrição"}

_COLUNAS_TABELA = [
    "unidade",
    "marca",
    "status",
    "modelo",
    "serie",
    "problema",
    "data_ocorrencia",
    "avaliada",
    "num_os",
    "chamado_glpi",
]


def render_dashboard(df: pd.DataFrame, servico: str, planilha: str) -> None:
    if servico == "Manutenção" and planilha == "Câmaras de Vacina":
        render_camaras_vacina(df)
    elif servico == "Manutenção" and planilha == "Serviços Prioritários":
        render_servicos_prioritarios(df)
    else:
        st.warning(
            f"Dashboard não configurado para '{planilha}' no serviço '{servico}'."
        )


def _rotulo_filtro(nome: str, key: str, total: int) -> str:
    selecionados = st.session_state.get(key, [])
    if not selecionados or len(selecionados) >= total:
        return f"{nome}: Todos"
    if len(selecionados) == 1:
        texto = str(selecionados[0])
        if len(texto) > 28:
            texto = texto[:25] + "…"
        return f"{nome}: {texto}"
    return f"{nome}: {len(selecionados)} selecionados"


def _filtro_popover(nome: str, opcoes: list, key: str) -> list | None:
    """Retorna None quando nenhum filtro está ativo (equivale a todos)."""
    with st.popover(_rotulo_filtro(nome, key, len(opcoes))):
        selecionados = st.multiselect(
            nome,
            options=opcoes,
            default=[],
            key=key,
            placeholder="Selecione para filtrar…",
            label_visibility="collapsed",
        )
    if not selecionados:
        return None
    return selecionados


def _aplicar_filtros(df: pd.DataFrame) -> pd.DataFrame:
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        unidades = _filtro_popover("Unidade", sorted(df["unidade"].unique()), "filtro_unidade")
    with c2:
        marcas = _filtro_popover("Marca", sorted(df["marca"].unique()), "filtro_marca")
    with c3:
        status = _filtro_popover("Status", sorted(df["status"].unique()), "filtro_status")
    with c4:
        avaliada_opts = {"Todos": None, "Sim": True, "Não": False}
        with st.popover(f"Avaliada: {st.session_state.get('filtro_avaliada', 'Todos')}"):
            avaliada_sel = st.selectbox(
                "Avaliada",
                options=list(avaliada_opts.keys()),
                index=0,
                key="filtro_avaliada",
                label_visibility="collapsed",
            )

    filtrado = df.copy()
    if unidades:
        filtrado = filtrado[filtrado["unidade"].isin(unidades)]
    if marcas:
        filtrado = filtrado[filtrado["marca"].isin(marcas)]
    if status:
        filtrado = filtrado[filtrado["status"].isin(status)]
    if avaliada_opts[avaliada_sel] is not None:
        filtrado = filtrado[filtrado["avaliada"] == avaliada_opts[avaliada_sel]]

    return filtrado


def _contar_operacionais(df: pd.DataFrame) -> int:
    status = df["status"].fillna("Operacional")
    return status.isin(_STATUS_OPERACIONAL).sum()


def render_camaras_vacina(df: pd.DataFrame) -> None:
    render_cabecalho("Status das Câmaras de Vacina — AP 5.1")
    df_filtrado = _aplicar_filtros(df)

    total = len(df_filtrado)
    operacionais = _contar_operacionais(df_filtrado)
    criticos = df_filtrado["status"].isin(["Inoperante", "Condenado"]).sum()
    taxa = (operacionais / total * 100) if total else 0.0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total de equipamentos", total)
    m2.metric("Operacionais + restrições", operacionais)
    m3.metric("Inoperantes + Condenados", criticos)
    m4.metric("Taxa operacional", f"{taxa:.1f}%")

    st.subheader("Equipamentos críticos")
    df_criticos = df_filtrado[df_filtrado["status"].isin(["Inoperante", "Condenado"])]
    if df_criticos.empty:
        st.success("Nenhum equipamento inoperante ou condenado nos filtros atuais.")
    else:
        st.dataframe(df_criticos[_COLUNAS_TABELA], use_container_width=True, hide_index=True)

    st.subheader("Visualizações")
    col_graf1, col_graf2 = st.columns(2)

    with col_graf1:
        status_counts = df_filtrado["status"].value_counts().reset_index()
        status_counts.columns = ["status", "quantidade"]
        fig_pizza = px.pie(status_counts, names="status", values="quantidade", title="Distribuição por status")
        st.plotly_chart(fig_pizza, use_container_width=True)

    with col_graf2:
        marca_counts = df_filtrado["marca"].value_counts().reset_index()
        marca_counts.columns = ["marca", "quantidade"]
        fig_marca = px.bar(
            marca_counts,
            x="quantidade",
            y="marca",
            orientation="h",
            title="Equipamentos por marca",
        )
        st.plotly_chart(fig_marca, use_container_width=True)

    status_unidade = (
        df_filtrado.groupby(["unidade", "status"])
        .size()
        .reset_index(name="quantidade")
        .sort_values("quantidade", ascending=False)
    )
    fig_unidade = px.bar(
        status_unidade,
        x="unidade",
        y="quantidade",
        color="status",
        title="Status por unidade",
        barmode="stack",
    )
    fig_unidade.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_unidade, use_container_width=True)

    st.subheader("Tabela detalhada")
    st.dataframe(df_filtrado[_COLUNAS_TABELA], use_container_width=True, hide_index=True)

    csv = df_filtrado.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Baixar CSV filtrado",
        data=csv,
        file_name="camaras_vacina_filtrado.csv",
        mime="text/csv",
    )


_COLUNAS_TABELA_PRIORITARIOS = [
    "unidade",
    "servico",
    "status",
    "grupo_status",
    "data_referencia",
    "data_execucao",
    "observacao",
]

_GRUPO_OK = "OK / Realizado"
_GRUPO_PENDENTE = "Pendente"
_GRUPO_ATENCAO = "Atenção"
_GRUPO_VENCIDO = "Vencido"


def _aplicar_filtros_prioritarios(df: pd.DataFrame) -> pd.DataFrame:
    c1, c2, c3 = st.columns(3)

    with c1:
        unidades = _filtro_popover(
            "Unidade", sorted(df["unidade"].unique()), "filtro_sp_unidade"
        )
    with c2:
        servicos = _filtro_popover(
            "Serviço", sorted(df["servico"].unique()), "filtro_sp_servico"
        )
    with c3:
        grupos = _filtro_popover(
            "Grupo status",
            sorted(df["grupo_status"].unique()),
            "filtro_sp_grupo",
        )

    filtrado = df.copy()
    if unidades:
        filtrado = filtrado[filtrado["unidade"].isin(unidades)]
    if servicos:
        filtrado = filtrado[filtrado["servico"].isin(servicos)]
    if grupos:
        filtrado = filtrado[filtrado["grupo_status"].isin(grupos)]
    return filtrado


def render_servicos_prioritarios(df: pd.DataFrame) -> None:
    render_cabecalho("Serviços Prioritários — AP 5.1")
    df_filtrado = _aplicar_filtros_prioritarios(df)

    total = len(df_filtrado)
    unidades = df_filtrado["unidade"].nunique()
    ok = (df_filtrado["grupo_status"] == _GRUPO_OK).sum()
    pendentes = (df_filtrado["grupo_status"] == _GRUPO_PENDENTE).sum()
    atencao = df_filtrado["grupo_status"].isin([_GRUPO_ATENCAO, _GRUPO_VENCIDO]).sum()

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Unidades", unidades)
    m2.metric("Registros ativos", total)
    m3.metric("OK / Realizado", ok)
    m4.metric("Pendentes", pendentes)
    m5.metric("Atenção + Vencido", atencao)

    st.subheader("Pendências e alertas")
    df_alertas = df_filtrado[
        df_filtrado["grupo_status"].isin([_GRUPO_PENDENTE, _GRUPO_ATENCAO, _GRUPO_VENCIDO])
    ].sort_values(["grupo_status", "unidade", "servico"])
    if df_alertas.empty:
        st.success("Nenhuma pendência ou alerta nos filtros atuais.")
    else:
        st.dataframe(
            df_alertas[_COLUNAS_TABELA_PRIORITARIOS],
            use_container_width=True,
            hide_index=True,
        )

    st.subheader("Visualizações")
    col_graf1, col_graf2 = st.columns(2)

    with col_graf1:
        grupo_counts = df_filtrado["grupo_status"].value_counts().reset_index()
        grupo_counts.columns = ["grupo_status", "quantidade"]
        fig_grupo = px.pie(
            grupo_counts,
            names="grupo_status",
            values="quantidade",
            title="Distribuição por grupo de status",
        )
        st.plotly_chart(fig_grupo, use_container_width=True)

    with col_graf2:
        servico_grupo = (
            df_filtrado.groupby(["servico", "grupo_status"])
            .size()
            .reset_index(name="quantidade")
        )
        fig_servico = px.bar(
            servico_grupo,
            x="servico",
            y="quantidade",
            color="grupo_status",
            title="Status por tipo de serviço",
            barmode="stack",
        )
        fig_servico.update_layout(xaxis_tickangle=-30)
        st.plotly_chart(fig_servico, use_container_width=True)

    st.subheader("Tabela detalhada")
    st.dataframe(
        df_filtrado[_COLUNAS_TABELA_PRIORITARIOS],
        use_container_width=True,
        hide_index=True,
    )

    csv = df_filtrado.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Baixar CSV filtrado",
        data=csv,
        file_name="servicos_prioritarios_filtrado.csv",
        mime="text/csv",
    )
