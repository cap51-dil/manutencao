"""Cabeçalho e estilos institucionais — PCRJ Saúde / SUS."""

from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

_ASSETS = Path("assets")

_LOGOS = {
    "gradiente": _ASSETS / "logo_pcrj_gradiente.png",
    "azul": _ASSETS / "logo_pcrj_azul.png",
    "branco": _ASSETS / "logo_pcrj_branco.png",
    "preto": _ASSETS / "logo_pcrj_preto.png",
}

_CORES = {
    "azul_escuro": "#102035",
    "azul_rio": "#1A3050",
    "azul_sus": "#0056B3",
    "azul_claro": "#EEF4FB",
    "azul_accent": "#4EB3E5",
}


def injetar_estilos() -> None:
    st.markdown(
        f"""
        <style>
            [data-testid="stSidebar"] {{
                background-color: {_CORES["azul_claro"]};
            }}
            [data-testid="stSidebar"] [data-testid="stMarkdown"] h1,
            [data-testid="stSidebar"] [data-testid="stMarkdown"] h2,
            [data-testid="stSidebar"] [data-testid="stMarkdown"] h3 {{
                color: {_CORES["azul_escuro"]};
            }}
            div[data-testid="stMetric"] {{
                background: white;
                border-left: 4px solid {_CORES["azul_sus"]};
                border-radius: 6px;
                padding: 0.75rem 1rem;
                box-shadow: 0 1px 3px rgba(16, 32, 53, 0.08);
            }}
            div[data-testid="stMetric"] label {{
                color: {_CORES["azul_rio"]} !important;
            }}
            div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
                color: {_CORES["azul_escuro"]};
            }}
            .faixa-pcrj {{
                background: {_CORES["azul_escuro"]};
                margin: -1rem -1rem 1.25rem -1rem;
                padding: 1rem 1.5rem 1.1rem 1.5rem;
                border-bottom: 3px solid {_CORES["azul_sus"]};
            }}
            .faixa-pcrj.clara {{
                background: white;
                border-bottom: 3px solid {_CORES["azul_sus"]};
            }}
            .faixa-pcrj:not(.clara) img {{
                height: 52px;
                width: auto;
                display: block;
                mix-blend-mode: lighten;
            }}
            .faixa-pcrj.clara img {{
                height: 52px;
                width: auto;
                display: block;
            }}
            .faixa-pcrj .titulo-pagina {{
                color: white;
                font-size: 1.2rem;
                font-weight: 600;
                margin: 0.85rem 0 0 0;
                line-height: 1.3;
            }}
            .faixa-pcrj.clara .titulo-pagina {{
                color: {_CORES["azul_escuro"]};
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _resolver_logo() -> tuple[Path, str]:
    branding = dict(st.secrets.get("branding", {}))
    variante = str(branding.get("logo", "branco")).lower()
    caminho = _LOGOS.get(variante, _LOGOS["branco"])
    if not caminho.exists():
        for fallback in _LOGOS.values():
            if fallback.exists():
                return fallback, "branco"
        raise FileNotFoundError("Nenhuma logo PCRJ encontrada em assets/")
    return caminho, variante


def render_cabecalho(titulo: str) -> None:
    logo, variante = _resolver_logo()
    mime = "image/png" if logo.suffix.lower() == ".png" else "image/jpeg"
    b64 = base64.b64encode(logo.read_bytes()).decode()
    img_tag = f'<img src="data:{mime};base64,{b64}" alt="Prefeitura do Rio — Saúde / SUS" />'

    faixa_clara = variante == "preto"
    classe_faixa = "faixa-pcrj clara" if faixa_clara else "faixa-pcrj"

    st.markdown(
        f"""
        <div class="{classe_faixa}">
            {img_tag}
            <p class="titulo-pagina">{titulo}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
