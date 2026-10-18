# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- Three or four sentences: what a user asks for, and what they get back. -->

FitFindr turns a plain-language request like "vintage graphic tee under $30, size M" into a thrift find you can picture wearing. It searches the secondhand listings for the best match within your size and budget, then shows you the item with its price and platform. For that item it suggests one or two outfits, built from pieces in your own wardrobe if you've saved one, or general styling ideas if you haven't. It finishes with a short caption you could post about the find. If nothing matches, it stops and tells you what to change, such as raising the price limit, dropping the size or using fewer keywords.

---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Searches the listings data by keyword, with optional size and price filters, without calling the model.
- **Inputs:** `description` (str | None, keywords such as `"vintage graphic tee"`, or `None` for no keywords, which returns `[]`; matched case-insensitively against each listing's `title`, `description`, `category`, `style_tags` and `colors`; the words a, an, the, in, on, at, for, with, and, or, but and any one-character word are ignored), `size` (str | None), `max_price` (float | None, inclusive). A size matches on whole tokens, not substrings. Parentheticals are dropped and the rest is split on `/`, so `"M"` matches `M`, `S/M` and `M/L` but not `US 9`, and `One Size` listings match any size.
- **Returns:** A list of up to 10 listing dicts, best match first. Each with `id`, `title`, `description`, `category`, `style_tags` (list), `size`, `condition`, `price` (float), `colors` (list), `brand` (str or `None`), `platform`. A listing's score is the number of distinct description keywords found in its searched fields, and listings with the same score stay in the order they appear in the data file.
- **When it has nothing:** Returns an empty list `[]`, never `None` and never an exception. This happens when no listing passes the size and price filters, or when every remaining listing scores zero, including a description made only of ignored words. The loop stops there and doesn't call the other two tools.
- **Known gap:** `W30 L30` stays one token, so a request for `"W30"` won't match it.

### `suggest_outfit`

- **What it does:** Asks the model for one or two outfits built around the thrifted item, using the user's own wardrobe pieces if there are any.
- **Inputs:** `new_item` (dict, a listing dict from `search_listings`), `wardrobe` (dict with an `items` key holding a list, which may be empty; each item is a dict with `id`, `name`, `category`, `colors` (list), `style_tags` (list) and `notes` (str or `None`)).
- **Returns:** A non-empty string with one or two outfits. With a non-empty wardrobe, each outfit names the thrifted item and at least one wardrobe piece, referring to pieces by their `name`. With an empty wardrobe, each outfit is built from the thrifted item plus general styling advice and names no wardrobe pieces.
- **When it has nothing:** With an empty `wardrobe["items"]` it returns general styling advice for the item as a non-empty string, never `""` and never an exception for an empty wardrobe. If the model is down, `generate` raises `ModelUnavailable` and `run_agent` handles it. If the model returns an empty string, it asks once more with `cache=False`, and if that is also empty it raises `ModelUnavailable` with the message "The model returned an empty response.", so the loop never receives `""`.

### `create_fit_card`

- **What it does:** Asks the model for a short social-post caption about the find.
- **Inputs:** `outfit` (str, the string from `suggest_outfit`), `new_item` (dict, the listing dict).
- **Returns:** A two-to-four sentence caption string that mentions the item, its price and its platform once each, and should vary between runs.
- **When it has nothing:** If `outfit` is empty or only whitespace it returns the exact string "No outfit was provided, so there is no caption to write." without calling the model and without raising an exception. An empty model response raises `ModelUnavailable` as in `suggest_outfit`.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:**
If `search_listings` returns `[]`, set `session["error"]` to a message built from what the user gave, then return the session:

- price and size both given: "No listings matched. Try raising your price limit, dropping the size, or using fewer keywords."
- only a price given: "No listings matched. Try raising your price limit or using fewer keywords."
- only a size given: "No listings matched. Try dropping the size or using fewer keywords."
- neither given: "No listings matched. Try using different or fewer keywords."

Otherwise, select `search_results[0]` and call `suggest_outfit`.

**Where it lives:** `agent.py::run_agent`

**One pass, no repeat:** `run_agent` goes through the steps once from top to bottom, and the only branch is the empty-search check. It never returns to an earlier step, so it has no `while` loop. It calls `trace.check_iterations(1)` once as the stop condition, so a loop added later would already be guarded.

**How the query is parsed:**

Strip the query, then pull out the price and size with case-insensitive regex and treat the remaining words as the description of the item.

- **Price:** a number with an optional `$` and optional decimals, right after `under`, `below`, `less than`, `up to` or `max`, for example `under $30` or `below 29.99`. A `$` amount with none of those words, such as `$30`, is also read as the price ceiling. It is stored as a float.
- **Size:** the single word right after `size`, for example `size M` or `size XL`. It is stored as a string.
- **Neither found:** the field is `None`. "Given" in the branch rule means the field is not `None`.
- **Shape of `parsed`:** always `description`, `size` and `max_price`. All three keys are always present, and a value the user did not give is `None`, never a missing key. For example, `{"description": None, "size": "M", "max_price": 40.0}`.
- **Removal:** the matched price and size text is removed before the remaining words become the description, so `30` or `M` is not searched as a keyword. A trailing comma or period is dropped.
- **Only price and size in the query:** The description is `None`, so `search_listings` returns `[]` and the loop stops with the message that matches which filters were given.
- **Known gap:** the size is whatever single word follows `size`, so a query like "plus size dress" reads `dress` as the size and the search returns nothing, and a two-word size like `size US 9` is read as just `US`.

**What moves through the session:**

`query` and `wardrobe` are set when the session starts.
Then in order: `parsed` -> `search_results` -> `selected_item` -> `outfit_suggestion` -> `fit_card`. On an early exit `error` is set and the later fields stay `None`.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30, size M'
  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   Outfit 1:
- Y2K Baby Tee — Butterfly Print
- Baggy straight-leg jeans, dark wash
- Chunky white sneakers
- Black crossbody bag

Outfit 2:
- Y2K Baby Tee — Butterfly Print
- Wide-leg khaki trousers
- Vintage black denim jacket
- Chunky white sneakers
- Brown leather belt

  Fit card: Living out my early 2000s pop star dreams in this butterfly print Y2K baby tee I just scored on Depop for $18. It gives major Lizzie McGuire off-duty energy, whether you throw it on with baggy dark-wash denim or dress it up a bit with wide-leg khakis.

2 model calls this session, 550 prompt + 152 output tokens
```

Note: the long dashes in the item title are part of the real output. They come from the listing title in the data file and are printed as is. This run was made with the cache off, so both model answers are fresh. One edit was made by hand: the last sentence of the fit card, "Seriously obsessed with how buttery soft the cotton is!", was removed because the listing says nothing about cotton or softness, so the model made it up. The rest is the real output.

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print([(r['id'], r['title'], r['price']) for r in search_listings('graphic tee', max_price=30)])"
[('lst_002', 'Y2K Baby Tee — Butterfly Print', 18.0), ('lst_006', 'Graphic Tee — 2003 Tour Bootleg Style', 24.0), ('lst_017', 'Mesh Long-Sleeve Top — Black', 15.0), ('lst_033', 'Vintage Band Tee — Faded Grey', 19.0), ('lst_011', 'Low-Rise Cargo Pants — Khaki', 27.0), ('lst_015', 'Vintage Graphic Hoodie — Faded Black', 26.0)]
```

Note: the long dashes in the titles are part of the real output. They come from the listing titles in the data file and are printed as is.

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(' '.join(suggest_outfit(load_listings()[1], get_example_wardrobe()).split()))"
Outfit 1: - Y2K Baby Tee — Butterfly Print - Baggy straight-leg jeans, dark wash - Chunky white sneakers - Black crossbody bag Outfit 2: - Y2K Baby Tee — Butterfly Print - Wide-leg khaki trousers - Vintage black denim jacket - Chunky white sneakers
```

Note: the long dash in the item name is part of the real output. It comes from the listing title in the data file and is printed as is.

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(' '.join(create_fit_card('baby tee with baggy dark-wash jeans and white platform sneakers', load_listings()[1]).split()))"
Found the ultimate Y2K baby tee with the cutest glitter butterfly print for just $18 over on Depop. I'm totally living for the early 2000s mall-rat energy of this piece. Just styled it with some baggy dark-wash denim and white platform sneakers for maximum Bratz doll vibes. Grab it before I change my mind and keep it for myself!
```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:* I asked Claude to build `suggest_outfit` to match my README spec, including a branch for an empty wardrobe that gives general styling advice. My spec also said each outfit is built from the thrifted item.
- *What came back:* The code worked, and with an empty wardrobe it returned styling advice. Although when I read the live output, the advice never mentioned the thrifted item at all, it was generic. That broke the README line saying each outfit is built from the thrifted item.
- *What I changed:* I had the empty-wardrobe prompt tightened so it tells the model to start each outfit by naming the new item, and still not to claim I own anything. A later live run did name the item. That was one run only, so I did not count it as proof, and I plan to measure this properly in Unit 4.

**Moment 2**

- *What I asked for:* After the loop was built I asked whether I should write the unit tests for the functions in `agent.py`. Claude said yes and drafted a `test_agent.py` with tests for the query parser, the four error messages and the branch, using fake tools so no model quota is used.
- *What came back:* Claude's first suggestion was to leave `test_agent.py` in the project root next to `test_tools.py`. Its reasons were that `python test_agent.py` would still find the `agent` and `tools` imports from the root, that pytest is not in requirements.txt, and that moving `test_tools.py` would change a file from the last milestone.
- *What I changed:* I believed that a separate tests folder is standard practice. So I had both files moved into tests/. That meant adding one line at the top of each file so that `python tests/test_agent.py` and `python tests/test_tools.py` still find the project's modules. I then ran both test files from their new location to check they still passed. I also asked Claude to add docstrings to every test and helper function.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The selected item is the item suggest_outfit receives | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. The fit card has the price, platform and item in 280 characters | 4 of 5 | PASS | FAIL | FAIL | FAIL | FAIL | MISSED (1/5) |
| 5. The parser returns exactly description, size and max_price | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

Criterion 2 row: each try cell covers four queries (price and size, price only, size only, keywords only). A cell is PASS only if all four queries passed in that try number. All four did in all five tries, so that is 20 of 20 individual tries.

**Real output from one try**, pasted as text, naming the file and function
that produced it:

Criterion 1, try 1 of "matching query completes". Produced by agent.py::run_agent (the trace.step calls) and tools.py::create_fit_card (the fit card), written to the log by run_eval.py::write_report. Query: vintage graphic tee under $30.

```
[1] parse_query
      in:  vintage graphic tee under $30
      out: {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
[2] search_listings (via MCP)
      in:  {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
      →    10 match(es)
[3] select_item
      out: Y2K Baby Tee — Butterfly Print ($18.0, depop)
[4] suggest_outfit
      in:  Y2K Baby Tee — Butterfly Print ($18.0, depop)
      out: Outfit 1: - Y2K Baby Tee — Butterfly Print - Baggy straight-leg jeans, dark wash - Vintage black denim jacket …
[5] create_fit_card
      in:  Outfit 1: - Y2K Baby Tee — Butterfly Print - Baggy straight-leg jeans, dark wash - Vintage black denim jacket …
      out: Finally scored the ultimate Y2K butterfly baby tee for just $18 on Depop! It gives major 2000s pop star off-du…
```

Criterion 2, try 1 of "impossible query stops early". Produced by agent.py::run_agent (the branch) with the message from agent.py::_no_results_message. Query: designer ballgown size XXS under $5. The trace has no suggest_outfit step.

```
[1] parse_query
      in:  designer ballgown size XXS under $5
      out: {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
[2] search_listings (via MCP)
      in:  {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
      out: [] (empty)
      →    0 match(es)
[3] branch
      →    search returned []: No listings matched. Try raising your price limit, dropping the size, or using fewer keywords.
```

Criterion 3, try 1 of "selected item reaches suggest_outfit". The first two ids are from agent.py::run_agent (session["selected_item"] and session["search_results"][0]). The third is recorded by the stand-in in run_eval.py::run_once and printed by run_eval.py::write_report. Query: denim jacket under $50.

```
- selected_item: Denim Jacket — Light Wash, Cropped ($42.0, poshmark)
- selected_item id: lst_007
- search_results[0] id: lst_007
- id received by suggest_outfit: lst_007
```

Criterion 4, try 2 of "fit card for the same item" (a FAIL). Produced by tools.py::create_fit_card. Query: vintage graphic tee under $30. This card is 309 characters, over the 280 limit, and writes "$18", not "$18.00". Try 1 of the same scenario passed all four checks.

```
Channeling serious early 2000s mall-rat energy with this butterfly baby tee. Grabbed it on Depop for just $18, and honestly, it’s giving the ultimate retro streetwear vibe whether you style it with baggy dark-wash denim or chunky khaki trousers. Don’t sleep on this one—it’s about to be your go-to all summer.
```

Criterion 5, try 1 of "parser: price, no size". Produced by agent.py::_parse_query, shown in the parse_query trace step from agent.py::run_agent. Query: levi's jeans under $40.

```
[1] parse_query
      in:  levi's jeans under $40
      out: {'description': "levi's jeans", 'size': None, 'max_price': 40.0}
```

The long dashes, the arrow and the curly apostrophes in these blocks come from the program output and the log. 

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 | A matching query completes all three tools | 4 of 5 | MET | 5 passes in 5 tries. 5 is at least the 4 the target asks for. |
| 2 | An impossible query stops before the second tool | 5 of 5 | MET | 5 passes in 5 tries on each of the four queries (20 of 20). The trace ended at the branch every time and the message named the right words. |
| 3 | The selected item is the item suggest_outfit receives | 5 of 5 | MET | 5 passes in 5 tries. The selected item, search_results[0] and the item suggest_outfit received were all lst_007 every time. |
| 4 | The fit card has the price, platform and item in 280 characters | 4 of 5 | MISSED | 1 pass in 5 tries, against a target of 4. Tries 2 to 5 failed: 4 were over 280 characters and 3 wrote "$18" instead of "$18.00". |
| 5 | The parser returns exactly description, size and max_price | 5 of 5 | MET | 5 passes in 5 tries. The same three keys came back every time, with size None. |

**Diagnoses**

Criterion 4 is the only miss (1 of 5 against a target of 4).

**Where it failed:** the model's output, in the third step, `create_fit_card` (tools.py). It is not the tool's code, the loop's branch, or the session.

- The tool passed the right price. The prompt line is `f"Price: ${new_item['price']:.2f}"`, so the model was shown "$18.00" every time.
- The branch was not involved. Criterion 4 only runs on a matching query, and the loop went on to the third tool every time.
- The session was not involved. The selected item was the same listing (lst_002) in every try, and criterion 3 passed on its ids.

**Mechanism:** the prompt gives no rule for two things the criterion measures.

1. **Length.** It asks for "two to four sentences" with no character limit. Tries 2 to 5 came out at 309, 315, 332 and 361 characters. Only try 1 (273) was under 280.
2. **Price format.** It says to mention the price "once" but not to copy it exactly. The model wrote "$18" in tries 2, 3 and 5. I tested this separately, outside the Run Log - Before. The outfit text has no dollar sign, so the model was not copying "$18" from it. With the current prompt, "$18.00" appeared in 2 of 10 tries. With one added sentence telling it to write the price exactly as shown, it appeared in 10 of 10. That sentence did not fix length, which stayed over 280 in 5 of 10 cards.

**Pattern:** this is one problem, not two. The prompt says what tone it wants and nothing about the format it is measured on. Platform and a title word, which it does ask for, passed 5 of 5.

**Were the targets low?** Criteria 2, 3 and 5 are at 5 of 5, the strictest possible. They test code with no model call, so passing every time is expected. Criterion 1 is the one I would tighten. Its target is 4 of 5, it passed 5 of 5 in both runs, and it only checks that all three tools ran on one query, so a failed try would still have been MET. I would hold it to 5 of 5. I left criteria.md as written, because it only allows a revision when a criterion could not be measured.



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```
[1] parse_query
      in:  vintage graphic tee under $30
      out: {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
[2] search_listings (via MCP)
      in:  {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
      →    10 match(es)
[3] select_item
      out: Y2K Baby Tee — Butterfly Print ($18.0, depop)
[4] suggest_outfit
      in:  Y2K Baby Tee — Butterfly Print ($18.0, depop)
      out: Outfit 1: - Y2K Baby Tee — Butterfly Print - Baggy straight-leg jeans, dark wash - Chunky white sneakers - Bla…
[5] create_fit_card
      in:  Outfit 1: - Y2K Baby Tee — Butterfly Print - Baggy straight-leg jeans, dark wash - Chunky white sneakers - Bla…
      out: Found the ultimate Y2K butterfly baby tee and I’m literally never taking it off. It’s giving peak 2000s mallra…
```

Real output from `python app.py ask 'vintage graphic tee under $30' --trace`, pasted as printed. The long dashes, the arrow and the curly apostrophe come from the program, not from me.

**Empty search**

```
[1] parse_query
      in:  designer ballgown size XXS under $5
      out: {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
[2] search_listings (via MCP)
      in:  {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
      out: [] (empty)
      →    0 match(es)
[3] branch
      →    search returned []: No listings matched. Try raising your price limit, dropping the size, or using fewer keywords.
```

Real output from `python app.py ask 'designer ballgown size XXS under $5' --trace`, pasted as printed. It stops at step 3, so suggest_outfit and create_fit_card never run.

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->

In mcp_server.py I registered search_listings with the inputs from the Tool Inventory: description, size and max_price, all optional. In agent.py I replaced the direct search_listings call in run_agent with call_tool("search_listings", {...}) from mcp_client.py, and the trace step is named "search_listings (via MCP)". The swap did not change what the agent gets back. On four queries (two with results, one empty search, one with no description), the MCP call and the direct call returned identical lists.

---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:** One sentence added to the prompt in tools.py::create_fit_card: "Write the price exactly as shown above, with a dollar sign and two decimals." Nothing else changed. The prompt, the system prompt, the temperature and the criteria are the same as in Run Log - Before.

**Which failure it was meant to fix:** The price-format half of the criterion 4 miss. The diagnosis found that the prompt said to mention the price but not how to write it, and the model wrote "$18" in tries 2, 3 and 5 of Run Log - Before. My separate 10-try check had shown this sentence took "$18.00" from 2 of 10 to 10 of 10. It was not meant to fix length.

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The selected item is the item suggest_outfit receives | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. The fit card has the price, platform and item in 280 characters | 4 of 5 | PASS | PASS | FAIL | FAIL | PASS | MISSED (3/5) |
| 5. The parser returns exactly description, size and max_price | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

Criterion 2 row: same as in Run Log - Before. All four queries passed in all five tries, 20 of 20.

Run from results/run_2026-10-18_0204_after.md with `python run_eval.py --label after`, caching off, temperature 0.9.

**Did it help, and how do I know:** It helped, but not enough to meet the target. Criterion 4 went from 1 of 5 to 3 of 5, still short of 4 of 5, so it is still MISSED. The price half is fixed: "$18.00" appeared in 5 of 5 cards, against 2 of 5 before. The remaining failures are length only. Tries 3 and 4 came out at 341 and 330 characters, over the 280 limit. Before, all four failing tries were over the limit and three of them also had the wrong price format. The prompt still has no character limit, so length is the half of the diagnosis that this change did not touch. The other four criteria did not move, which is what I expected because the change is inside create_fit_card only.

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
