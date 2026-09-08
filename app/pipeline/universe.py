# Curated 100-ticker signal universe — selected for high idiosyncratic news volume,
# reliable price reaction to company-specific events, and dense Benzinga/Alpaca coverage.
# Deliberately excludes utilities, REITs, gold miners, and commodity E&P (macro-dominated).
SIGNAL_UNIVERSE: list[str] = [
    # Technology — mega-cap platforms
    "AAPL",
    "MSFT",
    "NVDA",
    "GOOGL",
    "META",
    # Technology — cloud / SaaS
    "CRM",
    "NOW",
    "WDAY",
    "SNOW",
    "DDOG",
    "TEAM",
    # Technology — semiconductors (selective; analog/auto separated from AI chips)
    "AMD",
    "QCOM",
    "AVGO",
    "TXN",
    "MRVL",
    # Technology — cybersecurity
    "CRWD",
    "PANW",
    "ZS",
    # Technology — fintech / consumer tech
    "PYPL",
    "COIN",
    "SHOP",
    "UBER",
    # Technology — enterprise / infra
    "ORCL",
    "ADBE",
    "CSCO",
    "DELL",
    # Healthcare — large pharma
    "LLY",
    "ABBV",
    "MRK",
    "PFE",
    "BMY",
    # Healthcare — biotech (FDA binary events = cleanest idiosyncratic signals)
    "AMGN",
    "GILD",
    "REGN",
    "VRTX",
    "BIIB",
    "MRNA",
    # Healthcare — medical devices
    "ISRG",
    "MDT",
    "EW",
    "SYK",
    "BSX",
    # Healthcare — managed care
    "UNH",
    "ELV",
    "HUM",
    "CI",
    # Healthcare — specialty / health IT
    "VEEV",
    "DXCM",
    "IDXX",
    "ZTS",
    # Consumer Discretionary — e-commerce / streaming
    "AMZN",
    "NFLX",
    # Consumer Discretionary — restaurants (monthly comp sales = recurring catalyst)
    "MCD",
    "SBUX",
    "CMG",
    "YUM",
    # Consumer Discretionary — auto / EV
    "TSLA",
    "GM",
    "F",
    # Consumer Discretionary — retail
    "COST",
    "TGT",
    "LULU",
    # Consumer Discretionary — travel
    "BKNG",
    "MAR",
    "ABNB",
    # Financials — banks
    "JPM",
    "BAC",
    "GS",
    "MS",
    "WFC",
    # Financials — payments
    "V",
    "MA",
    # Financials — asset management / data
    "BLK",
    "SCHW",
    "SPGI",
    "MCO",
    # Financials — insurance (PGR: monthly loss ratios = recurring catalyst)
    "PGR",
    # Industrials — defense / aerospace (contract awards = textbook idiosyncratic signals)
    "LMT",
    "RTX",
    "NOC",
    "GD",
    "BA",
    # Industrials — machinery / logistics
    "CAT",
    "DE",
    "HON",
    "FDX",
    "UPS",
    # Energy — minimal; 5 highest-coverage names only
    "XOM",
    "CVX",
    "OXY",
    "SLB",
    "COP",
    # Consumer Staples — floor for eval segmentation
    "WMT",
    "PG",
    "KO",
    # Communications
    "DIS",
    "TMUS",
    "CMCSA",
    "EA",
]

assert len(SIGNAL_UNIVERSE) == 100, (
    f"Universe must be exactly 100 tickers, got {len(SIGNAL_UNIVERSE)}"
)
SIGNAL_UNIVERSE_SET: frozenset[str] = frozenset(SIGNAL_UNIVERSE)

# Company name keywords used for pre-LLM relevance filtering on RSS articles.
# Single-word or phrase match (case-insensitive). Tickers V, F, MA, GM, DE, EW, CI, GS, MS
# are too short/common for reliable text matching — covered here by name instead.
COMPANY_KEYWORDS: frozenset[str] = frozenset(
    [
        # Tech — mega-cap
        "apple",
        "microsoft",
        "nvidia",
        "google",
        "alphabet",
        "meta",
        "facebook",
        # Tech — cloud/SaaS
        "salesforce",
        "servicenow",
        "workday",
        "snowflake",
        "datadog",
        "atlassian",
        # Tech — semis
        "qualcomm",
        "broadcom",
        "texas instruments",
        "marvell",
        # Tech — cyber
        "crowdstrike",
        "palo alto",
        "zscaler",
        # Tech — fintech/consumer
        "paypal",
        "coinbase",
        "shopify",
        "uber",
        # Tech — enterprise/infra
        "oracle",
        "adobe",
        "cisco",
        "dell",
        # Healthcare — pharma
        "eli lilly",
        "abbvie",
        "merck",
        "pfizer",
        "bristol myers",
        "bristol-myers",
        # Healthcare — biotech
        "amgen",
        "gilead",
        "regeneron",
        "vertex",
        "biogen",
        "moderna",
        # Healthcare — devices
        "intuitive surgical",
        "medtronic",
        "edwards lifesciences",
        "stryker",
        "boston scientific",
        # Healthcare — managed care
        "unitedhealth",
        "elevance",
        "humana",
        "cigna",
        # Healthcare — specialty/health IT
        "veeva",
        "dexcom",
        "idexx",
        "zoetis",
        # Consumer Disc — ecommerce/streaming
        "amazon",
        "netflix",
        # Consumer Disc — restaurants
        "mcdonald",
        "starbucks",
        "chipotle",
        "yum brands",
        # Consumer Disc — auto
        "tesla",
        "general motors",
        "ford motor",
        # Consumer Disc — retail
        "costco",
        "target",
        "lululemon",
        # Consumer Disc — travel
        "booking holdings",
        "marriott",
        "airbnb",
        # Financials — banks
        "jpmorgan",
        "jp morgan",
        "bank of america",
        "goldman sachs",
        "morgan stanley",
        "wells fargo",
        # Financials — payments
        "visa",
        "mastercard",
        # Financials — asset mgmt/data
        "blackrock",
        "charles schwab",
        "s&p global",
        "moody",
        # Financials — insurance
        "progressive",
        # Industrials — defense
        "lockheed martin",
        "raytheon",
        "northrop grumman",
        "general dynamics",
        "boeing",
        # Industrials — machinery/logistics
        "caterpillar",
        "deere",
        "honeywell",
        "fedex",
        # Energy
        "exxon",
        "chevron",
        "occidental",
        "schlumberger",
        "conocophillips",
        # Staples
        "walmart",
        "procter",
        "coca-cola",
        "coca cola",
        # Comms
        "disney",
        "t-mobile",
        "comcast",
        "electronic arts",
    ]
)
