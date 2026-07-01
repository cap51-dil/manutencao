"""Componentes de dashboard por setor."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

SETOR_CAMARAS = "Manutenção — Câmaras de Vacina"

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


def render_dashboard(df: pd.DataFrame, setor: str) -> None:
    if setor == SETOR_CAMARAS:
        render_camaras_vacina(df)
    else:
        st.warning(f"Dashboard não configurado para o setor '{setor}'.")


def _aplicar_filtros(df: pd.DataFrame) -> pd.DataFrame:
    filtrado = df.copy()

    unidades = st.multiselect(
        "Unidade",
        options=sorted(df["unidade"].unique()),
        default=sorted(df["unidade"].unique()),
    )
    if unidades:
        filtrado = filtrado[filtrado["unidade"].isin(unidades)]

    marcas = st.multiselect(
        "Marca",
        options=sorted(df["marca"].unique()),
        default=sorted(df["marca"].unique()),
    )
    if marcas:
        filtrado = filtrado[filtrado["marca"].isin(marcas)]

    status_opts = sorted(df["status"].unique())
    status = st.multiselect("Status", options=status_opts, default=status_opts)
    if status:
        filtrado = filtrado[filtrado["status"].isin(status)]

    avaliada_opts = {"Todos": None, "Sim": True, "Não": False}
    avaliada_sel = st.selectbox("Avaliada", options=list(avaliada_opts.keys()), index=0)
    if avaliada_opts[avaliada_sel] is not None:
        filtrado = filtrado[filtrado["avaliada"] == avaliada_opts[avaliada_sel]]

    return filtrado


def render_camaras_vacina(df: pd.DataFrame) -> None:
    st.title("Status das Câmaras de Vacina — AP 5.1")

    st.subheader("Filtros")
    df_filtrado = _aplicar_filtros(df)

    total = len(df_filtrado)
    operacionais = (df_filtrado["status"] == "Operacional").sum()
    criticos = df_filtrado["status"].isin(["Inoperante", "Condenado"]).sum()
    taxa = (operacionais / total * 100) if total else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total de equipamentos", total)
    c2.metric("Operacionais", operacionais)
    c3.metric("Inoperantes + Condenados", criticos)
    c4.metric("Taxa operacional", f"{taxa:.1f}%")

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
