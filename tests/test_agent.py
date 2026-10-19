"""Tests for the parser and the planning loop. No model calls.

    python tests/test_agent.py
"""

import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import agent
from agent import _no_results_message, _parse_query, run_agent
from utils.data_loader import get_example_wardrobe


# -- _parse_query: shape --------------------------------------------------------

def test_parsed_always_has_three_keys():
    """Whatever the query, the parser returns exactly description, size and max_price (a missing value is None, never a missing key)."""
    for q in ["tee", "under $30", "size M", "", "tee under $30 size M"]:
        assert set(_parse_query(q)) == {"description", "size", "max_price"}


def test_price_and_size_together():
    """The full example query splits into description 'vintage graphic tee', size 'M' and max_price 30.0."""
    assert _parse_query("vintage graphic tee under $30, size M") == {
        "description": "vintage graphic tee", "size": "M", "max_price": 30.0}


def test_neither_given_is_none():
    """With no price and no size in the query, both come back as None and the whole query is the description."""
    assert _parse_query("vintage graphic tee") == {
        "description": "vintage graphic tee", "size": None, "max_price": None}


def test_price_only():
    """A price with no size gives max_price as a float and size None."""
    p = _parse_query("denim jacket under 45")
    assert p["max_price"] == 45.0 and p["size"] is None


def test_size_only():
    """A size with no price gives the size string and max_price None."""
    p = _parse_query("denim jacket size XL")
    assert p["size"] == "XL" and p["max_price"] is None


# -- _parse_query: price forms --------------------------------------------------

def test_price_words():
    """Each price phrase (under, below, less than, up to, max) is read as a ceiling of 30.0."""
    for q in ["tee under $30", "tee below 30", "tee less than $30",
              "tee up to 30", "tee max 30"]:
        assert _parse_query(q)["max_price"] == 30.0, q


def test_bare_dollar_amount_is_the_ceiling():
    """A '$30' with no price word is still read as the price ceiling."""
    assert _parse_query("tee $30")["max_price"] == 30.0


def test_decimal_price_is_a_float():
    """'below 29.99' gives 29.99, and the decimal point does not leak into the description."""
    p = _parse_query("tee below 29.99")
    assert p["max_price"] == 29.99 and p["description"] == "tee"


def test_case_insensitive():
    """UNDER and SIZE in capitals are still recognized. The size keeps the case the user typed."""
    p = _parse_query("Tee UNDER $30 SIZE xl")
    assert p["max_price"] == 30.0 and p["size"] == "xl"


# -- _parse_query: description --------------------------------------------------

def test_matched_text_is_removed_from_description():
    """The price and size text is removed, so '30' and 'M' are not searched as keywords."""
    d = _parse_query("graphic tee under $30, size M")["description"]
    assert "30" not in d and "M" not in d.split()


def test_only_price_and_size_gives_none_description():
    """If only a price and size are given, nothing is left, so the description is None (not an empty string)."""
    assert _parse_query("under $30 size M")["description"] is None


def test_blank_query_gives_none_description():
    """A query of only spaces gives a description of None."""
    assert _parse_query("   ")["description"] is None


# -- _parse_query: known gaps, recorded as current behavior ----------------------

def test_known_gap_plus_size_reads_next_word_as_size():
    """KNOWN GAP from the README: in 'plus size dress' the word after 'size' (dress) is read as the size. This records today's behavior."""
    assert _parse_query("plus size dress")["size"] == "dress"


def test_known_gap_two_word_size_reads_first_word_only():
    """KNOWN GAP from the README: 'size US 9' is read as just 'US'. This records today's behavior."""
    assert _parse_query("jeans size US 9")["size"] == "US"


# -- _no_results_message: one per README message ----------------------------------

def test_message_price_and_size():
    """Price and size both given: the message tells the user to raise the price, drop the size or use fewer keywords."""
    m = _no_results_message({"description": "x", "size": "M", "max_price": 5.0})
    assert "raising your price limit, dropping the size" in m


def test_message_price_only():
    """Only a price given: the message mentions the price limit but not the size."""
    m = _no_results_message({"description": "x", "size": None, "max_price": 5.0})
    assert "raising your price limit or using fewer keywords" in m


