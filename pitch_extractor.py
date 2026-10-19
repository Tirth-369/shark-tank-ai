
import re

INDUSTRY_KEYWORDS = {
    "Food and Beverage": ["food", "beverage", "snack", "chips", "momo", "restaurant", "kitchen", "drink", "coffee", "tea", "bakery", "meal", "sauce", "masala", "grocery"],
    "Technology/Software": ["software", "saas", "app", "application", "platform", "artificial intelligence", "machine learning", "cloud", "algorithm", "tech", "technology", "automation"],
    "Medical/Health": ["health", "medical", "healthcare", "doctor", "hospital", "diagnostic", "medicine", "therapy", "wellness", "clinical"],
    "Beauty/Fashion": ["beauty", "fashion", "clothing", "apparel", "skincare", "skin care", "cosmetic", "makeup", "jewellery", "jewelry", "wear", "dress"],
    "Children/Education": ["education", "educational", "course", "learning", "school", "student", "children", "kids", "teaching", "training"],
    "Fitness/Sports/Outdoors": ["fitness", "gym", "sports", "sport", "workout", "athlete", "running", "cycling", "outdoor", "yoga"],
    "Vehicles/Electrical Vehicles": ["vehicle", "ev", "electric vehicle", "e-bike", "bike", "scooter", "automobile", "mobility", "car", "motorcycle"],
    "Electronics": ["electronics", "electronic", "gadget", "device", "sensor", "wearable", "smartwatch", "camera"],
    "Hardware": ["hardware", "machine", "machinery", "tool", "equipment", "robot", "industrial"],
    "Agriculture": ["agriculture", "agri", "farm", "farming", "farmer", "crop", "soil", "irrigation", "fertilizer"],
    "Animal/Pets": ["pet", "pets", "dog", "cat", "animal", "veterinary", "vet"],
    "Green/CleanTech": ["clean energy", "cleantech", "solar", "renewable", "sustainable", "sustainability", "recycling", "waste management", "green energy", "water purification"],
    "Lifestyle/Home": ["home", "lifestyle", "furniture", "decor", "kitchenware", "household", "interior"],
    "Entertainment": ["entertainment", "media", "music", "movie", "gaming", "game", "content", "creator"],
    "Business Services": ["business service", "b2b", "consulting", "agency", "logistics", "marketing"],
    "Manufacturing": ["manufacturing", "manufacturer", "factory", "production"],
}

STATE_ALIASES = {
    "andhra pradesh":"Andhra Pradesh","arunachal pradesh":"Arunachal Pradesh","assam":"Assam","bihar":"Bihar",
    "chhattisgarh":"Chhattisgarh","goa":"Goa","gujarat":"Gujarat","haryana":"Haryana",
    "himachal pradesh":"Himachal Pradesh","jharkhand":"Jharkhand","karnataka":"Karnataka","kerala":"Kerala",
    "madhya pradesh":"Madhya Pradesh","maharashtra":"Maharashtra","manipur":"Manipur","meghalaya":"Meghalaya",
    "mizoram":"Mizoram","nagaland":"Nagaland","odisha":"Odisha","punjab":"Punjab","rajasthan":"Rajasthan",
    "sikkim":"Sikkim","tamil nadu":"Tamil Nadu","telangana":"Telangana","tripura":"Tripura",
    "uttar pradesh":"Uttar Pradesh","uttarakhand":"Uttarakhand","west bengal":"West Bengal","delhi":"Delhi"
}

def num(x):
    try:
        return float(str(x).replace(",", "").strip())
    except:
        return None

def money_value(value, unit):
    value = num(value)
    if value is None: return None
    unit = (unit or "").lower()
    if unit in ("crore","crores","cr"):
        return value * 100.0
    if unit == "million":
        return value * 10.0
    if unit in ("thousand","k"):
        return value * 0.1
    return value

def find_money(text, patterns):
    for pat in patterns:
        m = re.search(pat, text, re.I)
        if m:
            return money_value(m.group(1), m.group(2) if len(m.groups()) >= 2 else "")
    return None

