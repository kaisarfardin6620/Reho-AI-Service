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
    # ... (rest of function unchanged) ...
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
    # ... (rest of function unchanged) ...
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
    # ... (rest of function unchanged) ...
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
    # ... (rest of function unchanged) ...
    """
    
    return [{"role": "user", "content": prompt}]