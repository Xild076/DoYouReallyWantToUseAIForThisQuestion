#!/usr/bin/env python3
import csv
import re
from collections import Counter
from itertools import product
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
IB_PATH = DATA_DIR / "ib_dataset.csv"
IC_PATH = DATA_DIR / "ic_dataset.csv"

# Idempotent target totals. Re-running the script will top datasets up to these counts.
IB_TARGET_TOTAL = {"0": 531_870, "1": 747_162}
IC_TARGET_TOTAL = {"0": 330_766, "1": 155_139}

POLITE_PREFIXES = [
    "",
    "quick question: ",
    "serious question: ",
    "for work: ",
    "for school: ",
    "need help: ",
    "can you tell me ",
    "in plain english, ",
    "please ",
    "be concise: ",
]

SUFFIXES = [
    "",
    "?",
    " please",
    " asap",
    " with a short answer",
    " in one line",
]

CITY_TOKENS = [
    "san jose",
    "san francisco",
    "oakland",
    "sacramento",
    "los angeles",
    "san diego",
    "fresno",
    "long beach",
    "anaheim",
    "bakersfield",
    "stockton",
    "irvine",
    "chula vista",
    "new york",
    "brooklyn",
    "queens",
    "manhattan",
    "buffalo",
    "rochester",
    "syracuse",
    "albany",
    "boston",
    "worcester",
    "springfield",
    "providence",
    "hartford",
    "new haven",
    "philadelphia",
    "pittsburgh",
    "allentown",
    "chicago",
    "aurora",
    "naperville",
    "rockford",
    "milwaukee",
    "madison",
    "green bay",
    "detroit",
    "grand rapids",
    "ann arbor",
    "minneapolis",
    "saint paul",
    "duluth",
    "st louis",
    "kansas city",
    "omaha",
    "des moines",
    "sioux falls",
    "fargo",
    "bismarck",
    "denver",
    "colorado springs",
    "boulder",
    "salt lake city",
    "provo",
    "boise",
    "seattle",
    "spokane",
    "tacoma",
    "portland",
    "eugene",
    "bend",
    "las vegas",
    "reno",
    "phoenix",
    "mesa",
    "tucson",
    "albuquerque",
    "el paso",
    "dallas",
    "fort worth",
    "austin",
    "san antonio",
    "houston",
    "plano",
    "corpus christi",
    "new orleans",
    "baton rouge",
    "jackson",
    "nashville",
    "memphis",
    "atlanta",
    "augusta",
    "charlotte",
    "raleigh",
    "greensboro",
    "durham",
    "columbia",
    "charleston",
    "savannah",
    "miami",
    "fort lauderdale",
    "orlando",
    "tampa",
    "st petersburg",
    "jacksonville",
    "tallahassee",
    "washington dc",
    "arlington",
    "richmond",
    "norfolk",
    "baltimore",
    "cleveland",
    "columbus",
    "cincinnati",
    "toledo",
    "louisville",
    "indianapolis",
    "lexington",
]

REGION_TOKENS = [
    "california",
    "texas",
    "new york",
    "florida",
    "illinois",
    "arizona",
    "washington",
    "oregon",
    "nevada",
    "colorado",
    "utah",
    "idaho",
    "massachusetts",
    "pennsylvania",
    "ohio",
    "michigan",
    "wisconsin",
    "minnesota",
    "georgia",
    "north carolina",
    "south carolina",
    "virginia",
    "maryland",
    "new jersey",
    "louisiana",
    "tennessee",
    "alabama",
    "kentucky",
    "indiana",
    "missouri",
    "kansas",
    "nebraska",
    "iowa",
    "oklahoma",
    "new mexico",
    "canada",
    "mexico",
    "united kingdom",
    "germany",
    "france",
    "italy",
    "spain",
    "portugal",
    "japan",
    "south korea",
    "india",
    "singapore",
    "australia",
    "new zealand",
    "brazil",
]

WEATHER_TIME_HINTS = [
    "",
    " today",
    " right now",
    " this afternoon",
    " tonight",
    " tomorrow morning",
    " this weekend",
    " this week",
]

