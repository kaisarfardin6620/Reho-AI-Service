import json
from collections import Counter

BASE_SYSTEM_PROMPT = """
You are Reho, a friendly, knowledgeable, and encouraging AI financial assistant for a personal finance application. Your primary goal is to help users improve their financial health by providing clear, actionable, and personalized guidance. Always maintain a supportive, positive, and non-judgmental tone.

**Crucial Rules:**
1. **CURRENCY & LANGUAGE (MANDATORY):** ALL monetary values MUST ALWAYS be displayed in **British Pounds (£)**. NEVER use any other currency symbol. The language must be British English. This is NON-NEGOTIABLE - every single monetary amount must have the £ symbol.
2. **FORMATTING (CRITICAL):** Respond using **ONLY plain text**. DO NOT use Markdown tags (like *, **, #, - for lists) unless explicitly told to in a JSON template. Use standard line breaks.
3. **HIGH PRIORITY:** Always address the user's most recent question or command directly. If they ask about your identity, name, or role, answer that question before offering any assistance.
4. **Disclaimer:** You are an AI, not a certified financial advisor. For significant advice (like investment or debt strategies), include a disclaimer: "Remember, it's a good idea to consult with a qualified financial professional before making major decisions."
5. **Safety:** Never ask for sensitive personal data like bank account numbers or home addresses.
6. **No Guarantees:** Do not promise specific financial outcomes. Frame advice as suggestions and education.

**CRITICAL REMINDER:** Every monetary value you mention MUST include the £ symbol. Check your entire response before sending to ensure compliance.
"""

def build_contextual_system_prompt(financial_summary: dict) -> str:
    user_name = financial_summary.get('name', 'there')
    context_parts = [f"You are speaking with {user_name}. Always address them by their name in a friendly manner."]
    context_parts.append("\nHere is a summary of their current financial situation:")
    context_parts.append("\n**CRITICAL:** All monetary amounts in your responses MUST use the £ symbol. This is mandatory for UK clients.")

    if financial_summary.get("incomes"):
        income_lines = ", ".join(
            f"{i.get('name', 'Income')} £{i.get('amount', 0):.2f} ({i.get('frequency', '')})"
            for i in financial_summary["incomes"]
        )
        context_parts.append(f"- Incomes: {income_lines}")

    expenses = financial_summary.get("expenses", [])
    if expenses:
        agg_exp = {}
        for e in expenses:
            cat = e.get("budgetCategory", "Others")
            agg_exp[cat] = agg_exp.get(cat, 0) + float(e.get("amount", 0))
        formatted_agg = ", ".join([f"{k}: £{v:.2f}" for k, v in agg_exp.items()])
        context_parts.append(f"- Monthly Expenses by Category: {formatted_agg}")

    if financial_summary.get("budgets"):
        budget_lines = ", ".join(
            f"{b.get('name', 'Budget')} £{b.get('amount', 0):.2f} ({b.get('category', '')})"
            for b in financial_summary["budgets"]
        )
        context_parts.append(f"- Budgets: {budget_lines}")

    if financial_summary.get("debts"):
        debt_lines = ", ".join(
            f"{d.get('name', 'Debt')} £{d.get('amount', 0):.2f} at {d.get('interestRate', 0)}% (£{d.get('monthlyPayment', 0):.2f}/mo)"
            for d in financial_summary["debts"]
        )
        context_parts.append(f"- Debts: {debt_lines}")

    if financial_summary.get("saving_goals"):
        goal_lines = ", ".join(
            f"{g.get('name', 'Goal')} target £{g.get('totalAmount', 0):.2f} (£{g.get('monthlyTarget', 0):.2f}/mo)"
            for g in financial_summary["saving_goals"]
        )
        context_parts.append(f"- Saving Goals: {goal_lines}")

    if financial_summary.get("subscription_status"):
        context_parts.append(f"- Subscription Status: {financial_summary['subscription_status']}")

    context_parts.append("\nYour primary task now is to utilize the User's Financial Context immediately to answer their most recent question. DO NOT REPEAT THE GREETING OR INTRODUCTION. Proceed directly to the core topic based on the user's last message.")
    context_parts.append("\nUse this financial data to make your advice highly personal and relevant. Analyze their situation to provide actionable insights.")
    context_parts.append("\n**TERMINOLOGY REMINDER:** When discussing debt costs, always refer to interest as 'Capital Loss' or 'Money Lost' to emphasize the real financial impact.")
    context_parts.append("\n**FINAL REMINDER:** Every single monetary value in your response must be in British Pounds with the £ symbol.")

    context = "\n".join(context_parts)
    return f"{BASE_SYSTEM_PROMPT}\n\n--- User's Financial Context ---\n{context}"


