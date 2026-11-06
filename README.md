# Cooking Compass

Cooking Compass is a FastAPI backend for discovering, creating, and organizing recipes. It exposes a versioned REST API and uses MySQL for persistent data, Redis for caching, and Keycloak-issued access tokens for user authentication.

## Features

- Recipe listing, detail, search, create, update, delete, and ratings
- Recipe categories and ingredients
- User carts and cooking routines
- Async persistence through SQLAlchemy and the `asyncmy` MySQL driver
- Redis-backed response caching with cache invalidation
- Keycloak JWT validation for web and mobile clients
- Interactive API documentation through FastAPI

## Architecture

The application is a modular monolith. `app.py` creates the FastAPI application, sets up database tables during startup, and mounts the versioned router.

```mermaid
flowchart LR
    Client[Web and mobile clients] -->|REST /api/v1| API[FastAPI app]
    Client -->|Sign in and obtain token| KC[Keycloak]
    API --> Routes[Feature routes]
    Routes --> Auth[JWT validation]
    Auth <-->|JWKS keys| KC
    Routes --> Services[Feature services]
    Services --> Models[SQLAlchemy models]
    Models -->|Async SQL| MySQL[(MySQL)]
    Services <-->|Cache reads and invalidation| Redis[(Redis)]
```

Requests enter through the versioned FastAPI routes. Authenticated operations validate Keycloak tokens, feature services coordinate application logic, SQLAlchemy persists data in MySQL, and Redis holds cached data.

```text
app.py
└── src/cooking_compass/
    ├── auth/       Keycloak token validation
    ├── core/       SQLAlchemy database and Redis clients
    ├── models/     SQLAlchemy entities
    ├── routes/     FastAPI endpoints under /api/v1
    ├── schema/     Request and response models
    ├── service/    Business logic
    └── utils/      Shared user, authorization, and cache helpers
```

The API router currently groups endpoints for recipes, ingredients, categories, carts, and routines. Route schemas and service code are organized by feature.

## Requirements

- Python 3.14 or newer
- [uv](https://docs.astral.sh/uv/)
- A MySQL database
- A Redis server
- A Keycloak realm configured for the application when using authenticated endpoints

The repository does not include a frontend or a Docker Compose stack for local dependencies.

## Run locally

1. Clone the repository and enter its directory:

   ```bash
   git clone https://github.com/USANJAY05/cooking-compass.git
   cd cooking-compass
   ```

2. Create and edit a local environment file based on the example:

   ```bash
   cp .env.example .env
   ```

   Set the connection details for your MySQL instance and add the Redis URL. For example:

   ```dotenv
   APP_NAME="Cooking Compass"
   KEYCLOAK_URL=http://localhost:8080
   REALM_NAME=dev
   EXPECTED_AUDIENCE=cooking-cli
   DB_URL=mysql+asyncmy://root:password@localhost:3306/cooking_compass
   REDIS_URL=redis://localhost:6379/0
   KEYCLOAK_WEB_CLIENT_ID=myapp-web
   KEYCLOAK_MOBILE_CLIENT_ID=myapp-mobile
   ```

   Create the `cooking_compass` database before starting the app. Configure the Keycloak realm, clients, and token audience to match these values. Do not commit credentials or production secrets.

3. Install dependencies from the lockfile:

   ```bash
   uv sync --frozen
   ```

4. Start the development server:

   ```bash
   uv run uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```

On startup, the application creates missing SQLAlchemy tables. For production schema changes, use a migration process rather than relying on startup table creation.

## API documentation

With the server running, open:


- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- Welcome endpoint: [http://localhost:8000/](http://localhost:8000/)

API routes are mounted under `/api/v1`. Use the OpenAPI page to see available paths, parameters, and request/response schemas. Authenticated routes expect a bearer token issued by the configured Keycloak realm.

## Docker

The Dockerfile builds and runs the API on port `8000`. The image expects the database CA certificate at build time as `ca.cer`; the GitHub Actions workflow supplies it from the `DB_CERT` secret. Production database connections also require `APP_ENV=production` and `MYSQL_CA_CERT` pointing to the CA certificate path in the running container.

Build locally after providing `ca.cer`:

```bash
docker build -t cooking-compass .
docker run --rm -p 8000:8000 --env-file .env cooking-compass
```

The database and Redis must be reachable from the container. Configure production CORS origins for the deployed frontend before exposing the service publicly.

## Configuration reference

| Variable | Purpose |
| --- | --- |
| `APP_NAME` | Name returned by the root welcome endpoint |
| `APP_ENV` | Set to `production` to require MySQL TLS CA configuration |
| `DB_URL` | SQLAlchemy async MySQL connection URL |
| `MYSQL_CA_CERT` | CA certificate path required in production |
| `REDIS_URL` | Redis connection URL; use `rediss://` for TLS |
| `KEYCLOAK_URL` | Keycloak base URL |
| `REALM_NAME` | Keycloak realm |
| `EXPECTED_AUDIENCE` | JWT audience expected by the API |
| `KEYCLOAK_WEB_CLIENT_ID` | Allowed web client ID |
| `KEYCLOAK_MOBILE_CLIENT_ID` | Allowed mobile client ID |

`.env.example` lists the initial application variables. Add `REDIS_URL` for local and deployed environments.

## Deployment

On pushes to the configured branches, GitHub Actions builds and publishes `usanjay05/cooking-compass` Docker images tagged `latest` and with the commit SHA, then triggers the configured Render deploy hook. The workflow expects Docker Hub credentials, `DB_CERT`, and `RENDER_DEPLOY_HOOK` to be set as repository secrets.
