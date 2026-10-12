"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re

import config
import trace
from tools import search_listings, suggest_outfit, create_fit_card
from generate import ModelUnavailable


# ── session state ─────────────────────────────────────────────────────────────


def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {"description": None, "size": None, "max_price": None},  # pulled out of the query
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
    }


# ── query parsing ─────────────────────────────────────────────────────────────

_PRICE_WORDS = re.compile(
    r"\b(?:under|below|less than|up to|max)\s*\$?\s*(\d+(?:\.\d+)?)", re.I)
_PRICE_BARE = re.compile(r"\$\s*(\d+(?:\.\d+)?)")
_SIZE = re.compile(r"\bsize\s+(\w+)", re.I)


def _parse_query(query: str) -> dict:
    """Pull price, size and description out of a plain-language query (regex only)."""
    text = query.strip()
    max_price = size = None

    m = _PRICE_WORDS.search(text) or _PRICE_BARE.search(text)
    if m:
        max_price = float(m.group(1))
        text = text[:m.start()] + " " + text[m.end():]

    m = _SIZE.search(text)
    if m:
        size = m.group(1)
        text = text[:m.start()] + " " + text[m.end():]

    description = " ".join(text.replace(",", " ").replace(".", " ").split())
    return {"description": description or None, "size": size, "max_price": max_price}


def _no_results_message(parsed: dict) -> str:
    """The error text for an empty search, chosen by which filters the user gave."""
    has_price = parsed["max_price"] is not None
    has_size = parsed["size"] is not None
    if has_price and has_size:
        return "No listings matched. Try raising your price limit, dropping the size, or using fewer keywords."
    if has_price:
        return "No listings matched. Try raising your price limit or using fewer keywords."
    if has_size:
        return "No listings matched. Try dropping the size or using fewer keywords."
    return "No listings matched. Try using different or fewer keywords."


# ── planning loop ─────────────────────────────────────────────────────────────


def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the planning loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

    ─────────────────────────────────────────────────────────────────────────
    IN UNIT 4 you come back and add two things:

      • Trace calls. One per step. `trace.step("search_listings", inputs=...,
        returned=...)` — see trace.py. Your README needs the output.

      • A handler for ModelUnavailable, so a bad key produces a message rather
        than a stack trace. The import is already at the top of this file.
    """
    # Start a fresh session. Every result below goes into it, and the next
    # step reads it back out.
    session = new_session(query, wardrobe)

    # Stop condition. The loop is one pass, so the count is always 1, but the
    # check is kept in case a repeat is added later (see trace.py).
    trace.check_iterations(1)

    # Parse the query into a description, size and max_price (regex only, see
    # _parse_query). All three keys are always present, None if not given.
    session["parsed"] = _parse_query(session["query"])

    # Search with what was parsed.
    session["search_results"] = search_listings(
        session["parsed"]["description"],
        size=session["parsed"]["size"],
        max_price=session["parsed"]["max_price"],
    )

    # THE BRANCH. If nothing came back, say what the user could change (the
    # message depends on which filters they gave) and return. suggest_outfit
    # and create_fit_card are not called with nothing.
    if not session["search_results"]:
        session["error"] = _no_results_message(session["parsed"])
        return session

    # Choose an item: the best match, which is the first result.
    session["selected_item"] = session["search_results"][0]

    # Suggest outfits for the chosen item, from the user's wardrobe.
    session["outfit_suggestion"] = suggest_outfit(
        session["selected_item"], session["wardrobe"])

    # Write the caption from the outfit and the chosen item.
    session["fit_card"] = create_fit_card(
        session["outfit_suggestion"], session["selected_item"])

    return session


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    """Print a finished session: the error if the run stopped early, else the item, outfit and caption."""
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
