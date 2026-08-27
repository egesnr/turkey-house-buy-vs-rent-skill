# 🏠 Turkey House Buy vs. Rent Financial Engine

A quantitative financial engine and AI agent skill that evaluates whether **buying a home** or **renting and investing the difference** (stocks, funds, ETFs) yields greater wealth over a default **10-year horizon**.

When a user provides a **property listing link or price/rent figures**, the model computes the exact **Hurdle Rate ($r_s^*$)** — the annual real portfolio return required for a tenant to break even with (or outperform) homeownership.

---

## 📐 Mathematical Model & Core Formulas

### 1. Dynamic Real Mortgage Rate (Fisher Equation)
$$\text{Real Rate} = \frac{1 + \text{Nominal Annual Rate}}{1 + \text{Expected Inflation}} - 1$$
* Converts Turkish monthly nominal mortgage rates ($r_{\text{monthly}}$) to annual nominal, then computes the true real borrowing cost.

---

### 2. Price-to-Rent (P/R) Mean Reversion
Real estate appreciation adjusts dynamically toward the historical equilibrium ($P/R_{\text{normal}} = 18.0$ years):
$$a_{\text{catchup}} = g_{\text{rent}} - \frac{1}{T_{\text{close}}} \ln\left(1 + \frac{P/R_{\text{current}}}{P/R_{\text{normal}}} - 1\right)$$
* $g_{\text{rent}}$: Real annual rent growth ($1\%/\text{year}$).
* $T_{\text{close}}$: Mean reversion convergence period (default: 7 years).

---

### 3. Dynamic Refinancing & Demand Shock Elasticity
If interest rates drop to long-term levels (e.g., Year 3 at $4\%$ real):
* **Refinanced Principal:** $B_{\text{refi}} = B_3 \cdot (1 + 0.02)$ *(incorporating the statutory 2% early settlement penalty under Law No. 6502)*.
* **Demand Shock on House Value:**
$$\Delta H_{\text{shock}} = \alpha \cdot (r_{\text{initial}} - r_{\text{refi}}) \quad (\alpha = 1.2)$$

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
$$W_t = W_{t-1} \cdot (1 + r_s) + \underbrace{\left[12 \cdot P_t + M_t - 12 \cdot R_t\right]}_{\text{Net cash savings invested each year}}$$
  * $r_s$: Real stock/fund portfolio return.
  * $P_t$: Monthly mortgage installment.
  * $M_t$: Annual ownership/maintenance cost ($1.5\% \cdot H_t$).
  * $R_t$: Monthly rent.

---

### 6. Hurdle Rate Solver ($r_s^*$) & Saturation Detection
Solves for $r_s^*$ via bisection:
$$W_{\text{rent}}(r_s^*) = W_{\text{buy}} \times \text{Target Multiplier} \quad (\text{Tie}=1.0\times, +15\%=1.15\times, +35\%=1.35\times)$$
* **Deterministic Precision:** Runs exact root-finding instead of volatile Monte Carlo simulations.
* **Saturation Flags:** If $r_s^* \le -30\%$ or $\ge +40\%$, flags `SATURATED` (one side structurally dominates across all realistic market scenarios).

---

## ⚡ Quick Usage

### CLI Execution
```bash
python scripts/buy_vs_rent.py --price 7850000 --rent 42000 --mortgage-real 0.138
```

### Sample Output
```text
============================================================
              TÜRKİYE KONUT ALIM / KİRA ANALİZİ
============================================================
• Konut Fiyatı           : 7,850,000 TL | Aylık Kira: 42,000 TL
• Amortisman             : 15.6 Yıl     | Aylık Taksit: 63,400 TL

📊 SONUÇ (10 Yıl): 🏆 EV SATIN ALMAK KAZANIYOR (+1.42M TL)
📈 EŞİK GETİRİ (Hurdle Rate): Kiracının başa baş gelmesi için portföy getirisi en az TÜFE + %8.4 olmalıdır.
============================================================
```

---

## 🎮 Interactive Web Playground

Open `ui/playground.html` in your browser to interactively test scenarios with sliders and real-time equity comparison charts.

---

## 📄 License
MIT License - see [LICENSE](LICENSE) for details.