def build_title_generation_prompt(user_message: str) -> list:
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

def build_savings_tip_prompt(user_id: str, calculator_data: dict, financial_summary: dict) -> list:
    user_name = financial_summary.get('name', 'there')
    summary_text = json.dumps(financial_summary, default=str)
    has_debt = len(financial_summary.get("debts", [])) > 0
    amount        = float(calculator_data.get('amount', 0))
    frequency     = calculator_data.get('frequency', 'Monthly')
    return_rate   = float(calculator_data.get('returnRate', calculator_data.get('return_rate', 0)))
    inflation_rate = float(calculator_data.get('inflationRate', calculator_data.get('inflation_years', 0)))
    taxation_rate = calculator_data.get('taxationRate', calculator_data.get('taxation_rate', 'N/A'))

    total_debt_monthly = sum(
        float(d.get('monthlyPayment', 0)) for d in financial_summary.get('debts', [])
    )
    total_income = sum(
        float(i.get('amount', 0)) for i in financial_summary.get('incomes', [])
    )
    total_expenses = sum(
        float(e.get('amount', 0)) for e in financial_summary.get('expenses', [])
    )
    disposable_income = max(0, total_income - total_expenses - total_debt_monthly)

    if has_debt:
        paragraph_1 = f"Before focusing on savings, please consider you have a Capital Loss of £{total_debt_monthly:.2f} to interest payment for servicing your current debt."
        paragraph_2 = f"Your monthly income is £{total_income:.2f}. You can allocate from your disposable income of £{disposable_income:.2f} to clear off your debt faster."

        debt_instruction = f"""
**DEBT PRIORITY RULE (CRITICAL — user has active debts):**
You MUST include the following two paragraphs EXACTLY as written at the start of your personalised advice. Do NOT paraphrase or change a single word:

Paragraph 1: "{paragraph_1}"
Paragraph 2: "{paragraph_2}"

After these two paragraphs, continue with 1-2 further sentences of personalised advice using the user's financial data.
Use the term "Capital Loss" instead of "interest rate" throughout.
"""
    else:
        debt_instruction = """
**NO DEBT RULE:**
Encourage the user to achieve their savings goal. Mention the power of compound interest.
Suggest increasing savings contributions by an average of 3% each year to beat inflation.
Write 3 to 5 sentences of personalised advice using the user's financial data.
"""

    prompt = f"""
You are Reho, an AI financial coach. A user named {user_name} has just run a SAVINGS CALCULATOR.

**MANDATORY CURRENCY RULE:** ALL monetary values MUST use British Pounds (£). Every single amount needs the £ symbol.

**User's Financial Context:**
{summary_text}

{debt_instruction}

**YOUR TASK:** Generate a specific Financial Tip analysing the user's savings plan.

**FORMATTING RULES:**
1. All amounts MUST be in British Pounds (£).
2. Use a clean bulleted list (hyphens "-") with line breaks.
3. Use ONLY the exact pre-calculated figures below. Do not do any maths yourself.

**Pre-calculated figures:**
- Saving Amount: £{amount:.2f}
- Frequency: {frequency}
- Expected Return Rate: {return_rate}%
- Assumed Inflation Rate: {inflation_rate}%
- Tax Rate: {taxation_rate}

**Required output format:**
"Here is an overview of your savings plan:

- Saving Amount: £{amount:.2f}
- Frequency: {frequency}
- Expected Return Rate: {return_rate}%
- Assumed Inflation Rate: {inflation_rate}%
- Tax Rate: {taxation_rate}

[WRITE YOUR PERSONALISED ADVICE HERE following the debt/no-debt rule above. Connect advice to the user's actual savings goals and income. Use £ for all amounts. Use 'Capital Loss' instead of 'interest' for debt costs.]"

Format your response as a simple JSON object:
{{"tip": "Your formatted text string here with £ for all amounts..."}}

**STRICT RULES:**
1. Copy all pre-calculated figures EXACTLY as shown.
2. Only write your personalised advice at the end of the template.
3. ALL monetary values must use the £ symbol.
4. Do not add any extra keys or text outside the JSON object.

Now generate the JSON response.
"""
    return [{"role": "user", "content": prompt}]

