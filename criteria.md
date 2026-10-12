# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent should complete all three
tool calls and return a fit card, in at least 4 out of 5 tries.

**Why this target:**
<!-- Why 4 of 5 and not 5 of 5? Something about your search, probably —
     "my search is a plain keyword match and some phrasings will miss" is a
     real answer. -->

`search_listings` is a plain keyword match, so some phrasings of a request will miss even when a listing exists. For example, a request for "W30" does not match a "W30 L30" listing, and "plus size dress" reads "dress" as the size. A miss like these counts against the target, because the criterion measures what the agent returns, not what the user meant. The two model calls can also return an empty response. I retry once, and if it is still empty I raise `ModelUnavailable`, so a run can fail on the model and not on my code. One miss in five allows for this to happen, so 5 of 5 would punish me for things outside the loop and outside my code.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent should stop before calling
`suggest_outfit` and return a message naming what to change, in 5 out of 5 tries.

**Why this target:**
<!-- Why is 5 of 5 reasonable here when criterion 1 isn't? What's different
     about this path? -->

When `search_listings` returns `[]`, the loop sets `session["error"]` and returns before `suggest_outfit` is called. An empty list and the choice of message depend only on the data and the parsed query, so the result is the same every time. A miss here would mean a bug in my code, not variation, so there is no reason to allow one in five. The error message is chosen from which filters the user gave, so it always names something to change.

---

## 3. Something about state

<!-- YOU WRITE THIS ONE.

     How would you know that the item your search found is the same item the
     next tool received? Name something countable or observable.

     This is the criterion people find hardest, because state failure doesn't
     look like state failure — it looks like a tool problem. Something that
     compares session["selected_item"] against what actually reached
     suggest_outfit is the shape you're after. -->

Given a user query with at least one matching listing, `session["selected_item"]["id"]` should equal `search_results[0]["id"]` and the `id` of the `new_item` passed to `suggest_outfit`, in 5 out of 5 tries.

**Why this target:**

Nothing here involves the model. `selected_item` is assigned straight from `search_results[0]`, so the ids either match every time or there is a bug. There is no run-to-run variation that would justify 4 of 5. A mismatch would look like a bad outfit, so I compare ids instead of reading the output.

---

## 4. Something about the fit card

<!-- YOU WRITE THIS ONE.

     The fit card calls a model, so the same input can produce different words
     each time. That's not a bug — it's the nature of the tool. So what would
     make it acceptable?

     Think about what you'd actually be unhappy to see. A caption that never
     mentions the price? Two different items producing the same opening
     sentence? A card longer than a caption anyone would post? Any of those can
     be turned into a number. -->

Given one listing and its outfit, the fit card should be at most 280 characters and contain the item's price as a dollar sign followed by the price with two decimals (for example "$24.00" when the price is 24.0), the platform name, and at least one word from its title longer than two letters, all matched ignoring capitalization, in at least 4 out of 5 tries.

**Why this target:**

The model's wording changes every run, so I don't check the words. I check facts that should be there however it is phrased: the price, the platform and the item. They are what make a caption about a real find, and `create_fit_card` is given all three. Each is a string match and the length is a character count, so the result is the same every time. Because all five tries use the same listing, the only thing that changes between them is the model's wording, which is what this criterion is meant to test. The item check needs only one word from the title because a caption rarely repeats a full title. I chose 4 of 5 and not 5 of 5 because the model can write the price another way, such as "24 dollars" or "$24.5" for a $24.50 item, and the match would count that as a miss even though the caption reads fine. The 280 limit is a typical post length.

---

## 5. Your choice

<!-- YOU WRITE THIS ONE TOO.

     Pick something you actually care about getting right. Speed, the empty
     wardrobe path, what happens when the model can't be reached, whether the
     search respects a price ceiling — anything, as long as it names a number
     or an observable outcome. -->

Given a query with a price but no size, `parsed` should have exactly the keys `description`, `size` and `max_price`, with `size` set to `None`, in 5 out of 5 tries.

**Why this target:**

The parser is plain regex string manipulation with no model call, so the same query always gives the same `parsed` text. Any miss is a bug, not randomness, which is why the target is 5 of 5 and not lower. I chose the keys because the branch rule reads `parsed["size"]` and `parsed["max_price"]` to pick one of four error messages, and a missing key would raise a `KeyError` instead of giving a message. Five tries of one query give the same result each time, so the repeats only confirm that the parser is stable. The test uses a query with no size so it covers the `None` case, which is the one the branch rule depends on.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
