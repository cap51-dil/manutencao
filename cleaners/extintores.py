"""Cleaner da planilha Controle de Extintores — serviço Manutenção."""

from __future__ import annotations

import io
import re
import unicodedata

import pandas as pd

from utils.excel import ler_aba, validar

ABA_EXTINTORES = "🧯 Extintores"
ABA_HIDRANTES = "🚿 Hidrantes"
LINHA_CABECALHO = 2

COLUNAS_OBRIGATORIAS = ["unidade", "tipo_item", "status"]

STATUS_VALIDOS = {"VÁLIDO", "ATENÇÃO", "VENCIDO", "OK", "COM VENCIDOS", "REGULAR", "SEM HIDRANTES"}

_RENOMEAR_EXTINTOR = {
    "UNIDADE DE SAÚDE": "unidade",
    "TIPO": "tipo",
    "CAPACIDADE": "capacidade",
    "DATA DE RECARGA": "data_recarga",
    "VALIDADE": "validade",
    "DIAS P/ VENCER": "dias_vencer",
    "STATUS": "status",
    "LOCALIZAÇÃO": "localizacao",
    "OBSERVAÇÃO": "observacao",
    "Nº REGISTRO": "num_registro",
}

_RENOMEAR_HIDRANTE = {
    "UNIDADE DE SAÚDE": "unidade",
    "HIDRANTE": "hidrante",
    "MANGUEIRAS": "mangueiras",
    "ESGUICHOS": "esguichos",
    "CHAVES STORZ": "chaves_storz",
    "DATA TESTE HIDROSTÁTICO": "data_teste",
    "SITUAÇÃO": "status",
}


def _normalizar_status(texto: str) -> str:
    if texto is None or (isinstance(texto, float) and pd.isna(texto)):
        return "SEM STATUS"
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"[^\w\s/]", "", texto.upper())
    texto = re.sub(r"\s+", " ", texto).strip()
    mapa = {
        "VALIDO": "VÁLIDO",
        "ATENCAO": "ATENÇÃO",
        "VENCIDO": "VENCIDO",
        "OK": "OK",
        "COM VENCIDOS": "COM VENCIDOS",
        "REGULAR": "REGULAR",
        "NAO HA HIDRANTES": "SEM HIDRANTES",
        "SEM STATUS": "SEM STATUS",
    }
    return mapa.get(texto, texto)


def _limpar_extintores(conteudo: bytes) -> pd.DataFrame:
    buffer = io.BytesIO(conteudo)
    df = ler_aba(buffer, ABA_EXTINTORES, LINHA_CABECALHO)
    df = df.rename(columns=_RENOMEAR_EXTINTOR)
    df = df.drop(columns=[c for c in df.columns if str(c).startswith("Unnamed")], errors="ignore")
    df = df[df["unidade"].notna()].copy()
    df["tipo_item"] = "Extintor"
    df["status"] = df["status"].apply(_normalizar_status)
    for col in ("data_recarga", "validade"):
        df[col] = pd.to_datetime(df[col], errors="coerce")
    df["dias_vencer"] = pd.to_numeric(df["dias_vencer"], errors="coerce")
    df["num_registro"] = pd.to_numeric(df["num_registro"], errors="coerce")
    return df


def _limpar_hidrantes(conteudo: bytes) -> pd.DataFrame:
    buffer = io.BytesIO(conteudo)
    df = ler_aba(buffer, ABA_HIDRANTES, LINHA_CABECALHO)
    df = df.rename(columns=_RENOMEAR_HIDRANTE)
    df = df.drop(columns=[c for c in df.columns if str(c).startswith("Unnamed")], errors="ignore")
    df = df[df["unidade"].notna()].copy()
    df["tipo_item"] = "Hidrante"
    df["status"] = df["status"].apply(_normalizar_status)
    df["data_teste"] = pd.to_datetime(df["data_teste"], errors="coerce")
    return df


def limpar(conteudo: bytes) -> pd.DataFrame:
    ext = _limpar_extintores(conteudo)
    hid = _limpar_hidrantes(conteudo)

    colunas = [
        "unidade",
        "tipo_item",
        "tipo",
        "capacidade",
        "data_recarga",
        "validade",
        "dias_vencer",
        "status",
        "localizacao",
        "observacao",
        "num_registro",
        "hidrante",
        "mangueiras",
        "esguichos",
        "chaves_storz",
        "data_teste",
    ]
    df = pd.concat([ext, hid], ignore_index=True)
    for col in colunas:
        if col not in df.columns:
            df[col] = None
    df = df[colunas].reset_index(drop=True)
    df = df[df["status"] != "SEM STATUS"].copy()

    validar(df, COLUNAS_OBRIGATORIAS, STATUS_VALIDOS)
    return df
