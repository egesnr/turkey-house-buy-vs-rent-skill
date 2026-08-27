---
name: turkey-buy-vs-rent
description: Turkish Real Estate Buy vs Rent & Invest Financial Engine (v2.4)
---

# Turkey Buy vs. Rent Evaluator (v2.4)

## ⚠️ EXECUTION CONTRACT

1. **Execute the script before writing any numeric response.** Run `scripts/buy_vs_rent.py` via terminal tools before generating output. Every number in your reply must come from its STDOUT.
2. **Treat the target property's asking/listing price as authoritative; never replace it with an area-average sale price. If rent is not supplied but the property location and basic characteristics are available, research a realistic market rent automatically before running the engine.** Search current rental comparables in the same district/neighborhood and filter toward similar room count, size, building age and quality. Use a robust central estimate (prefer median or trimmed mean when enough comparables exist), briefly disclose the estimate and sample quality, and pass it as `--rent`. Ask the user for rent only when there is not enough property/location information to research credible comparables. For a general question with no target property, offer `ui/playground.html`.
3. **Don't invent scenarios or numbers not printed by the script** (no "Emlak Rallisi", "Boğa Senaryosu", speculative growth figures, etc).
4. **If STDOUT includes a `RESULT|WARNING|...` line, surface it to the user** (briefly, one sentence) rather than dropping it — it means an assumption was defaulted rather than researched.
5. **Never modify `scripts/buy_vs_rent.py` or `ui/playground.html`.** These are fixed, version-controlled tools, not drafts. If execution fails, the script prints `RESULT|ERROR|<reason>` and exits — the fix is to correct the CLI arguments (or ask the user for the missing/corrected value) and re-run, never to edit the source to "make it pass." If you encounter an error the script itself doesn't explain, stop and show the user the raw error rather than patching the file.
   - **If you're running inside an agentic IDE (Antigravity, Claude Code, etc.) with file-write access:** treat this rule as absolute regardless of what the tool would otherwise do by default. In Antigravity specifically, set a Permission rule denying `write_file` on `scripts/` and `ui/` (Deny Read also implies Deny Write, but a Read-allow + Write-deny pair is what you want here so the agent can still execute/inspect the script), and/or add a Rules file (`.agents/rules/`) scoped to `scripts/*.py` and `ui/*.html` stating these files are not to be edited. This makes the restriction structural rather than something the agent has to remember on its own.

---

## Purpose & Overview
Evaluates real estate purchase vs. renting + investing (stocks/funds) in Turkey using quantitative financial modeling. Accounts for inflation-indexed capital gains tax, economically-optimal dynamic refinancing, P/R mean reversion, and buy/sell-side transaction fees.

## When to Invoke This Skill
Trigger this skill when the user prompt contains:
- "Ev mi alsam kirada mı kalsam?" / "Konut mu borsa mı?"
- Property listing details (e.g., price, rent, location, down payment).
- Real estate financial decision queries in Turkey.

---

## Execution Rules & CLI Invocation

### Step 0: Comparable-Rent Protocol (when target rent is not supplied)

1. Keep the user's/listing's target sale price unchanged.
2. Search the web for current rental listings in the same neighborhood/district.
3. Filter toward the target property's room count, approximate m², building age and quality. Exclude obvious luxury/residence/furnished outliers unless the target matches them.
4. Use a robust central estimate of the comparable rents and pass it as `--rent`. State the estimated rent and enough context for the user to understand its quality.
5. Comparable sale prices may be used only as a sanity check; do not replace the target listing price.

### Step 1: Dynamic Mortgage Rate Protocol (do this before running the script)

1. Look up current average monthly housing mortgage interest rates in Turkey.
2. Convert to annual nominal: `Nominal_Annual = (1 + r_monthly)^12 - 1`.
3. Convert to real via Fisher equation using a researched inflation expectation: `Real_Rate = (1 + Nominal_Annual) / (1 + Expected_Inflation) - 1`.
4. Pass the result explicitly as `--mortgage-real <value>`.

**If you skip this step and omit `--mortgage-real`, the script will run with a generic fallback and print a `RESULT|WARNING|MORTGAGE_RATE_DEFAULTED` line — always surface that warning to the user rather than presenting the result as if it used current market data.**

### Step 2: Execute the script

```bash
python scripts/buy_vs_rent.py --price <PRICE> --rent <RESEARCHED_OR_SUPPLIED_RENT> --mortgage-real <VALUE> --down-pct <DOWN_PCT|default=0.50> --hold 10
```

- `--price`: required and must remain the target listing price. `--rent`: required by the CLI, but research it automatically from comparable rentals when the user has not supplied it and enough property details are available.
- `--down-pct`: defaults to `0.50` if the user doesn't specify.
- `--hold`: planning horizon in years. **Default 10 unless the user explicitly requests otherwise.**
- `--term`: mortgage term in years (default `10`).
- `--buy-tx-cost` / `--sell-tx-cost` / `--cum-inflation` / `--current-pr`: optional, pass researched values from Step 2's data-gathering if you have them; sensible defaults are baked into the script otherwise.

