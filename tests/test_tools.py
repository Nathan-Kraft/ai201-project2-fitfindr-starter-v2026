"""Tests for the tools, run on their own. No loop, no agent.

    python tests/test_tools.py
"""

import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import tools
from generate import ModelUnavailable
from tools import search_listings
from utils.data_loader import get_empty_wardrobe, get_example_wardrobe, load_listings


def ids(results):
    """Helper: pull just the listing ids out of a list of results."""
    return [r["id"] for r in results]


# -- empty cases: always a list, never None, never an exception ---------------

def test_no_match_returns_empty_list():
    """A made-up word matches nothing, so search_listings returns [] (not None, no error)."""
    assert search_listings("xyzzy") == []


def test_none_description_returns_empty_list():
    """A description of None means no keywords, so the result is []."""
    assert search_listings(None) == []


def test_only_ignored_words_returns_empty_list():
    """Stopwords like 'the and a' are ignored, leaving no keywords, so the result is []."""
    assert search_listings("the and a") == []


def test_filters_that_remove_everything_return_empty_list():
    """A price limit of 1 removes every listing, so the result is [] even though 'graphic tee' matches words."""
    assert search_listings("graphic tee", max_price=1) == []


# -- price: inclusive ----------------------------------------------------------

def test_price_is_inclusive():
    """max_price is inclusive: lst_006 costs exactly 24.0, so it is found at 24.0 and dropped at 23.99."""
    # lst_006 Graphic Tee is exactly 24.0
    assert "lst_006" in ids(search_listings("graphic tee", max_price=24.0))
    assert "lst_006" not in ids(search_listings("graphic tee", max_price=23.99))


def test_every_result_is_within_price():
    """Every listing returned under a price limit of 20 costs 20 or less."""
    results = search_listings("vintage", max_price=20)
    assert results
    assert all(r["price"] <= 20 for r in results)


# -- size: whole tokens, not substrings -----------------------------------------

def test_size_m_matches_s_slash_m():
    """Size M matches the token M inside 'S/M' (lst_002) but not an L listing (lst_033)."""
    # lst_002 Baby Tee is S/M, lst_033 Band Tee is L
    found = ids(search_listings("tee", size="M"))
    assert "lst_002" in found
    assert "lst_033" not in found


def test_size_s_does_not_match_us_sizes():
    """Size S must not match 'US 8' or 'US 9'. The letter s is a substring of 'us', so this checks whole-token matching."""
    # lst_019 is US 8 and lst_035 is US 9; "s" is a substring of "us 8"
    found = ids(search_listings("sneakers", size="S"))
    assert "lst_019" not in found
    assert "lst_035" not in found


def test_size_xl_does_not_match_l():
    """Size XL must not match a listing in size L (lst_033)."""
    # lst_033 is L
    assert "lst_033" not in ids(search_listings("tee", size="XL"))


def test_one_size_matches_any_size():
    """A 'One Size' listing (lst_014 belt) is returned even when the shopper asks for XL."""
    # lst_014 Leather Belt is One Size (adjustable)
    assert "lst_014" in ids(search_listings("belt", size="XL"))


def test_size_is_case_insensitive():
    """Asking for size 'm' gives the same results as 'M'."""
    assert ids(search_listings("tee", size="m")) == ids(search_listings("tee", size="M"))


# -- ranking and limit ----------------------------------------------------------

def test_ties_keep_data_file_order():
    """lst_002, lst_006 and lst_033 all score 3, so they must come back in the order they appear in the data file."""
    # lst_002, lst_006 and lst_033 each score 3 for "vintage graphic tee"
    found = ids(search_listings("vintage graphic tee"))
    trio = [i for i in found if i in {"lst_002", "lst_006", "lst_033"}]
    assert trio == ["lst_002", "lst_006", "lst_033"]


def test_higher_score_ranks_first():
    """A listing that matches more keywords (lst_006) ranks above one that matches fewer (lst_015)."""
    # lst_006 scores 3, lst_015 Graphic Hoodie has no "tee" in its searched fields
    found = ids(search_listings("vintage graphic tee"))
    assert found.index("lst_006") < found.index("lst_015")


def test_at_most_ten_results():
    """'vintage' matches many listings, but search_listings returns at most 10 (config.SEARCH_RESULT_LIMIT)."""
    assert len(search_listings("vintage")) == 10


# -- shape ------------------------------------------------------------------------

def test_result_is_a_listing_dict():
    """Each result has every field the README promises, and price is a float."""
    first = search_listings("graphic tee")[0]
    for key in ("id", "title", "description", "category", "style_tags",
                "size", "condition", "price", "colors", "brand", "platform"):
        assert key in first
    assert isinstance(first["price"], float)


# -- suggest_outfit (model replaced by a fake, no quota used) ---------------------

