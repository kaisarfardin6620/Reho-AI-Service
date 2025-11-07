## Running the Project with Docker

This project includes Docker and Docker Compose configuration for streamlined setup and deployment.

### Requirements
- **Python Version:** 3.13 (as specified in the Dockerfile)
- **Dependencies:** All Python dependencies are installed from `requirements.txt` inside a virtual environment (`.venv`).

### Environment Variables
- If your project requires environment variables, create a `.env` file in the project root. Uncomment the `env_file` line in `docker-compose.yml` to enable automatic loading.

### Build and Run Instructions
1. **Build and start the application:**
   ```sh
   docker compose up --build
   ```
   This will build the Docker image and start the `python-app` service.

2. **Stopping the application:**
   ```sh
   docker compose down
   ```

### Service Configuration
- **Main Service:** `python-app`
  - Uses Python 3.13 in a slim container.
  - Runs the application from `/app` using the virtual environment.
  - Default command: `python -m app.main`
  - No ports are exposed by default. If your app provides an HTTP API, uncomment and configure the `ports` section in `docker-compose.yml` (e.g., `8000:8000`).

- **MongoDB (Optional):**
  - If your application requires MongoDB (see `db/client.py` and `utils/mongo_metrics.py`), uncomment the `mongo` service in `docker-compose.yml` and configure credentials as needed.
  - Default exposed port: `27017` (uncomment in compose file if needed).
  - Data is persisted in the `mongo_data` volume.

### Special Notes
- The Docker setup uses a multi-stage build for efficient dependency management and a minimal runtime image.
- The application runs as a non-root user for improved security.
- If you add new dependencies, update `requirements.txt` and rebuild the image.

Refer to the comments in `docker-compose.yml` for further customization options specific to your development or production needs.