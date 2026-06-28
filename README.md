# ingestao-async

API de ingestao e processamento assincrono de dados publicos. O usuario autenticado submete uma fonte de dados (CSV ou URL), a API enfileira um job, um worker separado processa os dados em background e o resultado fica disponivel via REST e num dashboard React.

## Arquitetura

```
[React Dashboard] --> [FastAPI] --> [Fila Postgres] --> [Worker]
                         |                                  |
                         v                                  v
                    [Supabase Postgres] <------------------+
```

O processamento e assincrono por necessidade real: datasets publicos podem ter centenas de milhares de linhas e levar minutos para processar. A fila garante que a API responde em milissegundos enquanto o processamento ocorre em background.

## Stack

| Camada | Tecnologia |
|---|---|
| API | Python 3.12, FastAPI, Pydantic v2 |
| ORM | SQLAlchemy 2.0 async + asyncpg |
| Migrations | Alembic |
| Auth | argon2-cffi (senha), python-jose (JWT) |
| Fila | Postgres (SELECT FOR UPDATE SKIP LOCKED) |
| Logging | structlog (JSON estruturado) |
| Frontend | React 18, Vite, TypeScript strict, Tailwind CSS |
| Banco | Supabase Postgres (via Supavisor, porta 6543) |
| Deploy API | Render |
| Deploy Frontend | Cloudflare Pages |

## Fila Postgres x AWS SQS

A fila foi projetada como uma implementacao da interface `FilaInterface`, compativel com SQS:

| Nossa fila (Postgres) | AWS SQS |
|---|---|
| `enfileirar()` | `SendMessage` |
| `receber()` | `ReceiveMessage` |
| `confirmar()` | `DeleteMessage` |
| `rejeitar()` sem delete | Nao chamar `DeleteMessage` |
| `locked_until` | `VisibilityTimeout` |
| status=morto | Dead Letter Queue (DLQ) |

Para migrar para SQS: implementar `FilaSQS(FilaInterface)`. Zero mudancas no worker ou no codigo de negocio.

## Como rodar localmente

### Pre-requisitos

- Python 3.12+
- Docker (para o banco local)
- Node.js 20+

### Backend

```bash
docker compose up -d db

cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
# Editar .env: ajustar DATABASE_URL para localhost:5432, definir SECRET_KEY

alembic upgrade head
uvicorn app.main:app --reload
```

### Worker (outro terminal)

```bash
cd backend && source .venv/bin/activate
python -m app.worker.main
```

### Frontend (outro terminal)

```bash
cd frontend
npm install
npm run dev
# Acesse: http://localhost:5173
```

### Tudo junto com Docker

```bash
docker compose up
```

## Variaveis de Ambiente

| Variavel | Obrigatoria | Descricao |
|---|---|---|
| `DATABASE_URL` | sim | URL de conexao com o banco (asyncpg) |
| `SECRET_KEY` | sim | Chave JWT (gerar: `openssl rand -hex 32`) |
| `ENVIRONMENT` | nao | `development` / `test` / `production` |
| `CORS_ORIGINS` | nao | Origens permitidas, separadas por virgula |
| `WORKER_POLL_INTERVAL_SEGUNDOS` | nao | Intervalo de polling do worker (padrao: 5) |
| `UPLOAD_MAX_BYTES` | nao | Limite de upload CSV em bytes (padrao: 50MB) |

**Conexao Supabase (producao):**

```
postgresql+asyncpg://postgres.fdjvbmwdjwbfyrxotvot:[PASSWORD]@aws-0-sa-east-1.pooler.supabase.com:6543/postgres
```

Obter o password em: Supabase Dashboard > Project Settings > Database > Connection string.

## API

Base URL: `https://ingestao-async-api.onrender.com`

### Autenticacao

```
POST /api/v1/auth/registrar   # Cria usuario, retorna tokens
POST /api/v1/auth/login       # Autentica, retorna tokens
```

Incluir o token nas demais requisicoes:
```
Authorization: Bearer <access_token>
```

### Jobs

```
POST /api/v1/jobs/url         # Submete URL de dataset publico
POST /api/v1/jobs/csv         # Submete arquivo CSV (multipart)
GET  /api/v1/jobs             # Lista jobs do usuario
GET  /api/v1/jobs/{id}        # Status de um job especifico
```

**Resposta de submissao (202 Accepted):**
```json
{ "job_id": "uuid", "status": "pendente" }
```

**Status possiveis:** `pendente` | `processando` | `concluido` | `falhou` | `morto`

### Saude

```
GET /health  # { "status": "ok" }
```

## Testes

```bash
# Requer banco de teste rodando
docker compose up -d db-test

cd backend && source .venv/bin/activate
pytest tests/ -q

# Com cobertura
pytest tests/ --cov=app --cov-report=term-missing
```

Os testes usam banco real (sem mock de banco). O CI roda via GitHub Actions com banco Postgres efemero.

## Deploy

### Banco (Supabase)

Projeto `ingestao-async` na regiao `sa-east-1`. As migrations ja foram aplicadas.

Para aplicar novas migrations:
```bash
DATABASE_URL=<supabase-url> alembic upgrade head
```

### API e Worker (Render)

1. Conectar o repositorio GitHub ao Render.
2. Render detecta o `render.yaml` automaticamente.
3. Configurar manualmente no dashboard:
   - `DATABASE_URL`: URL do Supabase (ver secao de variaveis)
   - `SECRET_KEY`: gerado automaticamente pelo Render (`generateValue: true`)
4. O `render.yaml` define dois servicos:
   - `ingestao-async-api`: web service com health check em `/health`
   - `ingestao-async-worker`: background worker

**Atencao ao cold start:** o free tier do Render hiberna servicos apos 15 minutos sem requisicao. A primeira requisicao apos hibernacao pode levar 20-30 segundos.

### Frontend (Cloudflare Pages)

```bash
cd frontend
VITE_API_URL=https://ingestao-async-api.onrender.com npm run build
npx wrangler pages deploy dist --project-name=ingestao-async
```

URL de producao: `https://ingestao-async.pages.dev`

## CI

GitHub Actions (`.github/workflows/ci.yml`) executa em todo push para `main` e em PRs:

1. Lint e formatacao (ruff)
2. Verificacao de tipos (mypy strict)
3. Testes de integracao com banco Postgres real

## Estrutura

```
ingestao-async/
├── .github/workflows/ci.yml
├── backend/
│   ├── alembic/               # Migrations versionadas
│   ├── app/
│   │   ├── api/v1/routes/     # auth.py, jobs.py
│   │   ├── core/              # config, database, logging, security
│   │   ├── models/            # Usuario, Job, Dataset (SQLAlchemy)
│   │   ├── queue/             # FilaInterface + FilaPostgres
│   │   ├── schemas/           # Pydantic (auth, job)
│   │   ├── services/          # AuthService, JobService
│   │   └── worker/            # main.py + handlers/
│   └── tests/
├── frontend/
│   └── src/
│       ├── components/        # StatusBadge, BarChart (SVG puro)
│       ├── pages/             # Dashboard, Login, Submit
│       ├── services/          # api.ts (camada de fetch)
│       └── types/             # index.ts
├── docker-compose.yml
├── render.yaml
└── README.md
```
