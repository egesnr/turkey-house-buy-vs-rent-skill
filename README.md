# 🏠 Turkey House Buy vs. Rent Financial Engine (AI Agent Skill)

A quantitative financial engine that evaluates **buying a house** vs. **renting and investing the difference** (stocks, ETFs, funds), specifically calibrated for the Turkish economic and legal market.

Designed to work as a **universal AI Agent Skill** (compatible with Claude Code, Cursor, Antigravity, OpenAI agents, etc.) or as a **standalone Python CLI & Web Tool**.

---

## ⚡ Key Features

- **Turkish Tax & Legal Rules Built-in:** Accounts for the 5-year capital gains exemption (*GVK Mük. m.80*), deed acquisition & sale fees (*tapu harcı*), and legal early refinancing caps (*Law No. 6502*).
- **Hurdle Rate Solver:** Determines the exact net real return a tenant's investment portfolio must generate to match or beat homeownership.
- **Dynamic Defaults:** Default analysis horizon is **10 years** and default down payment is **50%**.
- **Interactive UI Included:** Comes with a standalone visual calculator (`ui/playground.html`) with real-time charts and dynamic sliders.

---

## 🚀 Quick Example

### 1. Run via CLI:
```bash
python scripts/buy_vs_rent.py --price 7850000 --rent 42000 --mortgage-real 0.138
```
*(Defaults applied: `--hold 10` years, `--down-pct 0.50`)*

### 2. Sample Output:
```text
============================================================
              TÜRKİYE KONUT ALIM / KİRA ANALİZİ
============================================================
• Konut Fiyatı           : 7,850,000 TL
• Aylık Kira             : 42,000 TL
• Brüt Amortisman        : 15.6 Yıl
• Aylık Taksit           : 63,400 TL

📊 SONUÇ (10 Yıl Sonra):
🏆 EV SATIN ALMAK KAZANIYOR (+1.42M TL Net Servet Farkı)

📈 EŞİK GETİRİ (Kiracının Ev Sahibini Yakalaması İçin):
Kiracı portföyünün yıllık en az TÜFE + %8.4 reel getiri üretmesi gerekir.
============================================================
```

---

## 🎮 Interactive Web Playground

Open `ui/playground.html` in any browser to interactively test scenarios with sliders:
- Property Price & Monthly Rent
- Down payment percentage (Default: 50%)
- Real mortgage rate & expected inflation
- Stock market real return expectations
- Horizon / Duration (Default: 10 Years)

---

## 🤖 Using as an AI Agent Skill

This repository follows standard Agent Skill conventions (`SKILL.md` instruction file).

### How AI Agents Use This Skill:
1. When asked *"Ev mi alsam kirada mı kalsam?"* or given property listing numbers, the AI agent inspects `SKILL.md`.
2. The agent executes `scripts/buy_vs_rent.py` with the provided parameters.
3. If inputs are missing, the agent presents `ui/playground.html` for instant user exploration.

### Installation:
Clone into your AI agent's skill directory:
```bash
# General AI agents / workspace skills
git clone https://github.com/egesnr/turkey-house-buy-vs-rent-skill.git .agents/skills/turkey-house-buy-vs-rent
```

---

## 📄 License
MIT License - see [LICENSE](LICENSE) for details.
