## Running the Project with Docker

This project includes a Docker setup for streamlined development and deployment. The provided `Dockerfile` uses **Python 3.11-slim** and installs all dependencies in a virtual environment. The recommended way to build and run the application is via Docker Compose.

### Requirements
- Docker (latest version recommended)
- Docker Compose (v2 or higher)

### Environment Variables
- The application supports environment variables via a `.env` file. If you have project-specific settings, create a `.env` file in the project root. Uncomment the `env_file` line in `docker-compose.yml` to enable this.

### Build and Run Instructions
1. **Build and start the application:**

   ```sh
   docker compose up --build
   ```

   This will build the image and start the `python-app` service.

2. **Stopping the application:**

   ```sh
   docker compose down
   ```

### Configuration Notes
- The application runs as a non-root user for improved security.
- All Python dependencies are installed in an isolated virtual environment inside the container.
- If your application exposes a web server, map the appropriate ports in the `ports` section of `docker-compose.yml`. By default, no ports are published. Uncomment and adjust as needed:

   ```yaml
   ports:
     - "8000:8000"  # Replace with your app's port if necessary
   ```

- The `.dockerignore` file should be configured to exclude files like `.env`, `.git`, and other development artifacts from the build context.

### Service Overview
- **python-app**: Main application service, built from the provided `Dockerfile`.
- **Network**: All services are attached to the `app-net` bridge network.

For any additional configuration, refer to the comments in the `docker-compose.yml` and `Dockerfile`.