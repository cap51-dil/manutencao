"""Leitura de planilhas no Google Drive via service account."""

from __future__ import annotations

import io
import unicodedata
from typing import Any

import httplib2
from google.oauth2 import service_account
from google_auth_httplib2 import AuthorizedHttp
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
TIMEOUT_SEGUNDOS = 60

MIME_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
MIME_GSHEET = "application/vnd.google-apps.spreadsheet"
MIME_SHORTCUT = "application/vnd.google-apps.shortcut"
MIME_PLANILHAS = (MIME_XLSX, MIME_GSHEET)


def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c)).lower()


def _criar_servico(credenciais: dict[str, Any]):
    from utils.gcp import normalizar_credenciais_gcp

    creds = normalizar_credenciais_gcp(credenciais)
    credentials = service_account.Credentials.from_service_account_info(creds, scopes=SCOPES)
    http = AuthorizedHttp(credentials, http=httplib2.Http(timeout=TIMEOUT_SEGUNDOS))
    return build("drive", "v3", http=http, cache_discovery=False)


def _resolver_atalho(servico, arquivo: dict) -> dict | None:
    if arquivo["mimeType"] != MIME_SHORTCUT:
        return arquivo

    detalhes = arquivo.get("shortcutDetails") or {}
    alvo_id = detalhes.get("targetId")
    alvo_mime = detalhes.get("targetMimeType")
    if not alvo_id or alvo_mime not in MIME_PLANILHAS:
        return None

    alvo = (
        servico.files()
        .get(fileId=alvo_id, fields="modifiedTime")
        .execute()
    )
    return {
        "id": alvo_id,
        "name": arquivo["name"],
        "mimeType": alvo_mime,
        "modifiedTime": alvo["modifiedTime"],
    }


def listar_planilhas(servico, folder_id: str) -> list[dict]:
    tipos = " or ".join(f"mimeType = '{mime}'" for mime in (*MIME_PLANILHAS, MIME_SHORTCUT))
    query = f"'{folder_id}' in parents and trashed = false and ({tipos})"
    resultados = []
    page_token = None
    while True:
        resposta = (
            servico.files()
            .list(
                q=query,
                fields=(
                    "nextPageToken, "
                    "files(id, name, mimeType, modifiedTime, shortcutDetails)"
                ),
                pageToken=page_token,
            )
            .execute()
        )
        for arquivo in resposta.get("files", []):
            resolvido = _resolver_atalho(servico, arquivo)
            if resolvido:
                resultados.append(resolvido)
        page_token = resposta.get("nextPageToken")
        if not page_token:
            break
    return resultados


def selecionar_arquivo(arquivos: list[dict], padrao_nome: str | None = None) -> dict:
    if not arquivos:
        raise FileNotFoundError("Nenhuma planilha encontrada na pasta do Drive.")

    candidatos = arquivos
    if padrao_nome:
        padrao = _normalizar(padrao_nome)
        filtrados = [a for a in arquivos if padrao in _normalizar(a["name"])]
        if filtrados:
            candidatos = filtrados

    if len(candidatos) > 1 and padrao_nome:
        padrao = _normalizar(padrao_nome)
        prefixo = [a for a in candidatos if _normalizar(a["name"]).startswith(padrao)]
        if prefixo:
            candidatos = prefixo
        menor_len = min(len(a["name"]) for a in candidatos)
        candidatos = [a for a in candidatos if len(a["name"]) == menor_len]

    return sorted(candidatos, key=lambda a: a["modifiedTime"], reverse=True)[0]


def baixar_arquivo(servico, arquivo: dict) -> bytes:
    buffer = io.BytesIO()
    if arquivo["mimeType"] == MIME_GSHEET:
        request = servico.files().export_media(fileId=arquivo["id"], mimeType=MIME_XLSX)
    else:
        request = servico.files().get_media(fileId=arquivo["id"])

    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()

    buffer.seek(0)
    return buffer.read()


def carregar_planilha(
    credenciais: dict[str, Any],
    folder_id: str,
    padrao_nome: str | None = None,
) -> tuple[bytes, dict]:
    """
    Retorna (conteudo_xlsx, metadados).
    metadados: nome, modificado_em, file_id
    """
    servico = _criar_servico(credenciais)
    arquivos = listar_planilhas(servico, folder_id)
    arquivo = selecionar_arquivo(arquivos, padrao_nome)
    conteudo = baixar_arquivo(servico, arquivo)
    meta = {
        "nome": arquivo["name"],
        "modificado_em": arquivo["modifiedTime"],
        "file_id": arquivo["id"],
    }
    return conteudo, meta
