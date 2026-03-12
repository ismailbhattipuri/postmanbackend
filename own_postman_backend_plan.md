## Own Postman Backend Plan — Final Documentation

### Overview

This document details the backend plan for Own Postman, including environment setup, database schema, REST API endpoints, WebSocket features, offline/online sync, scripts/plugins execution, testing, deployment, and future AI integration.

### 1. Environment & Stack

- Python 3.11+
- FastAPI (async REST + WebSocket)
- PostgreSQL (online storage)
- SQLite (offline cache)
- Redis (optional, for pub/sub)
- SQLAlchemy / Tortoise ORM
- httpx (async HTTP client)
- Docker Compose for development & deployment

### 2. Database Schema

#### Users

- id (PK)
- username
- email
- password\_hash
- role (user/admin)
- last\_online (datetime)
- last\_activity (datetime)
- created\_at
- updated\_at

#### Workspaces

- id (PK)
- name
- owner\_id (FK -> Users.id)
- type (personal/organisation)
- online\_users (JSON/Redis)
- created\_at
- updated\_at

#### Collections, API Requests, Environment Variables, Plugins

- Same as final documentation schema
- Include updated\_at timestamps for sync and auditing

### 3. Core API Endpoints

#### Authentication

- /auth/signup
- /auth/login (JWT)
- /auth/refresh

#### Users

- /users/me (CRUD)
- /users/{id}

#### Workspaces

- /workspaces (CRUD)
- /workspaces/{id}/members
- /workspaces/{id}/online

#### Collections & Requests

- /collections (CRUD, share/unshare)
- /collections/{id}
- /requests (CRUD + execute)
- /requests/{id}/execute

#### Environment Variables & Plugins

- /environments (CRUD)
- /plugins (CRUD, enable/disable)

### 4. WebSocket Implementation

- ws\://backend/workspace/{workspace\_id}
- Real-time sync for collections, requests, scripts, environment variables
- Track online/offline user status and last activity
- Queue offline changes for later sync

### 5. Offline/Online Sync Logic

- Offline: local SQLite storage
- Online: WebSocket pushes queued changes to backend, merge into PostgreSQL, broadcast updates
- Conflict resolution via timestamp or JSON merge

### 6. Scripts & Plugin Execution

- Plugins are Python classes: run(), config(), output()
- Sandboxed execution environment
- Results synced via WebSockets

### 7. Authentication & Role Management

- JWT-based authentication
- Role-based access control (Admin / Member)
- OAuth2 optional

### 8. Testing & QA

- Unit tests: API endpoints, models, scripts
- Integration tests: WebSocket sync, offline-to-online merge
- Load testing: multi-user workspace scenarios
- Security tests: JWT validation, SQL injection, CSRF

### 9. Deployment & Monitoring

- Docker Compose for backend + PostgreSQL + Redis
- CI/CD: lint → unit tests → integration tests → deploy
- Monitoring: Prometheus/Grafana, Sentry

### 10. Optional Future Features

- AI/ML integration via plugin system
- Analytics on workspace activity
- Smart merge strategies for offline edits

### 11. Development Milestones

| Milestone                 | Description                                             |
| ------------------------- | ------------------------------------------------------- |
| Environment Setup         | Docker, FastAPI, PostgreSQL                             |
| Database & ORM            | Models, migrations, SQLite + Postgres                   |
| REST API Implementation   | Auth, Users, Workspaces, Collections, Requests, Plugins |
| WebSocket Implementation  | Realtime sync, user presence, online status             |
| Offline Storage Logic     | SQLite caching, local script execution                  |
| Plugin & Script Execution | Sandboxed Python plugin system                          |
| Testing & QA              | Unit, integration, load, security                       |
| Deployment & Monitoring   | CI/CD, logging, Docker Compose                          |
| Optional AI Integration   | Future AI endpoints via plugins                         |