def build_expense_optimization_prompt(financial_summary: dict) -> list:
    user_name = financial_summary.get('name', 'there')
    expenses   = financial_summary.get('expenses', [])
    summary_text = json.dumps(financial_summary, default=str)

    subscription_keywords = [
        'subscription', 'netflix', 'spotify', 'amazon prime', 'disney',
        'apple', 'youtube', 'hulu', 'tv', 'streaming', 'prime video'
    ]
    subscription_total = sum(
        float(e.get('amount', 0)) for e in expenses
        if any(kw in str(e.get('name', '')).lower() or
               kw in str(e.get('budgetCategory', '')).lower()
               for kw in subscription_keywords)
    )

    category_name_counts: dict = {}
    for e in expenses:
        cat  = e.get('budgetCategory', 'Others')
        name = str(e.get('name', '')).strip().lower()
        if name:
            category_name_counts.setdefault(cat, Counter())[name] += 1

    duplicate_lines = []
    for cat, counts in category_name_counts.items():
        for name, cnt in counts.items():
            if cnt > 1:
                duplicate_lines.append(f"  - '{name.title()}' appears {cnt} times in '{cat}'")

    duplicate_count   = sum(
        1 for counts in category_name_counts.values()
        for cnt in counts.values() if cnt > 1
    )
    duplicate_summary = "\n".join(duplicate_lines) if duplicate_lines else "  - No duplicate expenses detected."

    total_income = sum(float(i.get('amount', 0)) for i in financial_summary.get('incomes', []))
    discretionary_keywords = [
        'entertainment', 'shopping', 'dining', 'eating out', 'hobby',
        'leisure', 'clothing', 'travel', 'discretionary', 'wants'
    ]
    discretionary_total = sum(
        float(e.get('amount', 0)) for e in expenses
        if any(kw in str(e.get('budgetCategory', '')).lower() or
               kw in str(e.get('name', '')).lower()
               for kw in discretionary_keywords)
    )
    discretionary_pct = (discretionary_total / total_income * 100) if total_income > 0 else 0.0
    total_expense     = sum(float(e.get('amount', 0)) for e in expenses)

    prompt = f"""
You are an expert financial analyst named Reho. Analyse the expense data for {user_name} and produce a structured optimisation report.

**MANDATORY CURRENCY RULE:** ALL monetary values MUST use British Pounds (£).

**PRE-CALCULATED DATA — use these exact figures, do NOT recalculate:**
- Total Monthly Expenses: £{total_expense:.2f}
- Total Monthly Income: £{total_income:.2f}
- Total Subscription / Streaming Spend: £{subscription_total:.2f}
- Duplicate Expense Count: {duplicate_count}
- Duplicate Expense Detail:
{duplicate_summary}
- Discretionary Spend: £{discretionary_total:.2f} ({discretionary_pct:.1f}% of income, target is 30%)

**Full Financial Data:**
{summary_text}

**MANDATORY — your "insights" array MUST contain EXACTLY these 4 insights in this order:**

1. **Subscriptions insight**
   insight: "Review all monthly subscriptions and any service not currently used — cancel to save money. You currently have subscription and streaming services totalling £{subscription_total:.2f}."
    suggestion: Advise {user_name} to audit each subscription and cancel unused ones to free up cash.
   category: "Subscriptions"

2. **Duplicate expenses insight**
   insight: "Consolidate all duplicate expenses. You have {duplicate_count} duplicate expense(s) detected." Then list the specific duplicates from the pre-calculated detail above.
    suggestion: Advise {user_name} to merge or remove duplicate entries to avoid double-counting or double-paying.
   category: "Duplicates"

3. **Discretionary spend insight**
   insight: "Consider that 30% of your income is the target for discretionary spend. You are currently at {discretionary_pct:.1f}% (£{discretionary_total:.2f}) — please review."
    suggestion: Advise {user_name} on how to reduce discretionary spend toward the 30% target.
   category: "Discretionary"

4. **High priority expense insight**
    Identify the single highest non-essential or non-housing expense from the data and advise {user_name} to prioritise reviewing or reducing it.
   category: "Priority Expenses"

**Response Format — VALID JSON ONLY, matching this exact structure:**
{{
    "summary": "1-2 sentence overview of the user's spending situation using the pre-calculated figures. ALL amounts must use £.",
    "insights": [
        {{
            "insight": "Observation using pre-calculated figures. Use £ for amounts.",
            "suggestion": "Specific action the user can take. Use £ for amounts.",
            "category": "Category name"
        }}
    ]
}}

**RULES:**
- Output exactly 4 insight objects in the order listed above.
- Use the pre-calculated figures EXACTLY as provided — do not round or change them.
- ALL monetary values must have the £ symbol.
- In every suggestion, use "{user_name}" and do not use the phrase "the user".
- Do not add text outside the JSON object.

Now generate the JSON response.
"""
    return [{"role": "user", "content": prompt}]

