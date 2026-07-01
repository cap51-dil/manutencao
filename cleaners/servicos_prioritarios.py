"""Cleaner da planilha SERVIÇOS PRIORITÁRIOS — serviço Manutenção (aba BASE_DADOS)."""

from __future__ import annotations

import io

import pandas as pd

from utils.excel import ler_aba, validar

ABA = "BASE_DADOS"
LINHA_CABECALHO = 1

COLUNAS_OBRIGATORIAS = ["unidade", "servico", "status", "grupo_status"]

GRUPOS_STATUS_VALIDOS = {
    "OK / Realizado",
    "Pendente",
    "Atenção",
    "Vencido",
    "Sem status",
}

_RENOMEAR = {
    "Unidade": "unidade",
    "Responsável / E-mail": "responsavel_email",
    "Serviço": "servico",
    "Detalhe do Serviço": "detalhe",
    "Data Referência": "data_referencia",
    "Data Execução / Vencimento / Prazo": "data_execucao",
    "Status": "status",
    "Grupo Status": "grupo_status",
    "Observação": "observacao",
    "Aba Origem": "aba_origem",
    "Linha Origem": "linha_origem",
    "Ativo": "ativo",
}

_COLUNAS_FINAIS = [
    "unidade",
    "responsavel_email",
    "servico",
    "detalhe",
    "data_referencia",
    "data_execucao",
    "status",
    "grupo_status",
    "observacao",
    "aba_origem",
    "linha_origem",
    "ativo",
]


def limpar(conteudo: bytes) -> pd.DataFrame:
    buffer = io.BytesIO(conteudo)
    df = ler_aba(buffer, ABA, LINHA_CABECALHO)

    df = df.rename(columns=_RENOMEAR)
    df = df.drop(columns=[c for c in df.columns if str(c).startswith("Unnamed")], errors="ignore")

    df["unidade"] = df["unidade"].astype(str).str.strip()
    df = df[df["unidade"].notna() & (df["unidade"] != "") & (df["unidade"] != "nan")]

    mask_ativo = df["ativo"].fillna("").astype(str).str.strip().str.upper() == "SIM"
    df = df[mask_ativo].copy()

    for col in ("data_referencia", "data_execucao"):
        df[col] = pd.to_datetime(df[col], errors="coerce")

    df["status"] = df["status"].astype(str).str.strip()
    df["grupo_status"] = df["grupo_status"].astype(str).str.strip()
    df["servico"] = df["servico"].astype(str).str.strip()
    df["linha_origem"] = pd.to_numeric(df["linha_origem"], errors="coerce")

    df = df[_COLUNAS_FINAIS]
    df = df.reset_index(drop=True)

    validar(
        df,
        COLUNAS_OBRIGATORIAS,
        GRUPOS_STATUS_VALIDOS,
        coluna_status="grupo_status",
    )
    return df
