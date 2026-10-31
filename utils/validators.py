import re
from datetime import datetime

EMAIL_REGEX = re.compile(r"^[\w\.-]+@([\w-]+\.)+[\w-]{2,4}$")
MONTH_REGEX = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
DATE_REGEX = re.compile(r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$")

ALLOWED_CATEGORIES = [
    "Salary",
    "Freelance",
    "Investments",
    "Food & Dining",
    "Groceries",
    "Housing & Rent",
    "Utilities",
    "Transportation",
    "Healthcare",
    "Entertainment",
    "Shopping",
    "Education",
    "Personal Care",
    "Travel",
    "Savings & Investments",
    "Other"
]

def validate_registration(data):
    errors = []
    if not data or not isinstance(data, dict):
        return False, ["Invalid request body"]

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not name or len(name) < 2:
        errors.append("Name must be at least 2 characters long.")
    if not email or not EMAIL_REGEX.match(email):
        errors.append("A valid email address is required.")
    if not password or len(password) < 6:
        errors.append("Password must be at least 6 characters long.")

    return (len(errors) == 0), errors

def validate_login(data):
    errors = []
    if not data or not isinstance(data, dict):
        return False, ["Invalid request body"]

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email:
        errors.append("Email is required.")
    if not password:
        errors.append("Password is required.")

    return (len(errors) == 0), errors

def validate_transaction(data):
    errors = []
    if not data or not isinstance(data, dict):
        return False, ["Invalid request body"]

    title = data.get("title", "").strip()
    amount = data.get("amount")
    t_type = data.get("type", "").strip().capitalize()
    category = data.get("category", "").strip()
    t_date = data.get("date", "").strip()

    if not title:
        errors.append("Transaction title is required.")

    try:
        amount_float = float(amount)
        if amount_float <= 0:
            errors.append("Amount must be greater than zero.")
    except (TypeError, ValueError):
        errors.append("Valid numeric amount is required.")

    if t_type not in ["Income", "Expense"]:
        errors.append("Type must be either 'Income' or 'Expense'.")

    if not category:
        errors.append("Category is required.")

    if not t_date or not DATE_REGEX.match(t_date):
        errors.append("Date must be in format YYYY-MM-DD.")
    else:
        try:
            datetime.strptime(t_date, "%Y-%m-%d")
        except ValueError:
            errors.append("Invalid date specified.")

    return (len(errors) == 0), errors

def validate_budget(data):
    errors = []
    if not data or not isinstance(data, dict):
        return False, ["Invalid request body"]

    month = data.get("month", "").strip()
    category = data.get("category", "").strip()
    limit_amount = data.get("limit_amount")

    if not month or not MONTH_REGEX.match(month):
        errors.append("Month must be in format YYYY-MM.")

    if not category:
        errors.append("Category is required.")

    try:
        limit_float = float(limit_amount)
        if limit_float <= 0:
            errors.append("Budget limit must be greater than zero.")
    except (TypeError, ValueError):
        errors.append("Valid numeric budget limit is required.")

    return (len(errors) == 0), errors