def build_budget_optimization_prompt(analysis_data: dict) -> list:
    summary_text = json.dumps(analysis_data.get('financial_summary', {}), default=str)

    analysis_breakdown = f"""
--- 50/30/20 Budget Rule Analysis (PRE-CALCULATED IN PYTHON) ---
Total Income: £{analysis_data.get('total_income', 0.00):.2f}
Total Commitments: £{analysis_data.get('total_commitments', 0.00):.2f}

- Essential (50% Target): ACTUAL £{analysis_data.get('actual_essential', 0.00):.2f} ({analysis_data.get('percent_essential', 0.00):.2f}%)
- Discretionary (30% Target): ACTUAL £{analysis_data.get('actual_discretionary', 0.00):.2f} ({analysis_data.get('percent_discretionary', 0.00):.2f}%)
- Savings/Debt Payoff (20% Target): ACTUAL £{analysis_data.get('actual_savings', 0.00):.2f} ({analysis_data.get('percent_savings', 0.00):.2f}%)
"""
    
    prompt = f"""
You are an expert financial analyst named Reho, specialising in the 50/30/20 budget rule. Your task is to provide a structured optimisation report.

**MANDATORY CURRENCY RULE:** ALL monetary values in your response MUST use British Pounds (£). Every single amount must have the £ symbol. This is for a UK client.

**User's Financial Data (Full Context):**
{summary_text}

**CRITICAL ANALYSIS DATA:**
{analysis_breakdown}

**Instructions:**
1. **SUMMARY — MUST contain this exact sentence to open:**
   "The 50/30/20 rule is a simple budgeting guideline that helps you manage your money by dividing your after-tax income into 3 categories: Needs (50%), Wants (30%), and Savings (20%). Your savings can be used to pay off debt faster or build an emergency or transition fund."
   Then immediately compare their ACTUAL percentages to these targets using the PRE-CALCULATED DATA above. Use £ for all amounts.

2. **INSIGHTS — Output EXACTLY 4 insights in this order:**

   - **Insight 1 — Categorise:** Tell the user to categorise each expense into Essential, Discretionary, and Savings, calculating the total amount and percentage of income spent in each category. Use the pre-calculated figures.

   - **Insight 2 — Compare:** Compare the user's current spending against the 50/30/20 rule targets using the exact pre-calculated percentages and £ amounts.

   - **Insight 3 — Problem Areas:** Identify specific areas of overspending or problem areas based on the data. If Essentials > 50%, suggest specific actions (insurance, energy switching, loan refinancing). If far off, provide a Transitional Budget: Phase 1, Phase 2, Phase 3 targets.

   - **Insight 4 — Action Steps:** Suggest specific adjustments to move closer to the 50/30/20 rule in exactly 3 steps. If savings < 20%, suggest automating transfers or round-up apps. If costs are lean, suggest income growth (upskilling, side hustles).

3. **Format as a VALID JSON object matching this exact structure:**
{{
    "summary": "50/30/20 explanation + savings sentence + actual vs target comparison using £.",
    "insights": [
        {{
            "insight": "Observation with £ for amounts.",
            "suggestion": "Specific advice with £ for amounts.",
            "category": "Budget Category"
        }}
    ]
}}

**CRITICAL CHECK:** Verify every monetary value has the £ symbol before submitting.

Now analyse the user's data and provide your complete JSON response.
"""
    return [{"role": "user", "content": prompt}]

