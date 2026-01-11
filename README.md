# Reho AI Finance Microservice 🧠

This project is the **Artificial Intelligence Microservice** for the Finance Management System. It serves as the "Brain" of the application, working alongside the [Main Backend (Node.js/Express)](https://github.com/Rifat7432/finance-management-backend) to provide intelligent financial advice, real-time chat, and automated data analysis.

---

## 📖 Overview: How it Works

While the [Main Backend](https://github.com/Rifat7432/finance-management-backend) handles user authentication, transaction creation, and core CRUD operations, this Microservice focuses entirely on **Data Intelligence**.

This service connects to the **same MongoDB database** as the main backend. This architecture allows the AI to "see" user data immediately after it is created in the main app, enabling:

1.  **Context-Aware Chat:** When a user asks "Can I afford a vacation?", the AI checks their *actual* bank balance and debts before answering.
2.  **Proactive Analysis:** Background jobs analyze spending patterns to generate "Red Flag" alerts for admins and "Optimization Tips" for users.
3.  **Personalization:** Every tip, alert, or chat response is tailored to the specific user's financial reality.

---

## 🛠 Tech Stack

*   **Framework:** Python FastAPI (Async)
*   **AI Engine:** OpenAI API (GPT-4o)
*   **Database:** MongoDB (via Motor async driver) - *Shared with Main Backend*
*   **Caching:** Redis (User session & summary caching)
*   **Deployment:** Docker & Docker Compose
*   **Server:** Uvicorn behind Nginx

---

## 🚀 Features & Modules

### 1. 💬 Intelligent Chat (`/chat`)
*   **Real-time WebSocket:** Provides a seamless chat experience with "Reho", the AI assistant.
*   **Dynamic Context Injection:** Before answering, the system builds a snapshot of the user's Incomes, Expenses, and Debts and feeds it to the LLM system prompt.
*   **Memory:** Maintains conversation history so the user can ask follow-up questions.

### 2. 📊 Admin Dashboard Intelligence (`/admin`)
*   **User 360 View:** Generates AI summaries for administrators to view a user's health.
*   **Spending Heatmap:** Categorizes where money is leaking.
*   **Risk Assessment:** Auto-calculates risk levels (Low/Medium/High) based on debt-to-income ratios.
*   **Peer Comparison:** Uses AI to generate anonymized comparisons (e.g., "User spends 15% more on dining than peers").

### 3. 💡 Optimization Feedback (`/feedback`)
*   **50/30/20 Analysis:** Analyzes if the user fits the "Needs/Wants/Savings" model.
*   **Debt Strategies:** Compares **Avalanche vs. Snowball** methods specifically for the user's loan portfolio.
*   **Expense Audits:** Identifies subscriptions or categories that can be trimmed.

### 4. 🧮 Calculator Tips (`/calculator`)
*   **Dynamic Insight:** When a user uses the frontend calculators (Savings, Loan, Inflation), this service generates a specific tip linking that calculation to their real-world budget.

### 5. ⏰ Scheduled Jobs (`/schedule`)
*   **Daily Runner:** A background task (`daily_job_runner.py`) pre-calculates heavy analysis reports at night so the dashboard loads instantly during the day.

---

## ⚙️ Setup & Installation

### Prerequisites
*   Python 3.11+
*   Docker & Docker Compose
*   MongoDB Connection String (From Main Backend)
*   OpenAI API Key

### 1. Environment Variables
Create a `.env` file in the root directory. Ensure the database matches your Main Backend.

```env
# Database
DATABASE_URL=mongodb+srv://<user>:<password>@<cluster>.mongodb.net
MONGO_DB_NAME=finance-management
REDIS_URL=redis://localhost:6379/0

# Security
JWT_SECRET=your_jwt_secret_from_main_backend
JWT_ALGORITHM=HS256
OPENAI_API_KEY=sk-proj-....
SCHEDULER_API_KEY=internal_secret_key_for_cron_jobs

# Config
API_BASE_URL=http://localhost:8000
ALLOWED_HOST_ORIGINS=http://localhost:3000,http://127.0.0.1:3000