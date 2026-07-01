"""Cleaner da planilha CHAMADOS CAP — serviço Manutenção."""

from __future__ import annotations

import io

import pandas as pd

from utils.excel import ler_aba, validar

ABA = "Controle de Chamados"
LINHA_CABECALHO = 5

COLUNAS_OBRIGATORIAS = ["numero", "data_abertura", "empresa", "tipo_servico", "setor", "status"]

STATUS_VALIDOS = {"CONCLUÍDO", "EM ANDAMENTO", "ABERTO", "CANCELADO"}

_RENOMEAR = {
    "Nº": "numero",
    "Data\nAbertura *": "data_abertura",
    "Empresa *": "empresa",
    "Tipo de Serviço *": "tipo_servico",
    "Setor *": "setor",
    "Descrição": "descricao",
    "Status *": "status",
    "Prioridade": "prioridade",
    "Data\nRealização": "data_realizacao",
    "Espera\n(dias)": "espera_dias",
    "Execução\n(dias)": "execucao_dias",
    "Observações": "observacoes",
}

_COLUNAS_FINAIS = [
    "numero",
    "data_abertura",
    "empresa",
    "tipo_servico",
    "setor",
    "descricao",
    "status",
    "prioridade",
    "data_realizacao",
    "espera_dias",
    "execucao_dias",
    "observacoes",
]


def limpar(conteudo: bytes) -> pd.DataFrame:
    buffer = io.BytesIO(conteudo)
    df = ler_aba(buffer, ABA, LINHA_CABECALHO)

    df = df.rename(columns=_RENOMEAR)
    df = df.drop(columns=[c for c in df.columns if str(c).startswith("Unnamed")], errors="ignore")

    df = df[df["numero"].notna() & df["empresa"].notna() & df["status"].notna()].copy()
    df["numero"] = pd.to_numeric(df["numero"], errors="coerce")
    df = df[df["numero"].notna()]

    for col in ("data_abertura", "data_realizacao"):
        df[col] = pd.to_datetime(df[col], errors="coerce")
    for col in ("espera_dias", "execucao_dias"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ("empresa", "tipo_servico", "setor", "descricao", "status", "prioridade", "observacoes"):
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace({"nan": None, "None": None})

    df = df[_COLUNAS_FINAIS].reset_index(drop=True)
    validar(df, COLUNAS_OBRIGATORIAS, STATUS_VALIDOS)
    return df