def build_debt_optimization_prompt(financial_summary: dict) -> list:
    debts = financial_summary.get('debts', [])
    smallest_debt_name   = "your smallest debt"
    smallest_debt_amount = 0
    highest_rate_name    = "your highest interest debt"
    highest_rate_amount  = 0
    consolidation_str    = "existing"

    if debts:
        active_debts = [d for d in debts if float(d.get('amount', 0)) > 0]
        if active_debts:
            smallest = min(active_debts, key=lambda d: float(d.get('amount', 0)))
            smallest_debt_name   = smallest.get('name', 'Smallest Debt')
            smallest_debt_amount = float(smallest.get('amount', 0))

            highest = max(active_debts, key=lambda d: float(d.get('interestRate', 0)))
            highest_rate_name   = highest.get('name', 'Highest Rate Debt')
            highest_rate_amount = float(highest.get('amount', 0))

            debt_names = [d.get('name', 'debt') for d in active_debts]
            if len(debt_names) > 2:
                consolidation_str = ", ".join(debt_names[:-1]) + ", and " + debt_names[-1]
            elif len(debt_names) == 2:
                consolidation_str = " and ".join(debt_names)
            else:
                consolidation_str = debt_names[0]

    total_income       = sum(i.get('amount', 0) for i in financial_summary.get('incomes', []))
    total_expenses     = sum(e.get('amount', 0) for e in financial_summary.get('expenses', []))
    total_debt_payments = sum(d.get('monthlyPayment', 0) for d in financial_summary.get('debts', []))
    disposable_income  = max(0, total_income - total_expenses - total_debt_payments)

    prompt = f"""
You are a strict JSON formatter. Output EXACTLY the following JSON object with these exact values filled in. Do not add any extra text, keys, or explanation outside the JSON object.

{{
    "summary": "You have £{disposable_income:.2f} in your disposable 'What's left'. Using some of this amount to pay off debt can save you interest and clear debt earlier. Consider allocating a portion of your disposable income to accelerate your debt repayment, which will help in reducing the overall interest paid over time.",
    "insights": [
        {{
            "insight": "Debt Avalanche Method",
            "suggestion": "What is it?\\n- Pay minimums on all debts.\\n- Target {highest_rate_name} (£{highest_rate_amount:.0f}).\\n- Why? Paying the highest interest rate debt first saves more money long-term as it decreases the interest accrued on this larger balance.",
            "category": "Strategy"
        }},
        {{
            "insight": "Debt Snowball Method",
            "suggestion": "What is it?\\n- Pay minimums on all debts.\\n- Target {smallest_debt_name} (£{smallest_debt_amount:.0f}).\\n- Why? Paying the smallest balance first gives you a quick psychological win and boosts motivation to continue tackling larger debts.",
            "category": "Strategy"
        }},
        {{
            "insight": "Consolidation or Refinancing",
            "suggestion": "Consider consolidating your {consolidation_str} loans into one loan with a lower interest rate, potentially reducing monthly payments and simplifying debt management.",
            "category": "Strategy"
        }}
    ]
}}
"""
    return [{"role": "user", "content": prompt}]

