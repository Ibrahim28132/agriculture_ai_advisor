# Agri Advisor

This repository contains a Django-based agricultural advisor web application.

What this contains
- Django project in `agricultural_project/` and app `advisor_app/`.
- Dockerfile and docker-compose for local development.
- GitHub Actions workflows for CI (tests) and CD (build & push Docker image to GHCR).

Quick start (local)

1. Create a Python virtual environment and activate it:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Copy the example environment file and edit values:

```powershell
copy .env.example .env
# then edit .env
```

4. Run migrations and start the dev server:

```powershell
python manage.py migrate
python manage.py runserver
```

5. Run tests:

```powershell
python manage.py test
```

Docker (local development)

```powershell
docker compose up --build
# app will be available on http://localhost:8000
```

GitHub Actions

- CI: runs on push and pull_request. It installs dependencies and runs tests.
- CD: runs on push to `main` (or `master`) and builds a Docker image and pushes it to the GitHub Container Registry (`ghcr.io/${{ github.repository_owner }}/agri-advisor`). The workflow uses the default `GITHUB_TOKEN` to authenticate.

Secrets & configuration

- Add API keys (TAVILY_API_KEY, OPENWEATHER_API_KEY, OPENAI_API_KEY) to GitHub repository secrets if you want workflows or deployed containers to access them.

Notes

- The CD workflow builds and pushes a Docker image. You will need to configure your hosting environment (Kubernetes, cloud run, or similar) to pull the image and run migrations.
- For production, replace the default `DATABASE_URL` with a managed database (Postgres) and set `DEBUG=False` and a secure `DJANGO_SECRET_KEY`.

