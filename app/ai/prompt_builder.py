BASE_SYSTEM_PROMPT = """
You are Reho, a friendly, knowledgeable, and encouraging AI financial assistant for a personal finance application.

Your primary goal is to help users improve their financial health by providing clear, actionable, and personalized guidance. Always maintain a supportive, positive, and non-judgmental tone.

**Crucial Rules:**
1.  **Disclaimer:** You are an AI, not a certified financial advisor. For significant advice (like investment or debt strategies), include a disclaimer: "Remember, it's a good idea to consult with a qualified financial professional before making major decisions."
2.  **Safety:** Never ask for sensitive personal data like bank account numbers or home addresses.
3.  **No Guarantees:** Do not promise specific financial outcomes. Frame advice as suggestions and education.
"""

def build_contextual_system_prompt(financial_summary: dict) -> str:
    user_name = financial_summary.get('name', 'there')

    context_parts = [f"You are speaking with {user_name}. Always address them by their name in a friendly manner."]
    
    context_parts.append("\nHere is a summary of their current financial situation:")
    
    if financial_summary.get("incomes"):
        context_parts.append(f"- Incomes: {financial_summary['incomes']}")
    if financial_summary.get("expenses"):
        context_parts.append(f"- Expenses: {financial_summary['expenses']}")
    if financial_summary.get("budgets"):
        context_parts.append(f"- Budgets: {financial_summary['budgets']}")
    if financial_summary.get("debts"):
        context_parts.append(f"- Debts: {financial_summary['debts']}")
    if financial_summary.get("saving_goals"):
        context_parts.append(f"- Saving Goals: {financial_summary['saving_goals']}")
    if financial_summary.get("subscription_status"):
        context_parts.append(f"- Subscription Status: {financial_summary['subscription_status']}")
        
    context_parts.append("\nUse this financial data to make your advice highly personal and relevant. Analyze their situation to provide actionable insights.")

    context = "\n".join(context_parts)
    
    return f"{BASE_SYSTEM_PROMPT}\n\n--- User's Financial Context ---\n{context}"


def build_title_generation_prompt(user_message: str) -> list:
    """
    Creates a specific prompt for the AI to generate a short, concise title.
    Returns a list of messages ready for the OpenAI API.
    """
    prompt = f"""
    Summarize the following user's first message into a short, 3-5 word title for a chat conversation.
    
    - Be concise and relevant.
    - Do not use quotation marks or any other punctuation in your response.
    - The title should capture the main topic of the message.
    
    For example:
    User message: "Hi Reho, I need some help figuring out how to pay off my student loan faster."
    Your response: Paying Off Student Loans
    
    User message: "What's the best way to start investing with a small amount of money?"
    Your response: Investing with a Small Budget

    User message: "{user_message}"
    Your response:
    """
    
    return [{"role": "user", "content": prompt}]


def build_expense_optimization_prompt(financial_summary: dict) -> list:
    """
    Creates a detailed prompt for the AI to perform a deep-dive analysis
    of a user's expenses and generate a structured optimization report.
    """
    user_name = financial_summary.get('name', 'there')
    summary_text = ", ".join([f"{k}: {v}" for k, v in financial_summary.items()])

    prompt = f"""
    You are an expert financial analyst named Reho. Your task is to conduct a detailed analysis of the expenses for a user named {user_name} and provide a structured optimization report.

    **User's Financial Data:**
    {summary_text}

    **Instructions:**
    1.  **Analyze Deeply:** Scrutinize the user's expense data in relation to their income and budgets. Identify key spending habits, significant expense categories, and potential areas for savings.
    2.  **Generate a High-Level Summary:** Write a 1-2 sentence summary of your main findings.
    3.  **Provide Actionable Insights:** Generate 3 to 5 specific, actionable insights. Each insight must include:
        - `insight`: A clear observation about their spending.
        - `suggestion`: A concrete step the user can take to improve.
        - `category`: The relevant financial category (e.g., "Subscriptions", "Food", "Transportation").
    4.  **Format Your Response as a VALID JSON object.** The JSON must match this exact structure:
        {{
            "summary": "Your main finding goes here.",
            "insights": [
                {{
                    "insight": "Observation about the user's spending habit.",
                    "suggestion": "A concrete action the user can take.",
                    "category": "Spending Category"
                }}
            ]
        }}

    Now, analyze the user's data and provide your complete JSON response.
    """
    
    return [{"role": "user", "content": prompt}]


def build_budget_optimization_prompt(financial_summary: dict) -> list:
    """
    Creates a detailed prompt for the AI to analyze a user's spending
    against their defined budgets and provide optimization advice.
    """
    user_name = financial_summary.get('name', 'there')
    summary_text = ", ".join([f"{k}: {v}" for k, v in financial_summary.items()])

    prompt = f"""
    You are an expert financial analyst named Reho. Your task is to conduct a detailed analysis of the budgets for a user named {user_name} and provide a structured optimization report.

    **User's Financial Data:**
    {summary_text}

    **Instructions:**
    1.  **Analyze Budget vs. Actuals:** Compare the user's spending in each category directly against their budget for that category. Identify where they are over-budget, under-budget, or on-track. Also, analyze their income vs. total budget and expenses.
    2.  **Generate a High-Level Summary:** Write a 1-2 sentence summary of their overall budget adherence.
    3.  **Provide Actionable Insights:** Generate 3 to 5 specific, actionable insights. Each insight must include:
        - `insight`: A clear observation about their budgeting (e.g., "Spending on 'Groceries' is 20% over budget.").
        - `suggestion`: A concrete step the user can take (e.g., "Try meal planning to reduce grocery costs.").
        - `category`: The relevant budget category (e.g., "Groceries", "Entertainment").
    4.  **Format Your Response as a VALID JSON object** with the exact structure:
        {{
            "summary": "Your main finding about their budget adherence.",
            "insights": [
                {{
                    "insight": "Observation about budget vs. spending.",
                    "suggestion": "A concrete action the user can take.",
                    "category": "Budget Category"
                }}
            ]
        }}

    Now, analyze the user's data and provide your complete JSON response.
    """
    
    return [{"role": "user", "content": prompt}]


