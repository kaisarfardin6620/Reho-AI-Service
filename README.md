# Reho AI Financial Assistant (FastAPI Service)

[![fastapi](https://img.shields.io/badge/FastAPI-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![python](https://img.shields.io/badge/Python-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![mongodb](https://img.shields.io/badge/MongoDB-47A248.svg?style=for-the-badge&logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![openai](https://img.shields.io/badge/OpenAI-412991.svg?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com/)

## Core Concept: The "AI Brain"

This is **not** a standalone backend. It is a highly specialized **AI microservice** designed to act as the intelligent brain for a larger financial management application. Its sole purpose is to handle all computationally intensive, data-driven, and AI-powered tasks, offloading this complexity from the main backend.

While the main backend handles core functionalities like user authentication and data storage, this FastAPI service connects to the same database to read financial data, analyze it using the OpenAI API, and provide actionable intelligence back to the user.

---

## Architecture: Relationship with the Node.js Backend

This project operates in a microservice architecture alongside the main backend. The division of responsibilities is clear:

#### Node.js Server (The Main Application Backend)
*   Handles all User Authentication & Management (Registration, Login, Password Reset, etc.).
*   Manages all standard CRUD (Create, Read, Update, Delete) operations for user data (incomes, expenses, budgets, etc.).
*   Processes payments and subscriptions.
*   Serves the primary API that the frontend application consumes for day-to-day operations.
> **Main Backend Repository:** [finance-management-backend (Node.js)](https://github.com/Rifat7432/finance-management-backend)

#### This FastAPI Server (The AI & Analysis Backend)
*   **Reads** user financial data from the shared database.
*   **Verifies** user identity by decoding JWTs signed by the Node.js server.
*   Provides all AI-powered features that require heavy data analysis and interaction with the OpenAI API.
*   Runs automated background jobs to analyze user data periodically.

The two services are tightly coupled through two key integration points:
1.  **Shared MongoDB Database**: Both services read from and write to the same database.
2.  **Shared JWT Secret**: The FastAPI service uses the exact same `JWT_SECRET` as the Node.js server to validate the authenticity of user requests.

---

## Core AI Features Implemented

This service provides a full suite of AI features to transform the user experience:

1.  **Conversational AI (Reho Chatbot)**
    *   A real-time, personalized WebSocket-based chatbot named "Reho".
    *   Understands the user's financial context (name, income, expenses) to provide tailored advice.
    *   Maintains full conversation history.
    *   Automatically generates titles for new conversations.
    *   Includes full conversation management (List, Rename, Delete).

2.  **Proactive "AI Suggestions" (Automated)**
    *   An automated background job runs daily to analyze each user's financial health.
    *   Generates 3 short, actionable tips (e.g., "Your spending on 'Food' is high") that are displayed on the user's dashboard.

3.  **On-Demand "AI Optimization" (User-Triggered)**
    *   Provides deep-dive analysis when a user requests it.
    *   **Optimize Expenses**: Returns a detailed report on spending habits.
    *   **Optimize Budget**: Analyzes spending against budgets and provides insights.
    *   **Optimize Debt**: Compares debt payoff strategies (Avalanche vs. Snowball) and creates a strategic plan.

4.  **Admin AI Alerts (Automated)**
    *   A second automated background job runs daily to screen all users for financial red flags (e.g., debt-to-income ratio is too high).
    *   Generates alerts that are accessible via a secure admin-only endpoint.

---

## API Endpoints Overview

The service exposes 10 total endpoints, grouped by functionality.

| Method      | Endpoint                                    | Description                                | Auth           |
|-------------|---------------------------------------------|--------------------------------------------|----------------|
| **WebSocket** | `/chat/ws`                                  | Real-time conversational AI.               | Token in Query |
| **GET**     | `/chat/conversations`                       | List all of a user's conversations.        | Bearer Token   |
| **PATCH**   | `/chat/conversations/{id}`                  | Rename a conversation.                     | Bearer Token   |
| **DELETE**  | `/chat/conversations/{id}`                  | Delete a conversation.                     | Bearer Token   |
| **GET**     | `/suggestions`                              | Get the latest daily AI suggestions.       | Bearer Token   |
| **POST**    | `/feedback/optimize-expenses`               | Get an on-demand expense analysis report.  | Bearer Token   |
| **POST**    | `/feedback/optimize-budget`                 | Get an on-demand budget analysis report.   | Bearer Token   |
| **POST**    | `/feedback/optimize-debt`                   | Get an on-demand debt analysis report.     | Bearer Token   |
| **GET**     | `/admin/alerts`                             | (Admin) Get all financial distress alerts. | Bearer (Admin) |
| **GET**     | `/health`                                   | Service health check.                      | None           |

---

## Technology Stack

*   **Framework**: FastAPI
*   **Async Server**: Uvicorn
*   **Database**: MongoDB (via `motor` async driver)
*   **AI Service**: OpenAI GPT-4 & GPT-3.5-Turbo
*   **Data Validation**: Pydantic
*   **Authentication**: PyJWT
*   **Job Scheduling**: APScheduler
*   **Environment Config**: python-dotenv, pydantic-settings

---

## Local Setup & Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/kaisarfardin6620/Reho-AI-Service.git
    cd Reho-AI-Service
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv .venv
    # On Windows
    .venv\Scripts\activate
    # On macOS/Linux
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Create the environment file:**
    Create a `.env` file in the `fastapi_server` root directory and add the following variables. **The `JWT_SECRET` must be identical to the one in the Node.js backend.**

    ```env
    # .env

    # MongoDB Connection String from your main backend
    DATABASE_URL=your-db-url

    # JWT Secret - MUST MATCH THE NODE.JS SERVER
    JWT_SECRET=your_shared_jwt_secret
    JWT_ALGORITHM=HS256

    # Your OpenAI API Key
    OPENAI_API_KEY=your-api-key
    ```

5.  **Run the development server:**
    The server will start, and the scheduler will be activated.
    ```bash
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
    ```

---

## Project Structure

The project follows a clean, scalable structure:

-   `/app/ai`: Contains all prompt engineering logic. The "soul" of the AI.
-   `/app/core`: Core application settings and configuration.
-   `/app/db`: Database client setup and all query functions.
-   `/app/jobs`: Logic for the automated, scheduled background tasks.
-   `/app/models`: Pydantic models for API request/response validation.
-   `/app/routers`: Defines all API endpoints (`@router.get`, etc.).
-   `/app/services`: Contains the core business logic for each feature.
-   `/app/utils`: Shared utilities, primarily for security and token handling.
-   `/app/main.py`: The main entry point that assembles the FastAPI application.