WEATHER_TEMPLATES = [
    "what's the weather in {location}{time_hint}",
    "whats the weather in {location}{time_hint}",
    "what is the weather in {location}{time_hint}",
    "weather in {location}{time_hint}",
    "whats weather in {location}{time_hint}",
    "weather forecast for {location}{time_hint}",
    "forecast for {location}{time_hint}",
    "current weather in {location}{time_hint}",
    "temperature in {location}{time_hint}",
    "current temperature in {location}{time_hint}",
    "humidity in {location}{time_hint}",
    "wind speed in {location}{time_hint}",
    "chance of rain in {location}{time_hint}",
    "uv index in {location}{time_hint}",
    "sunrise time in {location}{time_hint}",
    "sunset time in {location}{time_hint}",
]

WEATHER_GENERIC_TEMPLATES = [
    "what's the weather{time_hint}",
    "whats the weather{time_hint}",
    "what is the weather{time_hint}",
    "current weather{time_hint}",
    "weather forecast{time_hint}",
]

TIME_TEMPLATES = [
    "what time is it in {location}",
    "current time in {location}",
    "time in {location}",
    "what day is it in {location}",
    "date in {location}",
]

TEAM_NAMES = [
    "49ers",
    "warriors",
    "giants",
    "lakers",
    "celtics",
    "knicks",
    "nets",
    "bulls",
    "heat",
    "mavericks",
    "spurs",
    "rockets",
    "astros",
    "dodgers",
    "padres",
    "yankees",
    "mets",
    "red sox",
    "eagles",
    "cowboys",
    "chiefs",
    "packers",
    "steelers",
    "ravens",
    "bills",
    "seahawks",
    "rams",
    "sharks",
    "maple leafs",
    "canadiens",
    "manchester city",
    "arsenal",
    "liverpool",
    "real madrid",
    "barcelona",
]

SCORE_TEMPLATES = [
    "score of the {team} game",
    "latest {team} score",
    "did the {team} win last night",
    "who won the {team} game",
    "what was the final score for {team}",
]

FACT_TOPICS = [
    "capital of california",
    "capital of texas",
    "capital of japan",
    "population of san jose",
    "population of california",
    "distance from san jose to san francisco",
    "distance from new york to boston",
    "height of mount everest",
    "speed of light",
    "boiling point of water",
    "time zone of california",
    "zip code for san jose",
    "opening hours for costco",
    "stock price of AAPL",
    "stock price of MSFT",
    "stock price of NVDA",
    "market cap of TSLA",
    "who is the ceo of apple",
    "who is the ceo of microsoft",
    "when was python created",
    "who invented the internet",
    "definition of inflation",
    "definition of machine learning",
    "definition of recursion",
    "translate hello to spanish",
    "translate thank you to french",
    "usd to eur exchange rate",
    "usd to jpy exchange rate",
    "kilometers to miles conversion",
    "celsius to fahrenheit conversion",
]

TASK_ACTIONS = [
    "write",
    "draft",
    "create",
    "build",
    "generate",
    "design",
    "compose",
    "implement",
    "code",
    "plan",
    "outline",
    "refactor",
    "optimize",
    "debug",
    "review",
    "prepare",
]

TASK_ARTIFACTS = [
    "python script",
    "javascript function",
    "react component",
    "sql query",
    "api endpoint",
    "dockerfile",
    "resume",
    "cover letter",
    "project proposal",
    "marketing email",
    "study schedule",
    "workout plan",
    "meal plan",
    "business plan",
    "blog post",
    "meeting agenda",
    "onboarding checklist",
    "social media calendar",
    "incident postmortem",
    "test plan",
]

TASK_TOPICS = [
    "weather alert system",
    "route optimization",
    "customer support automation",
    "inventory forecasting",
    "fraud detection",
    "recommendation engine",
    "sales dashboard",
    "supply chain analytics",
    "budget planning",
    "exam preparation",
    "data pipeline monitoring",
    "cloud cost reduction",
    "iot telemetry processing",
    "mobile app onboarding",
    "e-commerce checkout flow",
    "email segmentation",
    "content strategy",
    "market expansion",
    "hiring pipeline",
    "performance review process",
    "feature flag rollout",
    "code quality governance",
    "database migration",
    "observability setup",
    "kubernetes deployment",
    "security hardening",
    "compliance reporting",
    "a/b testing plan",
    "retention strategy",
    "pricing experiments",
]

