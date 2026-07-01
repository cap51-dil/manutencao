"""Cleaner da planilha FALTA DE ÁGUA — serviço Manutenção (aba ÁGUA 2026)."""

from __future__ import annotations

import io

import pandas as pd

from utils.excel import ler_aba, validar

ABA = "ÁGUA 2026"
LINHA_CABECALHO = 1

COLUNAS_OBRIGATORIAS = ["unidade", "data_chamado", "status"]

STATUS_VALIDOS = {"CONCLUÍDO", "EM ANDAMENTO", "ABERTO", "CANCELADO"}

_RENOMEAR = {
    "UNIDADE": "unidade",
    "SOLICITADO POR ": "solicitado_por",
    "DATA DO CHAMADO": "data_chamado",
    "EMPRESA CONTACTADA": "empresa",
    "PRECISOU DE CARRO PIPA": "precisou_carro_pipa",
    "Nº DE PROTOCOLO": "protocolo",
    "Nº ORDEM DE SERVIÇO": "ordem_servico",
    "LITROS": "litros",
    "SOLICITAÇÃO DO COR": "solicitacao_cor",
    "DATA DE CONCLUSÃO": "data_conclusao",
    "CARRO PIPA ENTREGUE": "carro_pipa_entregue",
    "STATUS DO SERVIÇO": "status",
}

_COLUNAS_FINAIS = [
    "unidade",
    "solicitado_por",
    "data_chamado",
    "empresa",
    "precisou_carro_pipa",
    "protocolo",
    "ordem_servico",
    "litros",
    "solicitacao_cor",
    "data_conclusao",
    "carro_pipa_entregue",
    "status",
]


def limpar(conteudo: bytes) -> pd.DataFrame:
    buffer = io.BytesIO(conteudo)
    df = ler_aba(buffer, ABA, LINHA_CABECALHO)

    df = df.rename(columns=_RENOMEAR)
    df = df.drop(columns=[c for c in df.columns if str(c).startswith("Unnamed")], errors="ignore")
    df = df[df["unidade"].notna()].copy()

    for col in ("data_chamado", "data_conclusao"):
        df[col] = pd.to_datetime(df[col], errors="coerce")

    for col in ("precisou_carro_pipa", "solicitacao_cor"):
        df[col] = df[col].fillna(False).astype(bool)

    df["carro_pipa_entregue"] = (
        df["carro_pipa_entregue"].fillna("").astype(str).str.strip().str.upper()
    )
    df["status"] = df["status"].astype(str).str.strip().str.upper()
    df["empresa"] = df["empresa"].astype(str).str.strip()
    df["solicitado_por"] = df["solicitado_por"].astype(str).str.strip()
    df["litros"] = df["litros"].astype(str).str.strip()

    df = df[_COLUNAS_FINAIS].reset_index(drop=True)
    validar(df, COLUNAS_OBRIGATORIAS, STATUS_VALIDOS)
    return df
