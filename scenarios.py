"""
The runs your test needs. ← UNIT 4, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
the empty-search branch needs an impossible query. One about the fit card needs
the same item run more than once. Working that out is Milestone 3's first step,
and this file is where you write it down.

`run_eval.py` runs everything here five times and writes the run log — five
because your criteria are written out of five.

Three scenarios are filled in to show the shape. Add or change whatever your
own criteria need — these are a starting point, not a fixed set.
"""

SCENARIOS = [
    {
        # A query the data can match. Criterion 1.
        "name": "matching query completes",
        "query": "vintage graphic tee under $30",
        "wardrobe": "example",
        "criterion": 1,
    },
    {
        # A query nothing can match. Criterion 2 — the branch.
        "name": "impossible query stops early",
        "query": "designer ballgown size XXS under $5",
        "wardrobe": "example",
        "criterion": 2,
    },
    {
        # Criterion 2 also needs the other three message variants: price only.
        "name": "impossible query, price only",
        "query": "designer ballgown under $5",
        "wardrobe": "example",
        "criterion": 2,
    },
    {
        # Size only.
        "name": "impossible query, size only",
        "query": "designer ballgown size XXS",
        "wardrobe": "example",
        "criterion": 2,
    },
    {
        # Neither price nor size. "keywords" must still appear.
        "name": "impossible query, keywords only",
        "query": "designer ballgown",
        "wardrobe": "example",
        "criterion": 2,
    },
    {
        # Criterion 3. Any matching query works. The ids are compared in the
        # trace (select_item vs the suggest_outfit inputs).
        "name": "selected item reaches suggest_outfit",
        "query": "denim jacket under $50",
        "wardrobe": "example",
        "criterion": 3,
    },
    {
        # Criterion 4. The same query every try, so the same item reaches
        # create_fit_card and only the model's wording changes.
        "name": "fit card for the same item",
        "query": "vintage graphic tee under $30",
        "wardrobe": "example",
        "criterion": 4,
    },
    {
        # Criterion 5. A price and no size, so parsed["size"] is None.
        "name": "parser: price, no size",
        "query": "levi's jeans under $40",
        "wardrobe": "example",
        "criterion": 5,
    },
    {
        # A user with nothing saved. One of unit 4's three failure modes.
        "name": "empty wardrobe",
        "query": "denim jacket under $50",
        "wardrobe": "empty",
        "criterion": None,
    },
]

WARDROBES = ("example", "empty")


def validate() -> list[str]:
    """Complain about anything malformed, before a long run rather than during."""
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("query", "").strip():
            problems.append(f"scenario {i} has no query")
        if scenario.get("wardrobe") not in WARDROBES:
            problems.append(
                f"scenario {i} has wardrobe {scenario.get('wardrobe')!r} — "
                f"it should be one of {WARDROBES}"
            )
    return problems