HIGH_COMPLEXITY_ACTIONS = [
    "derive",
    "prove",
    "formalize",
    "quantify",
    "model",
    "evaluate",
    "benchmark",
    "synthesize",
    "decompose",
    "optimize",
    "analyze",
]

HIGH_COMPLEXITY_TOPICS = [
    "consensus safety in byzantine fault tolerant systems",
    "stability bounds for reinforcement learning with function approximation",
    "sample complexity tradeoffs in active learning",
    "latency tail mitigation in globally distributed databases",
    "quantization error propagation in transformer inference",
    "causal identification under latent confounding",
    "formal verification strategy for smart contracts",
    "adversarial robustness limits for vision transformers",
    "differential privacy budget allocation in federated learning",
    "multimodal retrieval calibration under domain shift",
    "zero-knowledge proof system performance bottlenecks",
    "game theoretic equilibria in repeated auctions",
    "catastrophic forgetting in continual learning",
    "traffic equilibrium in urban road networks",
    "credit assignment in long-horizon planning",
    "coherence constraints in large language models",
    "worst-case guarantees for online convex optimization",
    "power-law scaling behavior in pretraining corpora",
    "packet loss recovery dynamics in real-time media systems",
    "thermodynamic limits of data center cooling optimization",
]

HIGH_COMPLEXITY_CONSTRAINTS = [
    "with formal assumptions and proofs",
    "with asymptotic analysis and edge cases",
    "with quantitative metrics and failure modes",
    "including theoretical bounds and practical tradeoffs",
    "with a reproducible experimental design",
    "including ablation strategy and statistical significance checks",
    "with a risk model and mitigation plan",
    "using first-principles reasoning and rigorous notation",
]

CRITICAL_SIMPLE_SEEDS = [
    "whats the weather",
    "what's the weather",
    "what is the weather",
    "weather in san jose",
    "whats the weather in san jose",
    "what's the weather in san jose",
    "what is the weather in san jose right now",
    "forecast for san jose",
    "temperature in san jose",
]


def normalize(text: str) -> str:
    cleaned = " ".join(text.strip().split())
    # Remove common combinatoric duplicates from template mixing.
    cleaned = re.sub(r"\btoday\s+today\b", "today", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bright\s+now\s+right\s+now\b", "right now", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bplease\s+please\b", "please", cleaned, flags=re.IGNORECASE)
    return cleaned


def load_dataset(path: Path):
    rows = []
    seen_text = set()
    counts = Counter()
    with path.open("r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            text = normalize(row["text"])
            label = row["label"].strip()
            if not text or label not in {"0", "1"}:
                continue
            rows.append((text, label))
            seen_text.add(text)
            counts[label] += 1
    return rows, seen_text, counts


def write_dataset(path: Path, rows):
    with path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["text", "label"])
        writer.writeheader()
        for text, label in rows:
            writer.writerow({"text": text, "label": label})


def iter_locations():
    for city in CITY_TOKENS:
        yield city
        yield f"downtown {city}"
        yield f"{city} metro area"
    for city, region in product(CITY_TOKENS, REGION_TOKENS):
        yield f"{city}, {region}"
        yield f"{city} {region}"


def apply_style(base_prompt: str):
    for prefix, suffix in product(POLITE_PREFIXES, SUFFIXES):
        yield normalize(f"{prefix}{base_prompt}{suffix}")


def simple_lookup_prompts():
    for template, time_hint in product(WEATHER_GENERIC_TEMPLATES, WEATHER_TIME_HINTS):
        base = template.format(time_hint=time_hint)
        yield from apply_style(base)

    for template, location, time_hint in product(WEATHER_TEMPLATES, iter_locations(), WEATHER_TIME_HINTS):
        base = template.format(location=location, time_hint=time_hint)
        yield from apply_style(base)

    for template, location in product(TIME_TEMPLATES, iter_locations()):
        base = template.format(location=location)
        yield from apply_style(base)

    for template, team in product(SCORE_TEMPLATES, TEAM_NAMES):
        base = template.format(team=team)
        yield from apply_style(base)

    for topic in FACT_TOPICS:
        yield from apply_style(topic)
        yield from apply_style(f"what is the {topic}")
        yield from apply_style(f"what's the {topic}")


