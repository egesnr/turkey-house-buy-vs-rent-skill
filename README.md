# 🏠 Turkey House Buy vs. Rent Financial Engine (AI SKILL)

A quantitative financial engine and AI agent skill that evaluates whether **buying a home** or **renting and investing the difference** (in stocks, funds, ETFs) yields greater net wealth over a default **10-year horizon**.

When a user provides a **property listing link or price/rent details**, the engine computes the exact **Hurdle Rates (`r_hurdle`)** — the annual portfolio returns (both real and nominal) a tenant must achieve to **Tie**, **Beat (+15%)**, or **Crush (+35%)** homeownership wealth.

---

## 🎮 Interactive Web Playground

> 🚀 **Live Demo:** [**👉 Open Live Playground in Your Browser**](https://egesnr.github.io/turkey-house-buy-vs-rent-skill/ui/playground.html)
> *(No installation needed — runs directly in your browser)*

<p align="center">
  <a href="https://egesnr.github.io/turkey-house-buy-vs-rent-skill/ui/playground.html">
    <img src="docs/playground_preview.png" alt="Interactive Web Playground Preview" width="760" style="max-width: 100%; border-radius: 8px;">
  </a>
</p>

The playground is a standalone HTML/JS reimplementation of the same financial engine (verified numerically to match the Python script), for exploring scenarios interactively without running any code. For a real listing, use the CLI below — that's the path the AI skill is required to take so every number is grounded in an actual execution instead of a model guess.

---

## 🚀 Quick Example & Real Output

### CLI Execution
```bash
python scripts/buy_vs_rent.py --price 7850000 --rent 42000 --mortgage-real 0.138
```

### Actual STDOUT
```text
RESULT|VERDICT|RENT
RESULT|HORIZON_YEARS|10
RESULT|PRICE|7850000
RESULT|RENT_MONTHLY|42000
RESULT|GROSS_AMORTIZATION_YEARS|15.6
RESULT|INITIAL_OUTLAY|4082000
RESULT|MONTHLY_PAYMENT|60471
RESULT|REFI|diff_pct=-1.0|selected_year=4|selected_real_rate=5.96%
RESULT|HURDLE|TIE_REAL=+4.90%|TIE_NOMINAL=+11.25%|SATURATED=False
RESULT|HURDLE|PASS_15_REAL=+6.56%|PASS_15_NOMINAL=+13.01%|SATURATED=False
RESULT|HURDLE|PASS_35_REAL=+8.49%|PASS_35_NOMINAL=+15.06%|SATURATED=False
RESULT|BENCHMARK|SP500_NET_REAL=7.80%
RESULT|ALPHA|TIE_VS_SP500=-2.90pp
RESULT|ALPHA|PASS_15_VS_SP500=-1.24pp
RESULT|ALPHA|PASS_35_VS_SP500=+0.69pp
---
Gayrimenkul & Kredi Ozeti: 7850000 TL | Aylik Kira: 42000 TL | Brut Amortisman: 15.6 Yil | Baslangic Nakit Cikisi: 4082000 TL | Aylik Taksit: 60471 TL
DECISION MATRIX (10-Year Horizon):
 - To TIE with Buying: Renter needs real return TUFE +4.9% (nominal ~+11.2%)
 - To BEAT Buying by +15%: Renter needs real return TUFE +6.6% (nominal ~+13.0%)
 - To CRUSH Buying by +35%: Renter needs real return TUFE +8.5% (nominal ~+15.1%)
 - Benchmark Ref (S&P 500 20-Yr Net): TUFE +7.80%
```

The block above the `---` is machine-readable (`RESULT|KEY|VALUE`), meant for an LLM agent to parse without guessing; the block below is a pre-formatted human summary in the same units. This is the real, current output of the command above — not a mockup.

### Reading It as a Table

| Field | Value |
|---|---|
| Sale Price | 7,850,000 TL |
| Monthly Rent | 42,000 TL |
| Gross Amortization | 15.6 years |
| Initial Cash Outlay | 4,082,000 TL |
| Monthly Installment | 60,471 TL |
| Optimal Refinance | Year 4, real rate 5.96% |
| **Verdict (10-yr horizon)** | **RENT** (renting + investing leads by 1.0% of property value) |

**Decision Matrix — Hurdle Rates**

| Target Scenario | Required Real Return | Required Nominal Return | vs. S&P 500 Benchmark (TÜFE +7.80%) |
|---|---|---|---|
| 🟰 Tie with buying | TÜFE +4.90% | ~11.25% | −2.90pp (easier than benchmark) |
| 📈 Beat buying by +15% | TÜFE +6.56% | ~13.01% | −1.24pp (easier than benchmark) |
| 🚀 Crush buying by +35% | TÜFE +8.49% | ~15.06% | +0.69pp (harder than benchmark) |

At these inputs, a renter only needs to match a normal diversified equity return to come out ahead of buying — beating it by 35% would require modestly outperforming the long-run S&P 500 benchmark.

---

## 📐 Mathematical Model & Formulas

### 1. Dynamic Real Mortgage Rate (Fisher Equation)
$$\text{Real Rate} = \frac{1 + \text{Nominal Annual Rate}}{1 + \text{Expected Inflation}} - 1$$

---

### 2. Price-to-Rent (P/R) Mean Reversion
Real estate appreciation adjusts dynamically toward historical equilibrium ($P/R_{\text{normal}} = 18.0$ years):
$$a_{\text{catchup}} = g_{\text{rent}} - \frac{1}{T_{\text{close}}} \ln\left(1 + \frac{P/R_{\text{current}}}{P/R_{\text{normal}}} - 1\right)$$
* $g_{\text{rent}}$: Real annual rent growth ($1\%/\text{year}$).
* $T_{\text{close}}$: Mean reversion convergence period (default: 7 years).

---

### 3. Dynamic, Cost-Aware Refinancing
The engine does **not** force refinancing in a fixed year. It models the market real mortgage rate converging linearly from today's rate toward `--refi-target-real` over `--refi-normalize-years`, then evaluates every candidate year and picks the one that minimizes total remaining real debt service — including the refinancing cost — refinancing only when it's actually cheaper than keeping the original loan:
$$B_{\text{refi}} = B_{\text{year}} \cdot (1 + c_{\text{refi}})$$
* $B_{\text{year}}$: Remaining loan balance at the candidate refinance year.
* $c_{\text{refi}}$: Refinancing cost as a fraction of remaining principal (default 2%).

Refinancing only changes the loan's payment schedule — it is not treated as a signal to also shock the property's value; P/R normalization (formula 2) remains the sole valuation mechanism.

---

### 4. Buyer Final Net Wealth ($W_{\text{buy}}$)
$$W_{\text{buy}} = H_T \cdot (1 - c_{\text{sell}}) - B_T - T_{\text{tax}}$$
* $H_T$: Terminal property value at year $T$.
* $c_{\text{sell}}$: Sell-side transaction fees (default: 4% tapu harcı & brokerage).
* $B_T$: Remaining mortgage debt balance at year $T$.
* $T_{\text{tax}}$: Turkish Capital Gains Tax (*GVK Mük. m.80*): **0% after 5 years**; if $<5$ years, $20\%$ on inflation-indexed real gains.

---

### 5. Tenant Investment Portfolio ($W_{\text{rent}}$)
* **Initial Capital:** $W_0 = \text{DownPayment} + c_{\text{buy}}$ (Default down payment: 50%, $c_{\text{buy}} = 2\%$).
* **Annual Compounding with Cash Flow Differences:**
$$W_t = W_{t-1} \cdot (1 + r_{\text{stock}}) + \underbrace{\left[12 \cdot P_t + M_t - 12 \cdot R_t\right]}_{\text{Net cash savings invested each year}}$$
  * $P_t$: Monthly mortgage installment.
  * $M_t$: Annual ownership/maintenance cost ($1.5\% \cdot H_t$).
  * $R_t$: Monthly rent.

---

### 6. Multi-Target Hurdle Rate Solver
Solves for the required stock return $r_{\text{target}}$ via bisection search:
$$W_{\text{rent}}(r_{\text{target}}) = W_{\text{buy}} \times \text{Target Multiplier}$$

Where target multipliers are:
* **TIE (1.00x):** Break-even portfolio return.
* **BEAT (+15% / 1.15x):** Renter achieves 15% higher terminal wealth.
* **CRUSH (+35% / 1.35x):** Renter achieves 35% higher terminal wealth.
* **Saturation Check:** If $r_{\text{target}} \le -30\%$ or $\ge +40\%$, flags `SATURATED` — no realistic finite hurdle rate exists at these inputs; one side structurally dominates regardless of stock performance.

---

## 📄 License
MIT License - see [LICENSE](LICENSE) for details.
