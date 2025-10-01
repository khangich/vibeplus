# Vibecoder

Vibecoder is a minimal viable product for a "vibe coding" platform that helps users scaffold themed Next.js applications using a FastAPI backend and a Redis-backed worker pipeline. The project ships as a docker-compose stack and targets Fly.io for deployment.

## Features

- Prompt driven project generation with mock LLM planner/scaffolder
- Revision tracking backed by Postgres and Redis
- Async build pipeline that produces previews and downloadable artifacts
- Passwordless auth stubs with Supabase/Clerk adapters (placeholders)
- Rate limiting per user using Redis token buckets
- Observability via structured JSON logs and persisted artifacts
- Export pathways for GitHub pull requests and zip archives (stubbed)

## Getting Started

### Prerequisites

- Docker and docker-compose
- make (optional)

### Environment

Copy the example environment file and adjust values as needed:

```bash
cp .env.example .env
```

Ensure the `NEXT_PUBLIC_BACKEND_URL` points to the backend service (`http://localhost:8000` when accessed from your browser).

For server-side data fetching inside docker-compose, the frontend container reads `BACKEND_INTERNAL_URL`. Leave it empty for host-based development or set it to `http://backend:8000` (the docker service name) when running the full stack.

### Local Development

Build and start the stack:

```bash
docker-compose up --build
```

Services:

- Frontend: http://localhost:8080
- Backend API docs: http://localhost:8000/docs
- Redis: redis://localhost:6379/0
- Postgres: postgres://vibecoder:vibecoder@localhost:5432/vibecoder
- MinIO console: http://localhost:9001 (credentials in `.env.example`)

Once the stack is up you can use the UI to enter a prompt, choose a vibe, and generate a project. The mock LLM returns deterministic scaffolds so the pipeline completes quickly. Build logs and artifacts are available from the revision detail page.

### Preview URLs

Locally, previews are exposed at `http://<revision-id>.preview.localtest.me:8080`. The domain resolves to `127.0.0.1`, allowing multiple previews without additional DNS configuration.

### Testing

Run backend tests with:

```bash
cd backend
poetry run pytest
```

(You can also install dependencies via `pip install -e .[dev]`.)

### Deployment on Fly.io

The repository includes a `fly.toml` configured for the `sjc` region with `backend` and `frontend` processes. Deploy using:

```bash
fly launch --copy-config
fly secrets set $(cat .env | xargs)
fly deploy
```

For object storage, point the environment variables to your S3-compatible service or managed bucket.

### LLM Integration

The worker currently uses a deterministic mock (`backend.backend.llm.mock`). Replace the implementation in `backend/backend/llm/interface.py` and `worker/worker/pipeline.py` with real LLM calls and tooling when integrating with a provider. Ensure you respect rate limits and logging conventions when upgrading to a production LLM.

## Repository Structure

See the prompt for the detailed file tree. Each directory contains README-worthy comments inline for clarity.
