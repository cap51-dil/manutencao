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
    renderers = {
        ("Manutenção", "Câmaras de Vacina"): render_camaras_vacina,
        ("Manutenção", "Serviços Prioritários"): render_servicos_prioritarios,
        ("Manutenção", "Acesso Mais Seguro"): render_acesso_mais_seguro,
        ("Manutenção", "Chamados CAP"): render_chamados_cap,
        ("Manutenção", "Extintores"): render_extintores,
        ("Manutenção", "Equipamentos Prioritários"): render_equipamentos_prioritarios,
        ("Manutenção", "Falta de Energia"): render_falta_energia,
        ("Manutenção", "Falta de Água"): render_falta_agua,
        ("Manutenção", "Odonto"): render_odonto,
    }
    renderer = renderers.get((servico, planilha))
    if renderer:
        renderer(df)
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


def _botao_csv(df: pd.DataFrame, nome_arquivo: str) -> None:
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Baixar CSV filtrado",
        data=csv,
        file_name=nome_arquivo,
        mime="text/csv",
    )


def _render_painel_equipamentos(
    df: pd.DataFrame,
    titulo: str,
    status_ok: set[str],
    status_criticos: set[str],
    colunas_tabela: list[str],
    nome_csv: str,
    filtro_tipo_key: str | None = None,
    coluna_tipo: str | None = None,
) -> None:
    render_cabecalho(titulo)

    c1, c2, c3 = st.columns(3)
    with c1:
        unidades = _filtro_popover("Unidade", sorted(df["unidade"].unique()), f"f_{nome_csv}_u")
    with c2:
        status = _filtro_popover("Status", sorted(df["status"].unique()), f"f_{nome_csv}_s")
    with c3:
        tipos = None
        if filtro_tipo_key and coluna_tipo:
            tipos = _filtro_popover(
                "Tipo",
                sorted(df[coluna_tipo].unique()),
                filtro_tipo_key,
            )

    filtrado = df.copy()
    if unidades:
        filtrado = filtrado[filtrado["unidade"].isin(unidades)]
    if status:
        filtrado = filtrado[filtrado["status"].isin(status)]
    if tipos and coluna_tipo:
        filtrado = filtrado[filtrado[coluna_tipo].isin(tipos)]

    total = len(filtrado)
    ok = filtrado["status"].isin(status_ok).sum()
    criticos = filtrado["status"].isin(status_criticos).sum()
    taxa = (ok / total * 100) if total else 0.0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total de equipamentos", total)
    m2.metric("Operacionais", ok)
    m3.metric("Críticos", criticos)
    m4.metric("Taxa operacional", f"{taxa:.1f}%")

    st.subheader("Equipamentos críticos")
    df_criticos = filtrado[filtrado["status"].isin(status_criticos)]
    if df_criticos.empty:
        st.success("Nenhum equipamento crítico nos filtros atuais.")
    else:
        st.dataframe(df_criticos[colunas_tabela], use_container_width=True, hide_index=True)

    st.subheader("Visualizações")
    col_graf1, col_graf2 = st.columns(2)
    with col_graf1:
        status_counts = filtrado["status"].value_counts().reset_index()
        status_counts.columns = ["status", "quantidade"]
        fig = px.pie(status_counts, names="status", values="quantidade", title="Distribuição por status")
        st.plotly_chart(fig, use_container_width=True)
    with col_graf2:
        if coluna_tipo and coluna_tipo in filtrado.columns:
            tipo_counts = filtrado[coluna_tipo].value_counts().reset_index()
            tipo_counts.columns = [coluna_tipo, "quantidade"]
            fig = px.bar(
                tipo_counts,
                x="quantidade",
                y=coluna_tipo,
                orientation="h",
                title="Equipamentos por tipo",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            marca_counts = filtrado["marca"].value_counts().head(10).reset_index()
            marca_counts.columns = ["marca", "quantidade"]
            fig = px.bar(
                marca_counts,
                x="quantidade",
                y="marca",
                orientation="h",
                title="Equipamentos por marca",
            )
            st.plotly_chart(fig, use_container_width=True)

    if coluna_tipo and coluna_tipo in filtrado.columns:
        por_unidade = (
            filtrado.groupby(["unidade", coluna_tipo])
            .size()
            .reset_index(name="quantidade")
        )
        fig_unidade = px.bar(
            por_unidade,
            x="unidade",
            y="quantidade",
            color=coluna_tipo,
            title="Quantidade por unidade e tipo",
            barmode="stack",
        )
        fig_unidade.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_unidade, use_container_width=True)

    st.subheader("Tabela detalhada")
    st.dataframe(filtrado[colunas_tabela], use_container_width=True, hide_index=True)
    _botao_csv(filtrado, nome_csv)