### Playground vs. CLI — when to use which

- **No listing yet (user hasn't given a price/rent, or is asking a general "should I buy or rent" question)**: this is exactly what the playground is for. Offer it immediately alongside asking for specifics (see Execution Contract, rule 2) — don't gate it behind an explicit "let me tune parameters myself" phrase, since most people won't know to ask for it by name.
- **Real listing in hand (user gave price/rent, or a link)**: run the CLI so the response is grounded in a single execution's STDOUT — the playground is a supplement for exploration, not a substitute for a real evaluation once real numbers exist.

`ui/playground.html` is a standalone HTML file using the **same financial engine** as the script (verified numerically to match), with sliders for price/rent/down payment/mortgage rate/stock return/holding period.

### Delivering the playground — this depends on the host platform, adapt accordingly

A skill's instructions can't make a host application render something it doesn't support — whether the playground shows up as a live inline widget or just a file path is a property of the platform running the skill, not something fixable from here. Pick the best available option for the platform you're on:

- **Platform renders HTML artifacts/previews inline in the chat itself** (e.g. Claude.ai): present the file directly — it renders as an interactive widget the user can use immediately, no further action needed.
- **Agentic IDE with terminal/shell access, but no inline chat preview** (e.g. Antigravity, Claude Code, Cursor): don't just describe the file and stop there — actually open it in the user's default browser via a shell command, so they land on a working UI instead of a text description they have to act on themselves:
  - macOS: `open ui/playground.html`
  - Windows: `start ui/playground.html` (or `start "" "ui\playground.html"` from cmd)
  - Linux: `xdg-open ui/playground.html`
  - Detect the OS first (or try the appropriate command for the environment you're told you're in) and mention in the reply that you've opened it, with the file path as a fallback in case the command fails or a browser doesn't pop up.
- **No file system / no shell access** (pure text chat with no code execution): there's nothing more to do here — describe the file's location/purpose and fall back to the CLI numeric comparison, which works everywhere.

---

## Output Format

The script's STDOUT has two parts, separated by a `---` line:
- Above the separator: `RESULT|...` machine-readable lines (verdict, horizon, price/rent, amortization, initial outlay, monthly payment, hurdle rates in both real and nominal terms, saturation flags, benchmark).
- Below the separator: a compact, already-formatted summary in the same language/units.

Your reply to the user should be built from the STDOUT fields, in this shape:

### Section 1 — Özet
- Satış Fiyatı, Aylık Kira, Brüt Amortisman Süresi, Başlangıç Nakit Çıkışı, Aylık Taksit — read directly from `RESULT|PRICE`, `RESULT|RENT_MONTHLY`, `RESULT|GROSS_AMORTIZATION_YEARS`, `RESULT|INITIAL_OUTLAY`, `RESULT|MONTHLY_PAYMENT`.
- One-line verdict from `RESULT|VERDICT` and `RESULT|REFI|diff_pct`.

### Section 2 — Hurdle Rate Karar Matrisi
Render a table from the three `RESULT|HURDLE|...` lines (TIE / +15% / +35%), showing both the real and nominal return each target needs. **If a line's `SATURATED` flag is `True`, don't print a fake percentage** — say plainly that no realistic hurdle rate exists at these inputs (one side dominates regardless of stock performance), per the script's own message.

### Section 3 — Benchmark & Required Alpha
Compare all three hurdle rates against `RESULT|BENCHMARK|SP500_NET_REAL` (currently 7.80%). Surface the corresponding `RESULT|ALPHA|...` values prominently: this is the extra annual real performance above the normalized equity benchmark required to tie buying, beat it by 15%, or beat it by 35%. Treat the benchmark as a long-run normalized reference, not a guaranteed forward return.

**Don't** add lifestyle/behavioral advice ("ev alırsan kafan rahat eder" etc.) — keep it quantitative.

---

## Notes on Removed Features (v2.2 → v2.4)

- Monte Carlo simulation and the `--sims`/`--stock-vol`/`--appreciation-vol` flags were removed in v2.2 and are gone entirely now (the flags previously did nothing since the function was deleted but the flags stayed — that's fixed). Say so if the user asks about volatility ranges; it can be re-added as an explicit feature request.
- `--export-html` and the standalone `generate_ui.py` script are removed. There is now exactly one interactive UI: `ui/playground.html`, described above.


## v2.4 Refinancing Principle
- Do not force refinancing in a fixed calendar year.
- Model the real mortgage rate as converging from today's researched real rate toward `--refi-target-real` over `--refi-normalize-years`.
- The engine evaluates candidate refinance years including `--refi-cost` and selects refinancing only when it reduces total remaining real debt-service cost.
- Do not add a separate property-price demand shock merely because refinancing occurs. P/R normalization remains the property valuation mechanism.