def extract_pitch(text):
    t = " ".join(str(text or "").split())
    low = t.lower()

    out = {
        "industry": None, "state": None, "ask": None, "equity": None,
        "valuation": None, "revenue": None, "monthly_sales": None,
        "gross_margin": None, "net_margin": None, "ebitda": None,
        "started_in": None, "presenters": None, "age": None, "skus": None,
        "bootstrapped": None, "patents": None, "cash_burn": None,
        "customers": None, "users": None, "growth": None,
        "business_model": None, "traction": [], "signals": [],
        "detected_fields": [], "estimated_fields": []
    }

    # Industry
    scores = []
    for industry, words in INDUSTRY_KEYWORDS.items():
        hits = sum(bool(re.search(r"(?<![a-z])"+re.escape(w)+r"(?![a-z])", low)) for w in words)
        if hits:
            scores.append((hits, industry))
    if scores:
        out["industry"] = max(scores)[1]
        out["detected_fields"].append("industry")

    # State
    for key, value in sorted(STATE_ALIASES.items(), key=lambda x: -len(x[0])):
        if re.search(r"\b"+re.escape(key)+r"\b", low):
            out["state"] = value
            out["detected_fields"].append("state")
            break

    # Ask amount: explicitly support "asking for", "ask of", "seeking", "raise".
    out["ask"] = find_money(low, [
        r"(?:asking\s+for|ask(?:ing)?\s+of|seeking|raising|raise|looking\s+for|investment\s+of)\s*(?:₹|rs\.?|inr)?\s*([\d,.]+)\s*(crore|crores|cr|lakh|lakhs|million|thousand|k)?",
        r"(?:₹|rs\.?|inr)\s*([\d,.]+)\s*(crore|crores|cr|lakh|lakhs|million|thousand|k)?\s*(?:for|as)\s+(?:an?\s+)?(?:ask|investment)"
    ])
    if out["ask"] is not None: out["detected_fields"].append("ask")

    # Equity
    m = re.search(r"(?:for|in exchange for|against|at)\s*([\d,.]+)\s*%\s*(?:equity|stake|ownership)?", low)
    if not m:
        m = re.search(r"([\d,.]+)\s*%\s*(?:equity|stake|ownership)", low)
    if m:
        out["equity"] = num(m.group(1)); out["detected_fields"].append("equity")

    # Valuation
    out["valuation"] = find_money(low, [
        r"(?:requested\s+)?valuation\s*(?:of|is|at|:)?\s*(?:₹|rs\.?|inr)?\s*([\d,.]+)\s*(crore|crores|cr|lakh|lakhs|million|thousand|k)?",
        r"(?:valued\s+at|company\s+is\s+valued\s+at)\s*(?:₹|rs\.?|inr)?\s*([\d,.]+)\s*(crore|crores|cr|lakh|lakhs|million|thousand|k)?"
    ])
    if out["valuation"] is not None: out["detected_fields"].append("valuation")

    # Revenue
    out["revenue"] = find_money(low, [
        r"(?:annual|yearly)\s+revenue\s*(?:of|is|:)?\s*(?:₹|rs\.?|inr)?\s*([\d,.]+)\s*(crore|crores|cr|lakh|lakhs|million|thousand|k)?",
        r"revenue\s*(?:of|is|:)?\s*(?:₹|rs\.?|inr)?\s*([\d,.]+)\s*(crore|crores|cr|lakh|lakhs|million|thousand|k)?",
        r"(?:₹|rs\.?|inr)\s*([\d,.]+)\s*(crore|crores|cr|lakh|lakhs|million|thousand|k)?\s*(?:annual|yearly)?\s*revenue"
    ])
    if out["revenue"] is not None: out["detected_fields"].append("revenue")

    # Monthly sales
    out["monthly_sales"] = find_money(low, [
        r"(?:monthly\s+sales|sales\s+per\s+month)\s*(?:of|is|:)?\s*(?:₹|rs\.?|inr)?\s*([\d,.]+)\s*(crore|crores|cr|lakh|lakhs|million|thousand|k)?"
    ])
    if out["monthly_sales"] is not None: out["detected_fields"].append("monthly_sales")

    # Margins / EBITDA
    for key, label in [("gross_margin","gross margin"),("net_margin","net margin")]:
        m = re.search(rf"{label}s?\s*(?:of|is|:)?\s*(-?[\d,.]+)\s*%", low)
        if m:
            out[key] = num(m.group(1)); out["detected_fields"].append(key)
    m = re.search(r"ebitda\s*(?:of|is|:)?\s*(?:₹|rs\.?|inr)?\s*([\d,.]+)\s*(crore|crores|cr|lakh|lakhs)?", low)
    if m:
        out["ebitda"] = money_value(m.group(1),m.group(2)); out["detected_fields"].append("ebitda")

    # Dates: support since/in/founded/started/launched.
    m = re.search(r"(?:since|founded\s+in|started\s+in|established\s+in|launched\s+in)\s+(19\d{2}|20\d{2})", low)
    if m:
        out["started_in"] = int(m.group(1)); out["detected_fields"].append("started_in")

    # Presenters / age
    m = re.search(r"(\d+)\s+(?:founders?|co-?founders?|entrepreneurs?|presenters?)\b", low)
    if m:
        out["presenters"] = int(m.group(1)); out["detected_fields"].append("presenters")
    m = re.search(r"(?:average\s+age|founders?\s+are|aged?)\s*(?:of|is|:)?\s*(\d{2})", low)
    if m:
        a=int(m.group(1)); out["age"] = 0 if a<30 else (1 if a<50 else 2); out["detected_fields"].append("age")

    # Customers/users
    m = re.search(r"([\d,.]+)\s*(k|thousand|million)?\s*(?:customers?|users?|subscribers?)", low)
    if m:
        value=num(m.group(1)); unit=(m.group(2) or "").lower()
        if unit in ("k","thousand"): value*=1000
        elif unit=="million": value*=1000000
        out["customers"] = int(value)
        out["detected_fields"].append("customers")

    # SKUs
    m = re.search(r"([\d,]+)\s*(?:skus|products|product\s+variants)", low)
    if m:
        out["skus"]=int(m.group(1).replace(",","")); out["detected_fields"].append("skus")

    # Boolean / business model
    if any(x in low for x in ["bootstrapped","self-funded","self funded"]):
        out["bootstrapped"]=1; out["detected_fields"].append("bootstrapped")
    elif any(x in low for x in ["venture funded","externally funded","funded by"]):
        out["bootstrapped"]=0; out["detected_fields"].append("bootstrapped")
    if any(x in low for x in ["patent","patented","intellectual property","proprietary"]):
        out["patents"]=1; out["detected_fields"].append("patents")
    if any(x in low for x in ["cash burn","burning cash","monthly burn"]):
        out["cash_burn"]=1; out["detected_fields"].append("cash_burn")

    if any(x in low for x in ["d2c","direct to consumer","direct-to-consumer"]):
        out["business_model"]="D2C"
    elif any(x in low for x in ["b2b","business to business"]):
        out["business_model"]="B2B"
    elif any(x in low for x in ["subscription","subscribers"]):
        out["business_model"]="Subscription"
    elif any(x in low for x in ["marketplace","platform"]):
        out["business_model"]="Marketplace"

    # Qualitative signals
    if any(x in low for x in ["revenue","sales","customers","users","orders"]): out["signals"].append("Commercial traction")
    if any(x in low for x in ["patent","proprietary","exclusive","unique technology","differentiated"]): out["signals"].append("Differentiation / defensibility")
    if any(x in low for x in ["profit","profitable","positive ebitda"]): out["signals"].append("Profitability")
    if any(x in low for x in ["loss","losses","burn","cash burn"]): out["signals"].append("Cash-burn / loss signal")
    if any(x in low for x in ["amazon","retail","distributor","distribution","offline stores"]): out["signals"].append("Distribution channel")
    if any(x in low for x in ["recurring","subscription","repeat customer","repeat purchase"]): out["signals"].append("Recurring/repeat revenue signal")
    if any(x in low for x in ["growth","growing","grew","month on month","mom"]): out["signals"].append("Growth signal")

    # Growth rate if explicitly stated.
    m = re.search(r"(?:grew|growth|growing)\s*(?:by|at)?\s*([\d,.]+)\s*%", low)
    if m: out["growth"]=num(m.group(1))

    # Coverage should reward fields, not just raw count; qualitative signals add a small amount.
    core = ["industry","state","ask","equity","valuation","revenue","monthly_sales","gross_margin",
            "net_margin","ebitda","started_in","presenters","age","skus","bootstrapped","patents","cash_burn"]
    found=sum(out[k] is not None for k in core)
    out["extraction_coverage"]=min(1.0, (found/17.0)+min(len(out["signals"]),4)*0.025)
    return out
