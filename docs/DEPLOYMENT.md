# Deployment Architecture
AeroRecon supports dual deployment modalities.

## 1. Local CPU Execution (Field/Edge)
- **Architecture:** SQLite + FastAPI + ThreadPoolExecutor.
- **Constraints:** One job at a time. State resets on restart.
- **Setup:** `uvicorn app.main:app`

## 2. Distributed Execution (Command Center)
- **Architecture:** PostgreSQL + Redis + RQ + FastAPI (Docker Compose).
- **Capabilities:** Multiple GPU workers, durable state, load balancing.
- **Setup:** `docker-compose up -d`