class FakeModel:
    """Stand-in for tools.generate, so tests cost no quota.

    Give it the replies to return, in order (use "" to act like an empty model
    response). Each call is recorded in .calls as {"prompt", "cache"} so a test
    can check what was sent and whether the cache was on.
    """

    def __init__(self, *replies):
        self.replies = list(replies)
        self.calls = []

    def __call__(self, prompt, system=None, cache=True, temperature=None):
        self.calls.append({"prompt": prompt, "cache": cache})
        return self.replies.pop(0)


def run_suggest(fake, wardrobe):
    """Call suggest_outfit on the second listing with tools.generate swapped for `fake`, then put the real one back."""
    real = tools.generate
    tools.generate = fake
    try:
        return tools.suggest_outfit(load_listings()[1], wardrobe)
    finally:
        tools.generate = real


def test_outfit_prompt_names_item_and_wardrobe_pieces():
    """With a real wardrobe, the prompt sent to the model contains the new item's title and a wardrobe piece's name."""
    fake = FakeModel("Outfit one.")
    run_suggest(fake, get_example_wardrobe())
    prompt = fake.calls[0]["prompt"]
    assert "Y2K Baby Tee" in prompt
    assert "Baggy straight-leg jeans, dark wash" in prompt


def test_outfit_returns_model_text():
    """suggest_outfit returns the model's text unchanged."""
    assert run_suggest(FakeModel("Outfit one."), get_example_wardrobe()) == "Outfit one."


def test_empty_wardrobe_gets_general_advice_not_an_error():
    """An empty wardrobe still gets an answer (one model call), and the prompt lists no wardrobe pieces."""
    fake = FakeModel("Try it with straight jeans.")
    result = run_suggest(fake, get_empty_wardrobe())
    assert result == "Try it with straight jeans."
    assert len(fake.calls) == 1
    assert "Baggy straight-leg jeans" not in fake.calls[0]["prompt"]


def test_wardrobe_without_items_key_is_treated_as_empty():
    """A wardrobe dict with no 'items' key is treated like an empty wardrobe instead of raising KeyError."""
    assert run_suggest(FakeModel("General advice."), {}) == "General advice."


def test_empty_reply_retries_once_with_cache_off():
    """If the model returns '' the first time, suggest_outfit asks once more with cache=False and returns that answer."""
    fake = FakeModel("", "Second try worked.")
    assert run_suggest(fake, get_example_wardrobe()) == "Second try worked."
    assert len(fake.calls) == 2
    assert fake.calls[1]["cache"] is False


def test_two_empty_replies_raise_model_unavailable():
    """Two empty replies in a row raise ModelUnavailable ('empty response'), so the loop never receives ''."""
    fake = FakeModel("", "")
    try:
        run_suggest(fake, get_example_wardrobe())
    except ModelUnavailable as exc:
        assert "empty response" in str(exc)
    else:
        raise AssertionError("expected ModelUnavailable")
    assert len(fake.calls) == 2


# -- create_fit_card (model replaced by a fake, no quota used) --------------------

def run_card(fake, outfit):
    """Call create_fit_card on the second listing with tools.generate swapped for `fake`, then put the real one back."""
    real = tools.generate
    tools.generate = fake
    try:
        return tools.create_fit_card(outfit, load_listings()[1])
    finally:
        tools.generate = real


def test_card_prompt_has_title_price_platform_and_outfit():
    """The prompt sent to the model contains the item title, the price as $xx.xx, the platform and the outfit text."""
    fake = FakeModel("Caption.")
    run_card(fake, "Pair it with straight jeans.")
    prompt = fake.calls[0]["prompt"]
    item = load_listings()[1]
    assert item["title"] in prompt
    assert f"${item['price']:.2f}" in prompt
    assert item["platform"] in prompt
    assert "Pair it with straight jeans." in prompt


def test_card_returns_model_text():
    """create_fit_card returns the model's caption unchanged."""
    assert run_card(FakeModel("Caption."), "jeans and sneakers") == "Caption."


def test_empty_outfit_returns_message_without_calling_model():
    """An empty, whitespace or None outfit returns the fixed 'No outfit was provided' message and never calls the model."""
    for outfit in ("", "   \n", None):
        fake = FakeModel()
        result = run_card(fake, outfit)
        assert result == "No outfit was provided, so there is no caption to write."
        assert fake.calls == []


def test_card_empty_reply_retries_once_with_cache_off():
    """Same retry rule as suggest_outfit: one empty reply, then a second call with cache=False."""
    fake = FakeModel("", "Second try worked.")
    assert run_card(fake, "jeans and sneakers") == "Second try worked."
    assert fake.calls[1]["cache"] is False


def test_card_two_empty_replies_raise_model_unavailable():
    """Two empty replies in a row raise ModelUnavailable ('empty response')."""
    fake = FakeModel("", "")
    try:
        run_card(fake, "jeans and sneakers")
    except ModelUnavailable as exc:
        assert "empty response" in str(exc)
    else:
        raise AssertionError("expected ModelUnavailable")


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