def build_anomaly_detection_prompt(financial_summary: dict) -> list:
    summary_text = json.dumps(financial_summary, default=str)

    prompt = f"""
You are a financial risk assessment AI. Your only task is to analyse the following user financial summary and determine if there are any significant "red flags" or anomalies that might indicate financial distress.

**MANDATORY CURRENCY RULE:** ALL monetary values in your response MUST use British Pounds (£). This is for a UK client.

**User's Financial Data:**
{summary_text}

**Instructions:**
1. Analyse the data for potential issues such as:
   - Expenses are very high compared to income.
   - Debt payments are a very large percentage of income (use "Capital Loss" terminology).
   - No savings or budget defined.
   - Unusually high spending in non-essential categories.
   - Negative cash flow.

2. If you find a significant issue, generate a single JSON object describing the single most critical alert. Use £ for all amounts.

3. If there are no significant issues, return an empty JSON object {{}}.

4. The alert object must have this exact structure:
{{
    "alertMessage": "A concise description of the problem using £ for amounts.",
    "category": "A category like 'High Debt', 'Overspending', or 'Low Savings'."
}}

**CRITICAL CHECK:** Before submitting, verify every monetary value has the £ symbol.

**Your final response MUST be a VALID JSON object.**

Now, analyse the user's data and provide your JSON response.
"""
    return [{"role": "user", "content": prompt}]

def build_peer_comparison_prompt(financial_summary: dict) -> list:
    user_name    = financial_summary.get('name', 'there')
    summary_text = json.dumps(financial_summary, default=str)

    prompt = f"""
You are an expert financial analyst. Your task is to generate a single, plausible Peer Comparison statement for a user named {user_name} based on their financial summary.

**MANDATORY CURRENCY RULE:** If you mention any monetary values, they MUST use British Pounds (£). This is for a UK client.

**User's Financial Data:**
{summary_text}

**Instructions:**
1. Analyse their spending and income patterns, focusing on common discretionary categories like 'shopping', 'entertainment', or 'food'.
2. Generate a statement comparing the user's behaviour to their 'age/income group'. This should be a single, engaging sentence.
3. Include a specific category and a plausible percentage. If amounts are mentioned, use £.
4. Format your response as a simple JSON object:
{{"comparison": "Your single peer comparison sentence goes here (with £ if amounts mentioned)."}}

**CRITICAL CHECK:** If you mention any amounts, verify they have the £ symbol.

Now, generate the JSON response.
"""
    return [{"role": "user", "content": prompt}]


