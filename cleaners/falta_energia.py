"""Cleaner da planilha FALTA DE ENERGIA — serviço Manutenção (aba LUZ)."""

from __future__ import annotations

import io

import pandas as pd

from utils.excel import ler_aba, validar

ABA = "LUZ"
LINHA_CABECALHO = 1

COLUNAS_OBRIGATORIAS = ["unidade", "data_chamado", "status"]

STATUS_VALIDOS = {"CONCLUÍDO", "EM ANDAMENTO", "ABERTO", "CANCELADO"}

_RENOMEAR = {
    "UNIDADE": "unidade",
    "DATA DO CHAMADO": "data_chamado",
    "EMPRESA CONTACTADA": "empresa",
    "Nº DE PROTOCOLO": "protocolo",
    "SOLICITAÇÃO DO COR": "solicitacao_cor",
    "DATA DE CONCLUSÃO": "data_conclusao",
    "STATUS DO SERVIÇO": "status",
    "TEMPO PARA CONCLUSÃO": "tempo_conclusao",
}

_COLUNAS_FINAIS = [
    "unidade",
    "data_chamado",
    "empresa",
    "protocolo",
    "solicitacao_cor",
    "data_conclusao",
    "status",
    "tempo_conclusao_horas",
]


def _timedelta_horas(valor) -> float | None:
    if pd.isna(valor):
        return None
    if hasattr(valor, "total_seconds"):
        return round(valor.total_seconds() / 3600, 2)
    return None


def limpar(conteudo: bytes) -> pd.DataFrame:
    buffer = io.BytesIO(conteudo)
    df = ler_aba(buffer, ABA, LINHA_CABECALHO)

    df = df.rename(columns=_RENOMEAR)
    df = df.drop(columns=[c for c in df.columns if str(c).startswith("Unnamed")], errors="ignore")
    df = df[df["unidade"].notna()].copy()

    for col in ("data_chamado", "data_conclusao"):
        df[col] = pd.to_datetime(df[col], errors="coerce")

    df["solicitacao_cor"] = df["solicitacao_cor"].fillna(False).astype(bool)
    df["tempo_conclusao_horas"] = df["tempo_conclusao"].apply(_timedelta_horas)
    df["status"] = df["status"].astype(str).str.strip().str.upper()
    df["empresa"] = df["empresa"].astype(str).str.strip()
    df["protocolo"] = df["protocolo"].astype(str).str.strip().replace({"nan": None})

    df = df[_COLUNAS_FINAIS].reset_index(drop=True)
    validar(df, COLUNAS_OBRIGATORIAS, STATUS_VALIDOS)
    return df