def render_acesso_mais_seguro(df: pd.DataFrame) -> None:
    render_cabecalho("Acesso Mais Seguro — AP 5.1")

    meses = sorted(df["mes"].unique())
    mes_sel = st.selectbox("Mês", options=meses, index=len(meses) - 1)
    df_mes = df[df["mes"] == mes_sel].copy()

    c1, c2 = st.columns(2)
    with c1:
        unidades = _filtro_popover("Unidade", sorted(df_mes["unidade"].unique()), "filtro_ams_u")
    with c2:
        cores = _filtro_popover("Status", sorted(df_mes["status_cor"].unique()), "filtro_ams_c")

    if unidades:
        df_mes = df_mes[df_mes["unidade"].isin(unidades)]
    if cores:
        df_mes = df_mes[df_mes["status_cor"].isin(cores)]

    total = len(df_mes)
    verdes = (df_mes["status_cor"] == "VERDE").sum()
    alertas = df_mes["status_cor"].isin(["AMARELO", "LARANJA", "VERMELHO"]).sum()
    taxa = (verdes / total * 100) if total else 0.0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Registros no mês", total)
    m2.metric("Verde", verdes)
    m3.metric("Amarelo + Laranja + Vermelho", alertas)
    m4.metric("Taxa verde", f"{taxa:.1f}%")

    st.subheader("Alertas do mês")
    df_alertas = df_mes[df_mes["status_cor"].isin(["AMARELO", "LARANJA", "VERMELHO"])]
    if df_alertas.empty:
        st.success("Nenhum alerta no mês e filtros atuais.")
    else:
        st.dataframe(
            df_alertas[["unidade", "data", "status_cor"]].sort_values(["status_cor", "unidade"]),
            use_container_width=True,
            hide_index=True,
        )

    st.subheader("Visualizações")
    col_graf1, col_graf2 = st.columns(2)
    with col_graf1:
        cor_counts = df_mes["status_cor"].value_counts().reset_index()
        cor_counts.columns = ["status_cor", "quantidade"]
        fig = px.pie(cor_counts, names="status_cor", values="quantidade", title="Distribuição por cor")
        st.plotly_chart(fig, use_container_width=True)
    with col_graf2:
        por_unidade = (
            df_mes.groupby(["unidade", "status_cor"])
            .size()
            .reset_index(name="quantidade")
        )
        fig = px.bar(
            por_unidade,
            x="unidade",
            y="quantidade",
            color="status_cor",
            title="Status por unidade",
            barmode="stack",
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    pivot = df_mes.pivot_table(
        index="unidade",
        columns="data",
        values="status_cor",
        aggfunc="first",
    )
    st.subheader("Mapa do mês")
    st.dataframe(pivot, use_container_width=True)
    _botao_csv(df_mes, "acesso_mais_seguro_filtrado.csv")


_COLUNAS_CHAMADOS = [
    "numero",
    "data_abertura",
    "empresa",
    "tipo_servico",
    "setor",
    "descricao",
    "status",
    "prioridade",
    "data_realizacao",
]


def render_chamados_cap(df: pd.DataFrame) -> None:
    render_cabecalho("Chamados CAP — AP 5.1")

    c1, c2, c3 = st.columns(3)
    with c1:
        status = _filtro_popover("Status", sorted(df["status"].unique()), "filtro_ch_status")
    with c2:
        tipos = _filtro_popover("Tipo de serviço", sorted(df["tipo_servico"].unique()), "filtro_ch_tipo")
    with c3:
        prioridades = _filtro_popover("Prioridade", sorted(df["prioridade"].dropna().unique()), "filtro_ch_prio")

    filtrado = df.copy()
    if status:
        filtrado = filtrado[filtrado["status"].isin(status)]
    if tipos:
        filtrado = filtrado[filtrado["tipo_servico"].isin(tipos)]
    if prioridades:
        filtrado = filtrado[filtrado["prioridade"].isin(prioridades)]

    total = len(filtrado)
    abertos = (filtrado["status"] == "ABERTO").sum()
    andamento = (filtrado["status"] == "EM ANDAMENTO").sum()
    concluidos = (filtrado["status"] == "CONCLUÍDO").sum()
    taxa = (concluidos / total * 100) if total else 0.0

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total", total)
    m2.metric("Abertos", abertos)
    m3.metric("Em andamento", andamento)
    m4.metric("Concluídos", concluidos)
    m5.metric("Taxa de conclusão", f"{taxa:.1f}%")

    st.subheader("Chamados em aberto")
    pendentes = filtrado[filtrado["status"].isin(["ABERTO", "EM ANDAMENTO"])]
    if pendentes.empty:
        st.success("Nenhum chamado pendente nos filtros atuais.")
    else:
        st.dataframe(pendentes[_COLUNAS_CHAMADOS], use_container_width=True, hide_index=True)

    col_graf1, col_graf2 = st.columns(2)
    with col_graf1:
        status_counts = filtrado["status"].value_counts().reset_index()
        status_counts.columns = ["status", "quantidade"]
        st.plotly_chart(
            px.pie(status_counts, names="status", values="quantidade", title="Por status"),
            use_container_width=True,
        )
    with col_graf2:
        tipo_counts = filtrado["tipo_servico"].value_counts().reset_index()
        tipo_counts.columns = ["tipo_servico", "quantidade"]
        st.plotly_chart(
            px.bar(tipo_counts, x="tipo_servico", y="quantidade", title="Por tipo de serviço"),
            use_container_width=True,
        )

    st.subheader("Tabela detalhada")
    st.dataframe(filtrado[_COLUNAS_CHAMADOS + ["espera_dias", "execucao_dias", "observacoes"]], use_container_width=True, hide_index=True)
    _botao_csv(filtrado, "chamados_cap_filtrado.csv")


_COLUNAS_EXTINTORES = [
    "unidade",
    "tipo_item",
    "tipo",
    "capacidade",
    "validade",
    "dias_vencer",
    "status",
    "localizacao",
]


def render_extintores(df: pd.DataFrame) -> None:
    render_cabecalho("Controle de Extintores — AP 5.1")

    c1, c2, c3 = st.columns(3)
    with c1:
        unidades = _filtro_popover("Unidade", sorted(df["unidade"].unique()), "filtro_ext_u")
    with c2:
        tipos = _filtro_popover("Tipo de item", sorted(df["tipo_item"].unique()), "filtro_ext_t")
    with c3:
        status = _filtro_popover("Status", sorted(df["status"].unique()), "filtro_ext_s")

    filtrado = df.copy()
    if unidades:
        filtrado = filtrado[filtrado["unidade"].isin(unidades)]
    if tipos:
        filtrado = filtrado[filtrado["tipo_item"].isin(tipos)]
    if status:
        filtrado = filtrado[filtrado["status"].isin(status)]

    ext = filtrado[filtrado["tipo_item"] == "Extintor"]
    total = len(ext)
    validos = ext["status"].isin(["VÁLIDO", "OK"]).sum()
    atencao = (ext["status"] == "ATENÇÃO").sum()
    vencidos = (ext["status"] == "VENCIDO").sum()

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Extintores", total)
    m2.metric("Válidos", validos)
    m3.metric("Atenção", atencao)
    m4.metric("Vencidos", vencidos)
    m5.metric("Unidades", filtrado["unidade"].nunique())

    st.subheader("Itens críticos")
    criticos = filtrado[filtrado["status"].isin(["VENCIDO", "ATENÇÃO", "COM VENCIDOS"])]
    if criticos.empty:
        st.success("Nenhum item crítico nos filtros atuais.")
    else:
        st.dataframe(criticos[_COLUNAS_EXTINTORES], use_container_width=True, hide_index=True)

    col_graf1, col_graf2 = st.columns(2)
    with col_graf1:
        status_counts = ext["status"].value_counts().reset_index()
        status_counts.columns = ["status", "quantidade"]
        st.plotly_chart(
            px.pie(status_counts, names="status", values="quantidade", title="Extintores por status"),
            use_container_width=True,
        )
    with col_graf2:
        por_unidade = ext.groupby("unidade").size().reset_index(name="quantidade").sort_values("quantidade", ascending=False)
        st.plotly_chart(
            px.bar(por_unidade.head(15), x="unidade", y="quantidade", title="Extintores por unidade"),
            use_container_width=True,
        )

    st.subheader("Tabela detalhada")
    st.dataframe(filtrado[_COLUNAS_EXTINTORES + ["observacao"]], use_container_width=True, hide_index=True)
    _botao_csv(filtrado, "extintores_filtrado.csv")


_COLUNAS_EQUIPAMENTOS = [
    "unidade",
    "tipo_equipamento",
    "marca",
    "modelo",
    "serie",
    "status",
    "atualizado_em",
    "observacao",
]

_STATUS_EQUIP_OK = {"OPERANTE", "EMPRESTADO", "DISPONÍVEL"}
_STATUS_EQUIP_CRITICO = {"CONDENADO", "PARCIAL OU INOPERANTE", "INOPERANTE"}


def render_equipamentos_prioritarios(df: pd.DataFrame) -> None:
    _render_painel_equipamentos(
        df,
        "Equipamentos Prioritários — AP 5.1",
        _STATUS_EQUIP_OK,
        _STATUS_EQUIP_CRITICO,
        _COLUNAS_EQUIPAMENTOS,
        "equipamentos_prioritarios_filtrado.csv",
        filtro_tipo_key="filtro_eq_tipo",
        coluna_tipo="tipo_equipamento",
    )


_COLUNAS_ODONTO = [
    "unidade",
    "tipo_equipamento",
    "marca",
    "modelo",
    "serie",
    "status",
    "atualizado_em",
    "observacao",
]


def render_odonto(df: pd.DataFrame) -> None:
    _render_painel_equipamentos(
        df,
        "Odonto — Equipamentos Prioritários — AP 5.1",
        _STATUS_EQUIP_OK,
        _STATUS_EQUIP_CRITICO | {"CONDENADO"},
        _COLUNAS_ODONTO,
        "odonto_filtrado.csv",
        filtro_tipo_key="filtro_od_tipo",
        coluna_tipo="tipo_equipamento",
    )


_COLUNAS_FALTA_ENERGIA = [
    "unidade",
    "data_chamado",
    "empresa",
    "protocolo",
    "data_conclusao",
    "status",
    "tempo_conclusao_horas",
]


def render_falta_energia(df: pd.DataFrame) -> None:
    render_cabecalho("Falta de Energia — AP 5.1")

    c1, c2 = st.columns(2)
    with c1:
        unidades = _filtro_popover("Unidade", sorted(df["unidade"].unique()), "filtro_fe_u")
    with c2:
        status = _filtro_popover("Status", sorted(df["status"].unique()), "filtro_fe_s")

    filtrado = df.copy()
    if unidades:
        filtrado = filtrado[filtrado["unidade"].isin(unidades)]
    if status:
        filtrado = filtrado[filtrado["status"].isin(status)]

    total = len(filtrado)
    concluidos = (filtrado["status"] == "CONCLUÍDO").sum()
    tempo_medio = filtrado["tempo_conclusao_horas"].dropna().mean()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Ocorrências", total)
    m2.metric("Unidades afetadas", filtrado["unidade"].nunique())
    m3.metric("Concluídas", concluidos)
    m4.metric("Tempo médio (h)", f"{tempo_medio:.1f}" if pd.notna(tempo_medio) else "—")

    st.subheader("Ocorrências recentes")
    st.dataframe(
        filtrado.sort_values("data_chamado", ascending=False)[_COLUNAS_FALTA_ENERGIA],
        use_container_width=True,
        hide_index=True,
    )

    col_graf1, col_graf2 = st.columns(2)
    with col_graf1:
        por_mes = filtrado.assign(mes=filtrado["data_chamado"].dt.to_period("M").astype(str))
        mes_counts = por_mes.groupby("mes").size().reset_index(name="quantidade")
        st.plotly_chart(px.bar(mes_counts, x="mes", y="quantidade", title="Ocorrências por mês"), use_container_width=True)
    with col_graf2:
        unidade_counts = filtrado["unidade"].value_counts().head(10).reset_index()
        unidade_counts.columns = ["unidade", "quantidade"]
        st.plotly_chart(px.bar(unidade_counts, x="unidade", y="quantidade", title="Top unidades"), use_container_width=True)

    _botao_csv(filtrado, "falta_energia_filtrado.csv")


_COLUNAS_FALTA_AGUA = [
    "unidade",
    "data_chamado",
    "empresa",
    "litros",
    "carro_pipa_entregue",
    "data_conclusao",
    "status",
]


def render_falta_agua(df: pd.DataFrame) -> None:
    render_cabecalho("Falta de Água — AP 5.1")

    c1, c2 = st.columns(2)
    with c1:
        unidades = _filtro_popover("Unidade", sorted(df["unidade"].unique()), "filtro_fa_u")
    with c2:
        status = _filtro_popover("Status", sorted(df["status"].unique()), "filtro_fa_s")

    filtrado = df.copy()
    if unidades:
        filtrado = filtrado[filtrado["unidade"].isin(unidades)]
    if status:
        filtrado = filtrado[filtrado["status"].isin(status)]

    total = len(filtrado)
    concluidos = (filtrado["status"] == "CONCLUÍDO").sum()
    com_pipa = (filtrado["precisou_carro_pipa"]).sum()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Ocorrências", total)
    m2.metric("Unidades afetadas", filtrado["unidade"].nunique())
    m3.metric("Concluídas", concluidos)
    m4.metric("Com carro-pipa", com_pipa)

    st.subheader("Ocorrências recentes")
    st.dataframe(
        filtrado.sort_values("data_chamado", ascending=False)[_COLUNAS_FALTA_AGUA],
        use_container_width=True,
        hide_index=True,
    )

    col_graf1, col_graf2 = st.columns(2)
    with col_graf1:
        status_counts = filtrado["status"].value_counts().reset_index()
        status_counts.columns = ["status", "quantidade"]
        st.plotly_chart(px.pie(status_counts, names="status", values="quantidade", title="Por status"), use_container_width=True)
    with col_graf2:
        empresa_counts = filtrado["empresa"].value_counts().reset_index()
        empresa_counts.columns = ["empresa", "quantidade"]
        st.plotly_chart(px.bar(empresa_counts, x="empresa", y="quantidade", title="Por empresa"), use_container_width=True)

    _botao_csv(filtrado, "falta_agua_filtrado.csv")
