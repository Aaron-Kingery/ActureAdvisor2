# Acture Advisor 2.0 - Installation and Deployment Guide

## Prerequisites

- **Docker & Docker Compose**: Ensure Docker Desktop or Docker Engine is installed and running.
- **Git**: For cloning the repository.
- **SSL Certificates** (Optional for local dev): If deploying to production, ensure `certs/` contains your certificate files.

## Initial Setup

1.  **Clone the Repository**
    ```bash
    git clone <repository-url>
    cd ActureAdvisor2
    ```

2.  **Environment Configuration**
    
    The application relies on `.env` files which are **not tracked in git** for security. You must create them manually.

    **Backend (`backend/.env`):**
    ```ini
    # Database
    POSTGRES_USER=user
    POSTGRES_PASSWORD=password
    POSTGRES_DB=acture_advisor
    DATABASE_URL=postgresql+asyncpg://user:password@db:5432/acture_advisor

    # Core AI
    OLLAMA_BASE_URL=http://ollama:11434

    # OpenAI (Optional - Required if not using Ollama exclusively)
    OPENAI_API_KEY=sk-proj-... (Your Valid Key)

    # Document Connectors (SharePoint/Azure)
    SHAREPOINT_SITE_URL=https://your-sharepoint-site/
    AZURE_AD_CLIENT_ID=...
    AZURE_AD_CLIENT_SECRET=...
    AZURE_AD_TENANT_ID=...

    # CORS
    BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]
    ```

    **Frontend (`frontend/.env.local`):**
    ```ini
    NEXT_PUBLIC_API_URL=http://localhost:8000
    AUTH_SECRET=...
    # (Add other frontend public vars as needed)
    ```

3.  **Directory Permissions (CRITICAL)**

    The backup system requires strict permissions on the host directory to function correctly. You **must** run the following command on the host machine before starting containers:

    ```bash
    # Grant full write permissions to the backup directory
    sudo chmod -R 777 backups/
    ```
    
    *Failure to do this will result in the backup container crashing with "Insufficient permissions" errors.*

## Running the Application

1.  **Start Services**
    ```bash
    docker-compose up -d --build
    ```

2.  **Verify Services**
    - **Frontend**: http://localhost:3000
    - **Backend API**: http://localhost:8000/docs
    - **Ollama**: http://localhost:11434

## Maintenance & Operations

### Manual Backups
To trigger an immediate database backup:
```bash
docker exec acture-backup /backup.sh
```
Check the `backups/` directory on your host to verify the file creation.

### Database Recovery
To restore a backup, stop the database container, replace the volume data or load the SQL dump:
```bash
cat backups/daily/acture_advisor-YYYYMMDD.sql.gz | gunzip | docker exec -i acture-db psql -U user -d acture_advisor
```

### Updating Environment Variables
If you modify `backend/.env` (e.g., updating the API key), you must **recreate** the container for changes to take effect:
```bash
docker-compose up -d --force-recreate backend
```
*(Simply restarting with `docker restart` is not sufficient for .env changes)*

## Troubleshooting

- **Backup Container Restart Loop**: Ensure `backups/` has 777 permissions.
- **OpenAI 401 Error**: Verify `OPENAI_API_KEY` in `backend/.env` is valid and run `--force-recreate` on the backend.
