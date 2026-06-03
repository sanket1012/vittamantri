"""Category definitions and helpers for VittaMantri."""

CATEGORIES = {
    "Food & Dining": {"emoji": "🍔", "keywords": ["zomato", "swiggy", "restaurant", "food", "lunch", "dinner", "breakfast", "cafe", "hotel", "chai", "biryani"]},
    "Groceries": {"emoji": "🛒", "keywords": ["dmart", "bigbasket", "grocery", "vegetables", "fruits", "milk", "supermarket", "blinkit", "zepto"]},
    "Transport": {"emoji": "🚗", "keywords": ["petrol", "diesel", "uber", "ola", "auto", "bus", "metro", "fuel", "rapido", "parking"]},
    "Rent & Housing": {"emoji": "🏠", "keywords": ["rent", "maintenance", "society", "electricity", "water", "housing"]},
    "Health & Medical": {"emoji": "💊", "keywords": ["medicine", "doctor", "hospital", "pharmacy", "medical", "health", "clinic", "apollo"]},
    "Entertainment": {"emoji": "🎬", "keywords": ["netflix", "prime", "hotstar", "movie", "cinema", "pvr", "spotify", "youtube", "game"]},
    "Shopping": {"emoji": "👗", "keywords": ["amazon", "flipkart", "myntra", "clothes", "dress", "shoes", "shirt", "meesho", "ajio"]},
    "Subscriptions": {"emoji": "📱", "keywords": ["subscription", "recharge", "jio", "airtel", "vi", "plan", "mobile", "internet"]},
    "Education": {"emoji": "📚", "keywords": ["course", "udemy", "fees", "books", "coaching", "tuition", "school", "college"]},
    "EMI & Loans": {"emoji": "💸", "keywords": ["emi", "loan", "credit card", "bajaj", "hdfc", "icici", "emi payment"]},
    "Investment & SIP": {"emoji": "🏦", "keywords": ["sip", "mutual fund", "stocks", "zerodha", "groww", "gold", "fd", "ppf", "investment"]},
    "Salary & Income": {"emoji": "💰", "keywords": ["salary", "income", "credited", "received", "payment received", "freelance", "bonus"]},
    "Gifts & Misc": {"emoji": "🎁", "keywords": ["gift", "donation", "misc", "other", "random"]},
    "Utilities & Bills": {"emoji": "⚡", "keywords": ["electricity", "gas", "water bill", "wifi", "broadband", "insurance", "lic"]},
}

CATEGORY_NAMES = list(CATEGORIES.keys())
DEFAULT_CATEGORY = "Gifts & Misc"

SUBCATEGORY_MAP: dict[str, list[str]] = {
    "Food & Dining": ["Delivery", "Dining Out", "Snacks", "Beverages"],
    "Groceries": ["Vegetables", "Dairy", "Household", "Fruits"],
    "Transport": ["Fuel", "Cab", "Auto", "Public Transport", "Parking"],
    "Shopping": ["Clothes", "Electronics", "Home Decor", "Beauty", "Accessories"],
    "Health & Medical": ["Medicine", "Doctor Visit", "Lab Test", "Insurance"],
    "Entertainment": ["OTT", "Movies", "Events", "Games"],
    "Utilities & Bills": ["Electricity", "Internet", "Gas", "Water"],
    "Investment & SIP": ["Mutual Fund", "Stocks", "Gold", "FD", "PPF"],
    "EMI & Loans": ["Home Loan", "Personal Loan", "Credit Card", "Vehicle Loan"],
}


def category_emoji(category: str) -> str:
    return CATEGORIES.get(category, CATEGORIES[DEFAULT_CATEGORY])["emoji"]


def fuzzy_match_category(text: str, extra_names: list[str] | None = None) -> str | None:
    """Return the closest known category name for *text*, or None if no clear match.

    Checks built-in categories first, then any extra (custom) names passed in.
    Matching priority (stops at first hit):
    1. Exact match (case-insensitive)
    2. Known category starts with the input
    3. Input is contained within a known category name
    4. Known category name is contained within the input
    """
    if not text:
        return None
    lower = text.strip().lower()
    all_names = CATEGORY_NAMES + [n for n in (extra_names or []) if n not in CATEGORY_NAMES]
    for name in all_names:
        if name.lower() == lower:
            return name
    for name in all_names:
        if name.lower().startswith(lower):
            return name
    for name in all_names:
        if lower in name.lower():
            return name
    for name in all_names:
        if name.lower() in lower:
            return name
    return None


def build_categories_prompt_str(all_categories: list[dict]) -> str:
    """Return a compact inline string for injecting into LLM prompts.

    Format: "Food & Dining (Delivery, Dining Out), Transport (Fuel, Cab), Pet Care, ..."
    """
    parts = []
    for cat in all_categories:
        name = cat["name"]
        subs = cat.get("subcategories", [])
        parts.append(f"{name} ({', '.join(subs)})" if subs else name)
    return ", ".join(parts)


def infer_category(text: str, transaction_type: str = "expense") -> str:
    lower_text = (text or "").lower()
    if transaction_type == "income":
        return "Salary & Income"
    for name, meta in CATEGORIES.items():
        if any(keyword in lower_text for keyword in meta["keywords"]):
            return name
    return DEFAULT_CATEGORY
