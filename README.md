# Plataforma de Dados — APS 5.1

ELT automatizado: planilhas no Google Drive → tratamento (Python) → painel Streamlit.
As pessoas só encostam em dois pontos: **sobem planilha no Drive** e **abrem a URL do painel**.

```
Pastas por setor no Drive ──(service account, leitura)──▶ Streamlit
   • cada setor tem sua pasta                               • lê + limpa (cacheado)
   • pessoas largam a planilha lá                           • botão "Atualizar dados"
                                                            • app privado (allow-list)
```

---

## Estrutura

```
manutencao/
├── app.py                       # painel (entrypoint)
├── utils/
│   ├── drive.py                 # leitura do Drive via service account
│   ├── excel.py                 # desmescla, leitura de aba, validação
│   ├── clean.py                 # dispatcher por setor
│   └── dashboard.py             # KPIs, filtros e gráficos
├── cleaners/
│   └── camaras_vacina.py        # limpeza — Manutenção / Câmaras de Vacina
├── requirements.txt
├── .gitignore
└── .streamlit/
    ├── config.toml
    └── secrets.toml.example
```

---

## Setor POC

| Item | Valor |
|------|-------|
| Setor | `Manutenção — Câmaras de Vacina` |
| Pasta Drive | `1EAp-v4dyjxdmaEP4c85hxVCQsRH6Og09` |
| Padrão do arquivo | `STATUS CÂMARAS DE VACINA` |

---

## Passo a passo

> Os passos com 🔑 envolvem credenciais — **você** faz no console do Google / Streamlit.
> O arquivo `secrets.toml` é seu e fica fora do git.

### 1. 🔑 Service account (Google Cloud)

1. Acesse <https://console.cloud.google.com>
2. Crie um projeto e ative a **Google Drive API**
3. Crie uma **conta de serviço** e baixe a chave JSON
4. Compartilhe cada pasta de setor com o e-mail da service account como **Leitor**

### 2. Rodar localmente

```bash
cd manutencao
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# preencha [gcp_service_account], [setores] e [arquivos]

streamlit run app.py
```

**Modo dev (sem Drive):** marque **"Usar planilha local"** na sidebar. Coloque o `.xlsx` na raiz do projeto.

### 3. Calibrar um novo setor

Para cada nova área:

1. Crie `cleaners/<setor>.py` com `limpar(conteudo: bytes) -> DataFrame`
2. Registre em `utils/clean.py` → `CLEANERS`
3. Adicione `render_<setor>()` em `utils/dashboard.py`
4. Inclua pasta e padrão de arquivo em `secrets.toml` (`[setores]` e `[arquivos]`)

Use `validar()` em `utils/excel.py` para travar cedo se a planilha sair do contrato.

### 4. 🔑 Publicar no Streamlit Community Cloud

1. Suba o projeto no GitHub (`cap51-dil/manutencao`)
2. Acesse <https://share.streamlit.io> → Deploy → `app.py`
3. Em **Settings → Secrets**, cole o conteúdo do `secrets.toml`
4. Deixe o app **privado** e cadastre e-mails na allow-list

---

## Governança

- Pasta-fonte e projeto GCP numa conta institucional quando possível
- Pelo menos um segundo admin no GitHub
- Documente quem é dono das credenciais
- `secrets.toml` e `.json` da service account **nunca** vão pro git

---

## Credenciais — regras

- Revogue chaves vazadas no Google Cloud e gere outra
- No deploy, segredos vivem em **Settings → Secrets** do Community Cloud
