import json
BASE_SYSTEM_PROMPT = """
You are Reho, a friendly, knowledgeable, and encouraging AI financial assistant for a personal finance application.

Your primary goal is to help users improve their financial health by providing clear, actionable, and personalized guidance. Always maintain a supportive, positive, and non-judgmental tone.

**Crucial Rules:**
1.  **CURRENCY & LANGUAGE:** All monetary values MUST be displayed in **British Pounds (£)**. The language must be British English.
2.  **FORMATTING (CRITICAL):** Respond using **ONLY plain text**. DO NOT use Markdown tags (like *, **, #, - for lists). Use line breaks and simple symbols (like arrows -> or hyphens -) for lists and emphasis.
3.  **HIGH PRIORITY:** Always address the user's most recent question or command directly. If they ask about your identity, name, or role, answer that question before offering any assistance.
4.  **Disclaimer:** You are an AI, not a certified financial advisor. For significant advice (like investment or debt strategies), include a disclaimer: "Remember, it's a good idea to consult with a qualified financial professional before making major decisions."
5.  **Safety:** Never ask for sensitive personal data like bank account numbers or home addresses.
6.  **No Guarantees:** Do not promise specific financial outcomes. Frame advice as suggestions and education.
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
        
    context_parts.append("\nYour primary task now is to utilize the User's Financial Context immediately to answer their most recent question. DO NOT REPEAT THE GREETING OR INTRODUCTION. Proceed directly to the core topic based on the user's last message.")
 
    
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


def build_budget_optimization_prompt(analysis_data: dict) -> list:
    """
    Creates a detailed prompt for the AI to analyze a user's spending
    against their budgets AND the 50/30/20 rule, then provide optimization advice.
    The input is now the comprehensive analysis_data dictionary.
    """
    user_name = analysis_data.get('name', 'there')
    summary_text = json.dumps(analysis_data.get('financial_summary', {}))
    
    analysis_breakdown = f"""
    --- 50/30/20 Budget Rule Analysis ---
    Total Income: £{analysis_data.get('total_income', 0.00):.2f}
    Total Commitments: £{analysis_data.get('total_commitments', 0.00):.2f}
    
    - Essential (50% Target): ACTUAL £{analysis_data.get('actual_essential', 0.00):.2f} ({analysis_data.get('percent_essential', 0.00):.2f}%)
    - Discretionary (30% Target): ACTUAL £{analysis_data.get('actual_discretionary', 0.00):.2f} ({analysis_data.get('percent_discretionary', 0.00):.2f}%)
    - Savings/Debt Payoff (20% Target): ACTUAL £{analysis_data.get('actual_savings', 0.00):.2f} ({analysis_data.get('percent_savings', 0.00):.2f}%)
    """

    prompt = f"""
    You are an expert financial analyst named Reho, specializing in the 50/30/20 budget rule. Your task is to provide a structured optimization report.

    **User's Financial Data (Full Context):**
    {summary_text}
    
    **CRITICAL ANALYSIS DATA:**
    {analysis_breakdown}

    **Instructions:**
    1.  **Analyze 50/30/20:** Use the Critical Analysis Data to assess if the user is over or under the 50/30/20 targets. Identify the largest discrepancy.
    2.  **Analyze Budget vs. Actuals:** Also consider their manually defined budgets and expenses.
    3.  **Generate a High-Level Summary:** Write a 1-2 sentence summary of their overall budget health and 50/30/20 adherence.
    4.  **Provide Actionable Insights:** Generate 3 to 5 specific, actionable insights. Each insight must include:
        - `insight`: A clear observation (e.g., "Spending exceeds 50% Essential target by 5%").
        - `suggestion`: A concrete step to reallocate funds to hit the 50/30/20 goal.
        - `category`: The relevant category (e.g., "Essential", "Discretionary").
    5.  **Format Your Response as a VALID JSON object.** The JSON must match this exact structure:
        {{
            "summary": "Your main finding goes here, referencing the 50/30/20 rule.",
            "insights": [
                {{
                    "insight": "Observation about 50/30/20 or a budget vs. actual discrepancy.",
                    "suggestion": "A concrete action the user can take to balance their budget.",
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
    4.  **Format Your Response as a VALID JSON object.** The JSON must match this exact structure:
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
    1.  Analyze the data for potential issues suchs as:
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

def build_savings_tip_prompt(user_id: str, calculator_data: dict, financial_summary: dict) -> list:
    """
    Creates a prompt for the AI to generate a single, contextual financial tip 
    based on the user's current situation and a new savings calculation.
    """
    user_name = financial_summary.get('name', 'there')
    summary_text = json.dumps(financial_summary) 
    calc_text = json.dumps(calculator_data)     

    prompt = f"""
    You are Reho, an AI financial coach. A user named {user_name} has just run a SAVINGS CALCULATOR.

    **User's Current Financial Context (Use this for relevance):**
    {summary_text}

    **User's New Calculation Inputs:**
    {calc_text}
    
    **CRITICAL TASK:** Generate ONE single, highly contextual, and actionable Financial Tip for the user.
    
    - The tip should connect the calculator's goal to their existing financial data.
    - Example: If the 'Amount' is high, suggest they check their high-interest 'Debts' first.
    - Example: If the 'Return Rate' is low, suggest they aim higher based on their 'Income'.
    
    Format your response as a simple JSON object:
    {{"tip": "Your single, concise, and personalized financial tip goes here."}}
    
    Now, generate the JSON response.
    """
    
    return [{"role": "user", "content": prompt}]

def build_loan_tip_prompt(user_id: str, calculator_data: dict, financial_summary: dict) -> list:
    user_name = financial_summary.get('name', 'there')
    summary_text = json.dumps(financial_summary) 
    calc_text = json.dumps(calculator_data)     

    prompt = f"""
    You are Reho, an AI financial coach. A user named {user_name} has just run a LOAN REPAYMENT CALCULATOR.

    **User's Current Financial Context (Use this for relevance):**
    {summary_text}

    **User's Calculation Inputs (Principal: {calculator_data.get('principal'):.2f}, Rate: {calculator_data.get('annualInterestRate')}%):**
    {calc_text}
    
    **CRITICAL TASK:** Generate ONE single, highly contextual, and actionable Financial Tip focused on loan management and its impact on the user's current debt load.
    
    - The tip should connect the loan terms to their existing income or debt-to-income ratio.
    
    Format your response as a simple JSON object:
    {{"tip": "Your single, concise, and personalized financial tip goes here."}}
    
    Now, generate the JSON response.
    """
    
    return [{"role": "user", "content": prompt}]

# --- NEW FUNCTION: Inflation (Future Value) Tip Prompt ---
def build_inflation_tip_prompt(user_id: str, calculator_data: dict, financial_summary: dict) -> list:
    user_name = financial_summary.get('name', 'there')
    summary_text = json.dumps(financial_summary) 
    calc_text = json.dumps(calculator_data)     

    prompt = f"""
    You are Reho, an AI financial coach. A user named {user_name} has just run a FUTURE VALUE/INFLATION CALCULATOR.

    **User's Current Financial Context (Use this for relevance):**
    {summary_text}

    **User's Calculation Inputs (Initial: {calculator_data.get('initialAmount'):.2f}, Years: {calculator_data.get('yearsToProject')}):**
    {calc_text}
    
    **CRITICAL TASK:** Generate ONE single, highly contextual, and actionable Financial Tip focused on the impact of inflation on the user's savings goals.
    
    - The tip should connect the inflation rate to their existing 'Savings Goals' or 'Income'.
    
    Format your response as a simple JSON object:
    {{"tip": "Your single, concise, and personalized financial tip goes here."}}
    
    Now, generate the JSON response.
    """
    
    return [{"role": "user", "content": prompt}]

# --- NEW FUNCTION: Inflation (Historical) Tip Prompt ---
def build_historical_tip_prompt(user_id: str, calculator_data: dict, financial_summary: dict) -> list:
    user_name = financial_summary.get('name', 'there')
    summary_text = json.dumps(financial_summary) 
    calc_text = json.dumps(calculator_data)     

    prompt = f"""
    You are Reho, an AI financial coach. A user named {user_name} has just run a HISTORICAL INFLATION CALCULATOR.

    **User's Current Financial Context (Use this for relevance):**
    {summary_text}

    **User's Calculation Inputs (Amount: {calculator_data.get('amount'):.2f}, From Year: {calculator_data.get('fromYear')}):**
    {calc_text}
    
    **CRITICAL TASK:** Generate ONE single, highly contextual, and actionable Financial Tip focused on the change in buying power and how it should affect the user's current expense habits.
    
    - The tip should warn about the erosion of funds and suggest a change in spending/saving based on the user's expenses.
    
    Format your response as a simple JSON object:
    {{"tip": "Your single, concise, and personalized financial tip goes here."}}
    
    Now, generate the JSON response.
    """
    
    return [{"role": "user", "content": prompt}]