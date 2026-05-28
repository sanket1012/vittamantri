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


def category_emoji(category: str) -> str:
    return CATEGORIES.get(category, CATEGORIES[DEFAULT_CATEGORY])["emoji"]


def infer_category(text: str, transaction_type: str = "expense") -> str:
    lower_text = (text or "").lower()
    if transaction_type == "income":
        return "Salary & Income"
    for name, meta in CATEGORIES.items():
        if any(keyword in lower_text for keyword in meta["keywords"]):
            return name
    return DEFAULT_CATEGORY
