"""Fake but realistic data so anyone can run the project without API keys."""

import numpy as np
import pandas as pd

SITE = "https://www.example.com"
TOPICS = ["mba", "gmat", "essay", "scholarship", "interview", "visa", "loan", "ranking"]
MODIFIERS = ["guide", "tips", "cost", "deadline", "requirements", "best", "how to", "vs"]


def _gsc(seed, shift=0.0):
    rng = np.random.default_rng(seed)
    rows = []
    for i, topic in enumerate(TOPICS):
        for j in range(6):
            page = f"{SITE}/{topic}/{topic}-{MODIFIERS[j]}".replace(" ", "-")
            for mod in rng.choice(MODIFIERS, size=4, replace=False):
                query = f"{topic} {mod}"
                position = max(1.0, rng.gamma(2.2, 4.5) - shift * ((i % 3) - 1))
                impressions = int(rng.integers(80, 4000) / (1 + position / 15))
                ctr = max(0.001, 0.3 / position ** 1.1 * rng.uniform(0.4, 1.2))
                if topic in ("loan", "ranking"):  # weak titles, so low CTR shows up
                    ctr *= 0.25
                clicks = int(impressions * ctr)
                rows.append([page, query, clicks, impressions, clicks / max(impressions, 1), position])
    return pd.DataFrame(rows, columns=["page", "query", "clicks", "impressions", "ctr", "position"])


def gsc_current():
    return _gsc(seed=7, shift=1.5)


def gsc_previous():
    return _gsc(seed=7, shift=0.0)


def ga4():
    rng = np.random.default_rng(11)
    pages = gsc_current()["page"].unique()
    rows = []
    for p in pages:
        sessions = int(rng.integers(20, 1500))
        rows.append({
            "landing_page": p.replace(SITE, ""),
            "sessions": sessions,
            "engaged_sessions": int(sessions * rng.uniform(0.4, 0.75)),
            "key_events": float(int(sessions * rng.uniform(0.0, 0.05))),
        })
    return pd.DataFrame(rows)
