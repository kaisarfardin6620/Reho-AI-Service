## Running the Project with Docker

This project provides a Docker setup for local development and deployment. The application runs on Python 3.11 (as specified in the Dockerfile) and uses MongoDB as its database backend.

### Requirements
- Docker and Docker Compose installed on your system
- (Optional) `.env` file in the project root for environment variables

### Build and Run Instructions

1. **Clone the repository and navigate to the project root.**
2. **(Optional) Create a `.env` file** if you need to set environment variables for the application or MongoDB. Refer to the commented sections in `docker-compose.yml` for possible variables.
3. **Build and start the services:**

   ```bash
   docker compose up --build
   ```

   This will build the Python application image and start both the app and MongoDB containers.

### Service Details
- **python-app**: Runs the main application using Python 3.11 in a virtual environment. No ports are exposed by default; update `docker-compose.yml` if you need to expose application endpoints.
- **mongo**: Uses the official `mongo:latest` image. Data is persisted in the `mongo-data` volume. No ports are exposed by default; add a `ports:` section in `docker-compose.yml` if you need external access.

### Configuration Notes
- The application runs as a non-root user for improved security.
- MongoDB healthchecks are enabled for container reliability.
- All services are connected via the `backend` Docker network.
- If you need to set MongoDB credentials, uncomment and edit the `environment:` section under the `mongo` service in `docker-compose.yml`.

For further customization, review the `Dockerfile` and `docker-compose.yml` files in the project root.