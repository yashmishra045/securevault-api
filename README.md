# SecureVault API

A production-grade secrets management REST API — inspired by HashiCorp Vault.

## Features
-  AES-256-GCM encryption for all stored secrets
-  JWT authentication with refresh token rotation
-  Role-Based Access Control (Admin/Editor/Viewer)
-  Sliding-window rate limiting (100 req/min)
-  Append-only audit trail in PostgreSQL
-  Docker Compose setup

## Tech Stack
Python · FastAPI · PostgreSQL · Docker · SQLAlchemy · JWT · AES-256

## Quick Start
\`\`\`bash
docker-compose up -d
uvicorn app.main:app --reload --port 8000
\`\`\`

## API Docs
Visit: http://localhost:8000/docs
