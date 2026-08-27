# 🏠 Turkey House Buy vs. Rent Financial Engine

A quantitative AI agent skill that determines whether buying a property or renting and investing the difference (in stocks, funds, or ETFs) is more profitable over a default **10-year horizon**.

When a user provides a **house listing link or price/rent details**, the model calculates the **Hurdle Rate ($r_s^*$)** — the exact annual real return the tenant's investment portfolio must achieve to equal the financial return of buying.

---

## 📐 Mathematical Model & Formulas

### 1. Buyer Final Net Wealth ($W_{\text{buy}}$)
$$W_{\text{buy}} = H_T \cdot (1 - c_{\text{sell}}) - B_T - T_{\text{tax}}$$
* $H_T$: Terminal property value at year $T$, adjusted for Price-to-Rent mean reversion ($a_{\text{catchup}}$) and mortgage demand shocks ($\alpha \Delta r$).
* $c_{\text{sell}}$: Sell-side transaction fees (default: 4% tapu harcı & agent).
* $B_T$: Remaining mortgage principal balance at year $T$.
* $T_{\text{tax}}$: Turkish capital gains tax (exempt after 5 years via *GVK Mük. m.80*; inflation-indexed cost basis if $< 5$ years).

### 2. Tenant Investment Portfolio ($W_{\text{rent}}$)
* **Initial Capital:** $W_0 = \text{DownPayment} + c_{\text{buy}}$ (Initial cash committed to portfolio instead of house purchase).
* **Annual Compounding & Cash Flow Differentials:**
$$W_t = W_{t-1} \cdot (1 + r_s) + \underbrace{\left[12 \cdot P_t + M_t - 12 \cdot R_t\right]}_{\text{Annual cash difference invested into portfolio}}$$
  * $r_s$: Annual real stock portfolio return.
  * $P_t$: Monthly mortgage installment.
  * $M_t$: Annual ownership & maintenance cost ($1.5\% \cdot H_t$).
  * $R_t$: Monthly rent paid.

### 3. Hurdle Rate Solver ($r_s^*$)
Finds $r_s^*$ using bisection search such that:
$$W_{\text{rent}}(r_s^*) = W_{\text{buy}}$$
* If your expected portfolio return $> r_s^* \implies$ **Rent & Invest wins**.
* If your expected portfolio return $< r_s^* \implies$ **Buying wins**.

---

## ⚡ Quick Usage

### CLI Execution
```bash
python scripts/buy_vs_rent.py --price 7850000 --rent 42000 --mortgage-real 0.138
```
*(Defaults: 10-year horizon, 50% down payment, 10-year loan term)*

### Output Example
```text
• Konut Fiyatı           : 7,850,000 TL | Aylık Kira: 42,000 TL
• Amortisman             : 15.6 Yıl     | Aylık Taksit: 63,400 TL

📊 SONUÇ (10 Yıl): 🏆 EV SATIN ALMAK KAZANIYOR (+1.42M TL)
📈 EŞİK GETİRİ (Hurdle Rate): Kiracının başa baş gelmesi için portföy getirisi en az TÜFE + %8.4 olmalıdır.
```

---

## 🎮 Web Playground

Open `ui/playground.html` in any browser to dynamically adjust sliders for price, rent, mortgage rate, stock returns, and horizon with real-time interactive charts.

---

## 📄 License
MIT License - see [LICENSE](LICENSE) for details.
