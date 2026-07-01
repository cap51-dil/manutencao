# Plataforma de Dados — APS 5.1

ELT automatizado: planilhas no Google Drive → tratamento (Python) → painel Streamlit.
As pessoas só encostam em dois pontos: **sobem planilha no Drive** e **abrem a URL do painel**.

```
Pasta por serviço no Drive ──(service account, leitura)──▶ Streamlit
   • um serviço = uma pasta (ex.: Manutenção)                 • escolhe serviço + planilha
   • várias planilhas na mesma pasta                          • cada planilha = um dashboard
   • pessoas largam os .xlsx lá                               • botão "Atualizar dados"
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
│   ├── clean.py                 # dispatcher por serviço + planilha
│   └── dashboard.py             # KPIs, filtros e gráficos
├── cleaners/
│   ├── camaras_vacina.py        # limpeza — Manutenção / Câmaras de Vacina
│   └── servicos_prioritarios.py # limpeza — Manutenção / Serviços Prioritários
├── requirements.txt
├── .gitignore
└── .streamlit/
    ├── config.toml
    └── secrets.toml.example
```

---

## Modelo de configuração

| Nível | Exemplo | O que é |
|-------|---------|---------|
| **Serviço** | `Manutenção` | Pasta no Drive (uma por área/app) |
| **Planilha** | `Câmaras de Vacina` | Arquivo dentro da pasta → dashboard próprio |

Exemplo no `secrets.toml`:

```toml
[servicos]
"Manutenção" = "ID_DA_PASTA_NO_DRIVE"

[planilhas."Manutenção"]
"Câmaras de Vacina" = "STATUS CÂMARAS DE VACINA"
"Serviços Prioritários" = "SERVIÇOS PRIORITÁRIOS"
```

O valor de cada planilha é o **padrão do nome do arquivo** no Drive (substring, case-insensitive).

---

## POC — Manutenção

| Planilha | Padrão do arquivo | Fonte local (dev) |
|----------|-------------------|-------------------|
| Câmaras de Vacina | `STATUS CÂMARAS DE VACINA` | sim (`[locais]`) |
| Serviços Prioritários | `SERVIÇOS PRIORITÁRIOS` | só Drive |

Pasta Drive do serviço Manutenção: `1EAp-v4dyjxdmaEP4c85hxVCQsRH6Og09`

Serviços Prioritários lê a aba consolidada `BASE_DADOS` da planilha no Drive.

---

## Passo a passo

> Os passos com 🔑 envolvem credenciais — **você** faz no console do Google / Streamlit.
> O arquivo `secrets.toml` é seu e fica fora do git.

### 1. 🔑 Service account (Google Cloud)

1. Acesse <https://console.cloud.google.com>
2. Crie um projeto e ative a **Google Drive API**
3. Crie uma **conta de serviço** e baixe a chave JSON
4. Compartilhe cada pasta de serviço com o e-mail da service account como **Leitor**

### 2. Rodar localmente

```bash
cd manutencao
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Use o Python do ambiente virtual (`.venv`). Se o erro `No module named 'google.oauth2'` aparecer, o Streamlit provavelmente está usando o Python do sistema — rode com:

```bash
source .venv/bin/activate
streamlit run app.py
# ou, sem ativar:
.venv/bin/streamlit run app.py
```

Abra `.streamlit/secrets.toml` e preencha:
- `[gcp_service_account]`: copie os campos do **JSON baixado** no GCP
- `[servicos]`: um ID de pasta por serviço
- `[planilhas."<Serviço>"]`: uma entrada por planilha/dashboard (aspas obrigatórias se o nome tiver acento)
- `[locais."<Serviço>"]`: (opcional) caminho local para modo dev

**`private_key` — formato correto (evita erro PEM):**

```toml
private_key = """
-----BEGIN PRIVATE KEY-----
(cada linha da chave do JSON, sem \\n)
-----END PRIVATE KEY-----
"""
```

Se colar do JSON com `\n` escapado numa linha só, o app tenta corrigir automaticamente.
Se ainda falhar, use o bloco multilinha acima. Referência: [FAQ cryptography — PEM](https://cryptography.io/en/latest/faq/#why-can-t-i-import-my-pem-file).

streamlit run app.py
```

**Modo dev (sem Drive):** marque **"Usar planilha local"** na sidebar. Coloque o `.xlsx` na raiz e configure `[locais.<Serviço>]`.

### 3. Calibrar uma nova planilha

Para cada nova planilha dentro de um serviço:

1. Crie `cleaners/<nome>.py` com `limpar(conteudo: bytes) -> DataFrame`
2. Registre em `utils/clean.py` → `CLEANERS` com chave `("Serviço", "Planilha")`
3. Adicione `render_<nome>()` em `utils/dashboard.py`
4. Inclua a planilha em `secrets.toml` em `[planilhas."<Serviço>"]`

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