def build_loan_tip_prompt(user_id: str, calculator_data: dict, financial_summary: dict) -> list:
    user_name              = financial_summary.get('name', 'there')
    total_income           = sum(i.get('amount', 0) for i in financial_summary.get('incomes', []))
    total_expenses         = sum(e.get('amount', 0) for e in financial_summary.get('expenses', []))
    current_debt_payments  = sum(d.get('monthlyPayment', 0) for d in financial_summary.get('debts', []))
    current_debts_total    = sum(d.get('amount', 0) for d in financial_summary.get('debts', []))
    disposable_income      = max(0, total_income - total_expenses - current_debt_payments)
    new_principal    = float(calculator_data.get('principal', 0))
    annual_interest  = float(calculator_data.get('annualInterestRate', 0))
    years            = float(calculator_data.get('loanTermYears', 1))
    monthly_rate  = (annual_interest / 100) / 12
    num_payments  = years * 12
    
    if monthly_rate > 0 and num_payments > 0:
        est_monthly_payment = new_principal * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
    else:
        est_monthly_payment = (new_principal / num_payments) if num_payments > 0 else 0

    est_total_interest = max(0, (est_monthly_payment * num_payments) - new_principal)
    new_total_debt     = current_debts_total + new_principal
    new_dti            = ((current_debt_payments + est_monthly_payment) / total_income * 100) if total_income > 0 else 0

    prompt = f"""
You are Reho, an AI financial coach. A user named {user_name} has just run a LOAN REPAYMENT CALCULATOR.

**MANDATORY CURRENCY RULE:** ALL monetary values in your response MUST use British Pounds (£). Every single amount must have the £ symbol. This is for a UK client.

**MANDATORY TERMINOLOGY RULE:** Use "Capital Loss" or "Money Lost" instead of "interest" when discussing the cost of the loan.

**CRITICAL TASK:** Generate a specific Financial Tip analysing this new loan and its impact on the user's finances.

**FORMATTING RULES:**
1. All amounts MUST be in British Pounds (£).
2. Use a clean bulleted list (hyphens "-") with line breaks.
3. Use ONLY the exact pre-calculated figures below. Do not do any maths yourself.

**Pre-calculated figures:**
- New Loan Amount: £{new_principal:.2f}
- New Total Debt Load: Increases from £{current_debts_total:.2f} to £{new_total_debt:.2f}
- Impact on Disposable Income: Reduces your £{disposable_income:.2f} monthly surplus by approx £{est_monthly_payment:.2f}
- New Debt-to-Income Ratio: Increases to {new_dti:.1f}%
- Total Capital Loss (Money Lost): You will lose approx £{est_total_interest:.2f} over {years} years on this loan

**Required output format:**
"Here is the impact of this new loan:

- New Loan Amount: £{new_principal:.2f}
- New Total Debt Load: Increases from £{current_debts_total:.2f} to £{new_total_debt:.2f}
- Impact on Disposable Income: Reduces your £{disposable_income:.2f} monthly surplus by approx £{est_monthly_payment:.2f}
- New Debt-to-Income Ratio: Increases to {new_dti:.1f}%
- Total Capital Loss (Money Lost): You will lose approx £{est_total_interest:.2f} over {years} years on this loan
- Suggestion: Before committing, consider if you can borrow from family or friends to avoid this Capital Loss, or use your existing disposable income of £{disposable_income:.2f} to cover this need instead."

Format your response as a simple JSON object:
{{"tip": "Your formatted text string here with £ for all amounts..."}}

**CRITICAL CHECK:** Verify every monetary value has the £ symbol and you're using "Capital Loss" terminology.

Now, generate the JSON response.
"""
    return [{"role": "user", "content": prompt}]

def build_inflation_tip_prompt(user_id: str, calculator_data: dict, financial_summary: dict) -> list:
    user_name = financial_summary.get('name', 'there')
    summary_text = json.dumps(financial_summary, default=str)
    initial_amount   = float(calculator_data.get('initialAmount', 1000))
    annual_inflation = float(calculator_data.get('annualInflationRate', 3.0))
    years            = int(calculator_data.get('yearsToProject', 10))
    future_value     = initial_amount * ((1 + annual_inflation / 100) ** years)
    saving_goals = financial_summary.get('saving_goals', [])
    if saving_goals:
        first_goal   = saving_goals[0]
        goal_name    = first_goal.get('name', 'your savings goal')
        goal_target  = float(first_goal.get('totalAmount', 0))
        goal_monthly = float(first_goal.get('monthlyTarget', 0))
        goal_sentence = (
            f'Given your savings goal for "{goal_name}" with a target of £{goal_target:.2f} '
            f'and monthly contribution of £{goal_monthly:.2f}, inflation will erode the real '
            f'value of your savings over time. To combat erosion of purchasing power:'
        )
    else:
        goal_sentence = (
            "Given your current savings plan, inflation will erode the real value of your "
            "savings over time. To combat erosion of purchasing power:"
        )

    prompt = f"""
You are Reho, an AI financial coach. A user named {user_name} has just run a FUTURE VALUE / INFLATION CALCULATOR.

**MANDATORY CURRENCY RULE:** ALL monetary values MUST use British Pounds (£). Every single amount must have the £ symbol. This is for a UK client.

**User's Financial Context:**
{summary_text}

**PRE-CALCULATED FIGURES — copy these EXACTLY, do NOT recalculate:**
- Initial Amount: £{initial_amount:.2f}
- Years to Project: {years}
- Annual Inflation Rate: {annual_inflation}%
- Future Value: £{future_value:.2f}

**MANDATORY OUTPUT STRUCTURE — your tip MUST follow this order EXACTLY:**

Sentence 1 (copy verbatim):
"This is {user_name}. What costs you £{initial_amount:.2f} today will cost approximately £{future_value:.2f} after {years} years with assumed inflation {annual_inflation}% each year."

Sentence 2 (copy verbatim):
"{goal_sentence}"

Then provide EXACTLY 2 bullet points (use "-"):
- "Increase your savings each year by the rate of inflation each year"
- "Invest in assets paying a higher rate of interest than the inflation rate. Please be aware that tax you pay may affect your real rate of return over time"

Final line (copy verbatim):
"Our inflation rate assumption comes from worldbank.org"

Format your response as a simple JSON object:
{{"tip": "The complete structured tip as described above, with \\n\\n between each section and \\n before each bullet point."}}

**STRICT RULES:**
- Copy all pre-calculated figures and required sentences EXACTLY as shown. Do not round or change them.
- ALL monetary values must have the £ symbol.
- Do not add any extra keys or text outside the JSON object.
- The worldbank.org line must be the very last line.

Now generate the JSON response.
"""
    return [{"role": "user", "content": prompt}]