def task_prompts():
    task_suffixes = [
        "",
        " for beginners",
        " for a startup",
        " for a small business",
        " for an enterprise team",
        " with examples",
        " in bullet points",
        " with implementation steps",
        " with a timeline",
    ]
    for action, artifact, topic, suffix in product(TASK_ACTIONS, TASK_ARTIFACTS, TASK_TOPICS, task_suffixes):
        base = f"{action} a {artifact} for {topic}{suffix}"
        yield from apply_style(base)
        yield from apply_style(f"can you {action} a {artifact} for {topic}{suffix}")
        yield from apply_style(f"help me {action} a {artifact} for {topic}{suffix}")


def high_complexity_prompts():
    for action, topic, constraint in product(
        HIGH_COMPLEXITY_ACTIONS,
        HIGH_COMPLEXITY_TOPICS,
        HIGH_COMPLEXITY_CONSTRAINTS,
    ):
        base = f"{action} {topic} {constraint}"
        yield from apply_style(base)
        yield from apply_style(f"develop a rigorous framework to {action} {topic} {constraint}")
        yield from apply_style(f"provide a deep technical analysis to {action} {topic} {constraint}")


def append_generated(rows, seen_text, label: str, source_iter, target: int):
    if target <= 0:
        return 0
    added = 0
    for text in source_iter:
        if text in seen_text:
            continue
        rows.append((text, label))
        seen_text.add(text)
        added += 1
        if added >= target:
            return added
    return added


def ensure_seed_prompts(rows, seen_text, label: str, seeds):
    added = 0
    for seed in seeds:
        cleaned = normalize(seed)
        if cleaned in seen_text:
            continue
        rows.append((cleaned, label))
        seen_text.add(cleaned)
        added += 1
    return added


def expand_ib():
    rows, seen_text, before = load_dataset(IB_PATH)
    need_info = max(0, IB_TARGET_TOTAL["0"] - before["0"])
    need_task = max(0, IB_TARGET_TOTAL["1"] - before["1"])
    add_info = append_generated(rows, seen_text, "0", simple_lookup_prompts(), need_info)
    add_task = append_generated(rows, seen_text, "1", task_prompts(), need_task)
    seed_added = ensure_seed_prompts(rows, seen_text, "0", CRITICAL_SIMPLE_SEEDS)
    write_dataset(IB_PATH, rows)
    after = Counter(label for _, label in rows)
    return {"before": before, "after": after, "added": {"0": add_info + seed_added, "1": add_task}}


def expand_ic():
    rows, seen_text, before = load_dataset(IC_PATH)
    need_low = max(0, IC_TARGET_TOTAL["0"] - before["0"])
    need_high = max(0, IC_TARGET_TOTAL["1"] - before["1"])
    add_low = append_generated(rows, seen_text, "0", simple_lookup_prompts(), need_low)
    add_high = append_generated(rows, seen_text, "1", high_complexity_prompts(), need_high)
    seed_added = ensure_seed_prompts(rows, seen_text, "0", CRITICAL_SIMPLE_SEEDS)
    write_dataset(IC_PATH, rows)
    after = Counter(label for _, label in rows)
    return {"before": before, "after": after, "added": {"0": add_low + seed_added, "1": add_high}}


def main():
    ib_report = expand_ib()
    ic_report = expand_ic()

    print("IB dataset expansion")
    print(f"  before: {dict(ib_report['before'])}")
    print(f"  added:  {ib_report['added']}")
    print(f"  after:  {dict(ib_report['after'])}")

    print("IC dataset expansion")
    print(f"  before: {dict(ic_report['before'])}")
    print(f"  added:  {ic_report['added']}")
    print(f"  after:  {dict(ic_report['after'])}")

    print(f"Updated: {IB_PATH}")
    print(f"Updated: {IC_PATH}")


if __name__ == "__main__":
    main()
