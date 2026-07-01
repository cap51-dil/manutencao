"""Cleaner da planilha STATUS CÂMARAS DE VACINA — setor Manutenção."""

from __future__ import annotations

from typing import Optional

import pandas as pd

from utils.excel import desmesclar_planilha, ler_aba, validar

ABA = "STATUS CÂMARAS"
LINHA_CABECALHO = 2

COLUNAS_OBRIGATORIAS = ["unidade", "marca", "status", "modelo", "serie"]

STATUS_VALIDOS = {
    "Operacional",
    "Inoperante",
    "Operacional c/ restrição",
    "Condenado",
}

_RENOMEAR = {
    "UNIDADE": "unidade",
    "MARCA": "marca",
    "STATUS DE \n FUNCIONAMENTO": "status",
    "MODELO": "modelo",
    "SÉRIE": "serie",
    "PROBLEMA": "problema",
    "DATA DA OCORRÊNCIA": "data_ocorrencia",
    "AVALIADA": "avaliada",
    "ABERTURA DA OS": "abertura_os",
    "N° DA OS": "num_os",
    "CHAMADO GLPI": "chamado_glpi",
    "PEÇAS SOLICITADAS": "pecas_solicitadas",
    "OBSERÇÃO": "observacao",
    "SISBENS": "sisbens",
    "ÓRGÃO": "orgao",
}

_COLUNAS_FINAIS = [
    "unidade",
    "marca",
    "status",
    "modelo",
    "serie",
    "problema",
    "data_ocorrencia",
    "avaliada",
    "abertura_os",
    "num_os",
    "chamado_glpi",
    "pecas_solicitadas",
    "observacao",
    "sisbens",
    "orgao",
]


def _como_texto(valor) -> Optional[str]:
    if pd.isna(valor):
        return None
    texto = str(valor).strip()
    if texto.endswith(".0") and texto.replace(".", "").isdigit():
        texto = texto[:-2]
    return texto or None


def limpar(conteudo: bytes) -> pd.DataFrame:
    buffer = desmesclar_planilha(conteudo, ABA)
    df = ler_aba(buffer, ABA, LINHA_CABECALHO)

    df = df.rename(columns=_RENOMEAR)
    df = df.drop(columns=[c for c in df.columns if str(c).startswith("Unnamed")], errors="ignore")
    df = df.drop(columns=["TOTAL"], errors="ignore")

    df["unidade"] = df["unidade"].ffill()
    df["marca"] = df["marca"].ffill()

    mask_total = df["unidade"].astype(str).str.contains("Total", case=False, na=False)
    mask_sem_status = df["status"].isna()
    df = df[~mask_total & ~mask_sem_status].copy()

    df["data_ocorrencia"] = pd.to_datetime(df["data_ocorrencia"], errors="coerce")
    df["abertura_os"] = pd.to_datetime(df["abertura_os"], errors="coerce")
    df["avaliada"] = df["avaliada"].fillna(False).astype(bool)
    df["serie"] = df["serie"].astype(str).str.replace(r"\.0$", "", regex=True)
    df["num_os"] = df["num_os"].apply(_como_texto)
    df["chamado_glpi"] = df["chamado_glpi"].apply(_como_texto)

    df = df[_COLUNAS_FINAIS]
    df = df.reset_index(drop=True)

    validar(df, COLUNAS_OBRIGATORIAS, STATUS_VALIDOS)
    return df