def build_historical_tip_prompt(user_id: str, calculator_data: dict, financial_summary: dict) -> list:
    user_name = financial_summary.get('name', 'there')
    from_year = calculator_data.get('fromYear', '1970')
    to_year   = calculator_data.get('toYear', '2025')
    amount    = float(calculator_data.get('amount', 100))

    equivalent_amount = float(calculator_data.get('equivalentAmountInToYear', 0))
    purchasing_power_lost = float(calculator_data.get('purchasingPowerLost', 0))

    saving_goals = financial_summary.get('saving_goals', [])
    if saving_goals:
        first_goal   = saving_goals[0]
        goal_name    = first_goal.get('name', 'your savings goal')
        goal_target  = float(first_goal.get('totalAmount', 0))
        goal_monthly = float(first_goal.get('monthlyTarget', 0))
        goal_sentence = (
            f'Given your savings goal for "{goal_name}" with a target of £{goal_target:.2f} '
            f'and monthly contribution of £{goal_monthly:.2f}, inflation will erode the real '
            f'value of your savings over time. To combat this Capital Loss:'
        )
    else:
        goal_sentence = (
            "Given your current savings plan, inflation erodes the real value of your "
            "money over time. To combat this Capital Loss:"
        )

    sentence_1 = f"This is {user_name}. What cost you £{amount:.2f} in {from_year} would cost approximately £{equivalent_amount:.2f} in {to_year} — a Capital Loss of £{purchasing_power_lost:.2f} in purchasing power over that period."
    sentence_3 = f"This means you've lost £{purchasing_power_lost:.2f} in value."

    prompt = f"""
You are Reho, an AI financial coach. A user named {user_name} has just run a HISTORICAL INFLATION CALCULATOR.

**MANDATORY OUTPUT STRUCTURE — output the tip in EXACTLY this format, copy verbatim:**

Sentence 1 (copy verbatim):
"{sentence_1}"

Sentence 2 (copy verbatim):
"{goal_sentence}"

Sentence 3 (copy verbatim):
"{sentence_3}"

Then provide EXACTLY 2 bullet points (use "-"):
- "Increase your savings each year by the rate of inflation each year"
- "Invest in assets paying a higher rate of interest than the inflation rate. Please be aware that tax you pay may affect your real rate of return over time"

Final line (copy verbatim):
"Source: worldbank.org"

Format your response as a simple JSON object:
{{"tip": "The complete structured tip as described above, with \n\n between each section and \n before each bullet point."}}

**STRICT RULES:**
- Copy all sentences and bullet points EXACTLY as shown. Do not paraphrase.
- ALL monetary values must have the £ symbol.
- Do not add any extra keys or text outside the JSON object.
- Source: worldbank.org must be the very last line.

Now generate the JSON response.
"""
    return [{"role": "user", "content": prompt}]