def test_message_size_only():
    """Only a size given: the message mentions dropping the size but not the price."""
    m = _no_results_message({"description": "x", "size": "M", "max_price": None})
    assert "dropping the size or using fewer keywords" in m


def test_message_neither():
    """Neither given: the message only suggests different or fewer keywords."""
    m = _no_results_message({"description": "x", "size": None, "max_price": None})
    assert "different or fewer keywords" in m


# -- run_agent: the branch, with fake tools so no quota is used ------------------

ITEM = {"id": "lst_999", "title": "Test Tee", "price": 10.0, "platform": "Depop"}


class FakeTools:
    """Stand-ins for the three real tools, so run_agent can be tested without the model.

    `results` is what the fake search returns (use [] to test the empty-search
    branch). Every call is recorded in .calls, in order, so a test can check
    which tools ran and what they were given.
    """

    def __init__(self, results):
        self.results = results
        self.calls = []

    def search(self, description, size=None, max_price=None):
        self.calls.append(("search", description, size, max_price))
        return self.results

    def outfit(self, new_item, wardrobe):
        self.calls.append(("outfit", new_item["id"]))
        return "an outfit"

    def card(self, outfit, new_item):
        self.calls.append(("card", outfit, new_item["id"]))
        return "a caption"


def run_with(results, query):
    """Run run_agent with the three tools in agent.py swapped for FakeTools, then restore the real ones.

    Search goes through agent.call_tool (the MCP call), so that
    is what gets swapped for the fake search.

    Returns (session, fake) so a test can check both the session and the calls.
    """
    fake = FakeTools(results)

    def fake_call_tool(name, arguments):
        assert name == "search_listings"
        return fake.search(**arguments)

    saved = (agent.call_tool, agent.suggest_outfit,
             agent.create_fit_card)
    agent.call_tool, agent.suggest_outfit, agent.create_fit_card = (
        fake_call_tool, fake.outfit, fake.card)
    try:
        session = run_agent(query, get_example_wardrobe())
    finally:
        agent.call_tool, agent.suggest_outfit, agent.create_fit_card = (
            saved)
    return session, fake


def test_empty_search_stops_before_the_second_tool():
    """THE BRANCH: when search returns [], error is set, later session fields stay None, and only the search tool is called."""
    session, fake = run_with([], "tee under $5 size XXS")
    assert session["error"]
    assert session["selected_item"] is None
    assert session["outfit_suggestion"] is None
    assert session["fit_card"] is None
    assert [c[0] for c in fake.calls] == ["search"]


def test_empty_search_message_depends_on_what_was_given():
    """The error text differs depending on which filters the user gave, so the message is built from the input, not fixed."""
    both, _ = run_with([], "tee under $5 size XXS")
    neither, _ = run_with([], "tee")
    assert both["error"] != neither["error"]


def test_results_run_all_three_tools():
    """When search finds something, there is no error and all three tools run in order: search, outfit, card."""
    session, fake = run_with([ITEM], "tee under $30")
    assert session["error"] is None
    assert [c[0] for c in fake.calls] == ["search", "outfit", "card"]
    assert session["outfit_suggestion"] == "an outfit"
    assert session["fit_card"] == "a caption"


def test_state_selected_item_is_first_result_and_is_passed_on():
    """State check (criterion 3): selected_item is search_results[0], and that same id is passed to suggest_outfit and create_fit_card."""
    other = dict(ITEM, id="lst_000")
    session, fake = run_with([ITEM, other], "tee")
    assert session["selected_item"]["id"] == session["search_results"][0]["id"]
    assert ("outfit", "lst_999") in fake.calls
    assert ("card", "an outfit", "lst_999") in fake.calls


def test_search_receives_the_parsed_values():
    """The values the parser produced (description, size, max_price) are what search_listings is actually called with."""
    session, fake = run_with([ITEM], "vintage tee under $30, size M")
    assert fake.calls[0] == ("search", "vintage tee", "M", 30.0)
    assert session["parsed"]["max_price"] == 30.0


if __name__ == "__main__":
    failures = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except Exception as exc:
                failures += 1
                print(f"FAIL {name}: {type(exc).__name__} {exc}")
    print(f"\n{failures} failed")
    raise SystemExit(1 if failures else 0)