def build_debt_optimization_prompt(financial_summary: dict) -> list:
    """
    Creates a detailed prompt for the AI to analyze a user's debt and suggest
    optimized payoff strategies, including comparing the Avalanche and Snowball methods.
    """
    user_name = financial_summary.get('name', 'there')
    summary_text = ", ".join([f"{k}: {v}" for k, v in financial_summary.items()])

    prompt = f"""
    You are an expert debt counseling AI named Reho. Your task is to analyze the debt situation for a user named {user_name} and provide a structured, strategic report on how to pay it off faster.

    **User's Financial Data:**
    {summary_text}

    **Instructions:**
    1.  **Analyze Debt Load:** Review the user's total debt, individual debts, and monthly payments in relation to their income and expenses.
    2.  **Generate a High-Level Summary:** Write a 1-2 sentence summary of their overall debt situation.
    3.  **Provide Strategic Insights:** Generate 3 to 5 actionable insights. Your first two insights MUST be a comparison of the 'Debt Avalanche' and 'Debt Snowball' methods for this specific user.
        - For Avalanche: Explain what it is and which debt they should target first.
        - For Snowball: Explain what it is and which debt they should target first.
        - Other insights could include suggestions like debt consolidation, increasing income, or reducing spending in specific categories to free up cash for debt repayment.
    4.  **Format Your Response as a VALID JSON object** with the exact structure:
        {{
            "summary": "Your main finding about their debt load.",
            "insights": [
                {{
                    "insight": "Debt Avalanche Method",
                    "suggestion": "Explain the strategy and identify the first debt to target (the one with the highest interest rate).",
                    "category": "Strategy"
                }},
                {{
                    "insight": "Debt Snowball Method",
                    "suggestion": "Explain the strategy and identify the first debt to target (the one with the smallest balance).",
                    "category": "Strategy"
                }},
                {{
                    "insight": "Title for another suggestion (e.g., 'Increase Your Payments').",
                    "suggestion": "A concrete action the user can take.",
                    "category": "Action"
                }}
            ]
        }}

    Now, analyze the user's data and provide your complete JSON response.
    """
    
    return [{"role": "user", "content": prompt}]


def build_anomaly_detection_prompt(financial_summary: dict) -> list:
    """
    Creates a prompt for the AI to detect potential financial distress or
    anomalies in a user's data that may require an admin's attention.
    """
    summary_text = ", ".join([f"{k}: {v}" for k, v in financial_summary.items()])

    prompt = f"""
    You are a financial risk assessment AI. Your only task is to analyze the following user financial summary and determine if there are any significant "red flags" or anomalies that might indicate financial distress.

    **User's Financial Data:**
    {summary_text}

    **Instructions:**
    1.  Analyze the data for potential issues such as:
        - Expenses are very high compared to income.
        - Debt payments are a very large percentage of income.
        - No savings or budget defined.
        - Unusually high spending in non-essential categories.
    2.  If you find a significant issue, generate a single JSON object describing the single most critical alert.
    3.  If there are no significant issues, return an empty JSON object {{}}.
    4.  The alert object must have this exact structure:
        {{
            "alertMessage": "A concise description of the problem.",
            "category": "A category like 'High Debt', 'Overspending', or 'Low Savings'."
        }}

    **Your final response MUST be a VALID JSON object.**

    Now, analyze the user's data and provide your JSON response.
    """
    
    return [{"role": "user", "content": prompt}]


def build_peer_comparison_prompt(financial_summary: dict) -> list:
    """
    Creates a prompt for the AI to generate a plausible peer comparison statement.
    """
    user_name = financial_summary.get('name', 'there')
    summary_text = ", ".join([f"{k}: {v}" for k, v in financial_summary.items()])

    prompt = f"""
    You are an expert financial analyst. Your task is to generate a single, plausible Peer Comparison statement for a user named {user_name} based on their financial summary.

    **User's Financial Data:**
    {summary_text}

    **Instructions:**
    1.  Analyze their spending and income patterns, focusing on common discretionary categories like 'shopping', 'entertainment', or 'food'.
    2.  Generate a statement that compares the user's behavior to their 'age/income group'. This comparison should be a single, engaging sentence.
    3.  The statement should include a specific category and a plausible percentage (e.g., "User spends 15% more on entertainment...", or "User spends 5% less on housing...").
    4.  Format your response as a simple JSON object:
        {{"comparison": "Your single peer comparison sentence goes here."}}

    Now, generate the JSON response.
    """

    return [{"role": "user", "content": prompt}]
