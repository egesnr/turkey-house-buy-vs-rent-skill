#!/usr/bin/env python3
"""
Turkey Buy vs. Rent Evaluator Engine (v2.4)
Calculates real estate vs. stock market wealth differential with:
- Two-phase P/R mean reversion
- Dynamic economically-optimal Mortgage Refinancing (2% refinancing cost assumption)
- Long-run mortgage-rate normalization path (no property-price demand shock)
- 5-Year Turkish Capital Gains Tax Exemption (GVK Mük. m.80), inflation-indexed cost basis
- Buy-side AND sell-side transaction costs (tapu harci etc.)
- Hurdle Rate Solver (Esik Getiri Motoru for Tie, +15%, +35% wealth targets)

CHANGELOG v2.2 -> v2.3 (bug fixes, in response to review):
- FIX: STDOUT now prints every field the SKILL.md output template requires
  (price, rent, gross amortization period, initial cash outlay, monthly
  installment, and NOMINAL hurdle returns alongside the real ones). v2.2's
  template asked for fields that never existed in STDOUT, which forced a
  choice between violating the "no hallucinated numbers" rule or leaving
  the template half-empty.
- FIX: nominal hurdle returns are derived via Fisher equation using the
  annualized rate implied by --cum-inflation (not invented separately), so
  they still trace back to a value the caller supplied.
- FIX: removed --sims / --stock-vol / --appreciation-vol -- these were dead
  flags left over after Monte Carlo was removed in v2.2; they silently did
  nothing if set. Monte Carlo can be reintroduced later as its own flag if
  wanted.
- FIX: --mortgage-real now has no baked-in numeric default. If omitted, the
  script computes a fallback AND prints a RESULT|WARNING line, so it is
  never silently used without the caller (or the person reading STDOUT)
  knowing a real value wasn't supplied.
- FIX: hurdle-rate binary search now detects when the answer sits at the
  edge of its search range (no realistic finite hurdle rate exists -- e.g.
  buying dominates regardless of stock returns) and reports SATURATED
  instead of a fake-precise percentage.
- Unchanged from v2.2: transaction-cost split, inflation-indexed capital
  gains basis, hurdle-rate solver logic itself.
"""
import argparse
import math
import sys

# Fallback used only if --mortgage-real is omitted. Callers (the SKILL.md
# dynamic-rate protocol) should always compute and pass a fresh value --
# this exists so the script never crashes, not so it's silently relied on.
FALLBACK_MORTGAGE_REAL = 0.06


def validate_inputs(args):
    """
    Fails fast with a clean RESULT|ERROR line + exit(1) instead of letting
    bad input reach the math and raise a raw traceback. This matters for
    agentic callers: a traceback reads as "the code is broken, patch it";
    a clean validation message reads as "bad input, fix the arguments" --
    which is what should actually happen. Never edit this script to work
    around a validation failure; fix the CLI arguments instead.
    """
    errors = []
    if args.price is None or args.price <= 0:
        errors.append("--price must be a positive number")
    if args.rent is None or args.rent <= 0:
        errors.append("--rent must be a positive number")
    if not (0 <= args.down_pct < 1):
        errors.append("--down-pct must be in [0, 1)")
    if args.term < 1:
        errors.append("--term must be >= 1")
    if args.hold < 1:
        errors.append("--hold must be >= 1")
    if args.normal_pr <= 0:
        errors.append("--normal-pr must be positive")
    if args.buy_tx_cost < 0 or args.sell_tx_cost < 0 or args.sell_tx_cost >= 1:
        errors.append("--buy-tx-cost must be >= 0 and --sell-tx-cost must be in [0, 1)")
    if args.cum_inflation <= 0:
        errors.append("--cum-inflation must be positive")

    if errors:
        for e in errors:
            print(f"RESULT|ERROR|{e}")
        print("---")
        print("Input validation failed -- fix the CLI arguments above and re-run. "
              "Do not modify this script to work around bad input.")
        sys.exit(1)


def derived_catchup_rate(current_pr, normal_pr, rent_growth, years_to_close):
    years_to_close = max(1, years_to_close)
    gap = current_pr / normal_pr - 1
    return rent_growth - (1 / years_to_close) * math.log(1 + gap)


def monthly_payment(loan, annual_rate, term_years):
    mr = annual_rate / 12
    months = term_years * 12
    if mr == 0:
        return loan / months
    return loan * mr / (1 - (1 + mr) ** (-months))


def remaining_balance(loan, annual_rate, term_years, years_elapsed):
    if years_elapsed >= term_years:
        return 0.0
    mr = annual_rate / 12
    n_months = term_years * 12
    t_months = years_elapsed * 12
    if mr == 0:
        return loan * (1 - t_months / n_months)
    top = (1 + mr) ** n_months - (1 + mr) ** t_months
    bottom = (1 + mr) ** n_months - 1
    return loan * top / bottom


def choose_refi_plan(initial_loan, mortgage_rate, term, target_rate, normalize_years, refi_cost=0.02):
    """Choose the single refinancing year that minimizes remaining real debt-service cost.

    The market mortgage rate is assumed to converge linearly from today's real rate
    toward a long-run normalized real rate. Refinancing is not forced in a fixed year:
    every candidate year is evaluated including the refinancing cost, and no refinance
    is chosen when staying with the original loan is cheaper.
    """
    if target_rate is None or target_rate >= mortgage_rate or term <= 1:
        return None, None
    original_payment = monthly_payment(initial_loan, mortgage_rate, term)
    best = (original_payment * term * 12, None, None)
    for year in range(1, term):
        frac = min(1.0, year / max(1, normalize_years))
        market_rate = mortgage_rate + (target_rate - mortgage_rate) * frac
        balance = remaining_balance(initial_loan, mortgage_rate, term, year)
        remaining_years = term - year
        new_loan = balance * (1 + refi_cost)
        new_payment = monthly_payment(new_loan, market_rate, remaining_years)
        paid_before = original_payment * year * 12
        total_cost = paid_before + new_payment * remaining_years * 12
        if total_cost < best[0]:
            best = (total_cost, year, market_rate)
    return best[1], best[2]


def simulate_one(price, rent_month, down_pct, mortgage_rate, term, hold,
                 own_cost_rate, buy_tx_cost, sell_tx_cost, cum_inflation,
                 a_catchup, years_to_close, rent_growth, stock_return,
                 refi_target_rate=None, refi_normalize_years=5, refi_cost=0.02,
                 appreciation_noise_fn=None, stock_noise_fn=None):

    initial_loan = 1.0 - down_pct
    current_pay = monthly_payment(initial_loan, mortgage_rate, term)
    current_loan_base = initial_loan
    current_term = term
    current_rate = mortgage_rate
    elapsed_since_refi = 0
    refi_year, refi_rate = choose_refi_plan(
        initial_loan, mortgage_rate, term, refi_target_rate, refi_normalize_years, refi_cost
    )

    r0_month = rent_month / price
    H = 1.0
    upfront_outlay = down_pct + buy_tx_cost
    portfolio = upfront_outlay

    for year in range(1, hold + 1):
        elapsed_since_refi += 1

        base_growth = a_catchup if year <= years_to_close else rent_growth
        growth = base_growth
        if appreciation_noise_fn:
            growth += appreciation_noise_fn()
        H *= (1 + growth)

        if refi_year and year == refi_year and refi_rate and refi_rate < mortgage_rate:
            bal_before = remaining_balance(current_loan_base, current_rate, current_term, elapsed_since_refi - 1)
            current_loan_base = bal_before * (1 + refi_cost)
            current_term = term - refi_year
            current_rate = refi_rate
            elapsed_since_refi = 1
            current_pay = monthly_payment(current_loan_base, current_rate, current_term)

        rent_i = r0_month * (1 + rent_growth) ** (year - 1)
        own_cost_i = own_cost_rate * H
        pay_this_year = current_pay if elapsed_since_refi <= current_term else 0.0
        diff = 12 * pay_this_year + own_cost_i - 12 * rent_i

        s = stock_return
        if stock_noise_fn:
            s += stock_noise_fn()
        portfolio = portfolio * (1 + s) + diff

    balance = remaining_balance(current_loan_base, current_rate, current_term, elapsed_since_refi)

    net_sale_proceeds = H * (1 - sell_tx_cost)
    cap_gains_tax = 0.0
    if hold < 5:
        indexed_cost_basis = 1.0 * cum_inflation
        real_gain = max(0.0, net_sale_proceeds - indexed_cost_basis)
        cap_gains_tax = real_gain * 0.20

    buy_wealth = net_sale_proceeds - balance - cap_gains_tax
    return buy_wealth, portfolio


def find_hurdle_rate(args, a_catchup, target_mult=1.0, use_refi=True):
    """
    Finds the real stock return required for the renter to hit
    buy_wealth * target_mult. Returns (rate, saturated) where saturated
    is True if the answer sits at the edge of the search range, meaning
    no realistic finite hurdle rate exists (one side structurally
    dominates regardless of stock performance).
    """
    refi_target = args.refi_target_real if use_refi else None

    target_buy_wealth, _ = simulate_one(
        args.price, args.rent, args.down_pct, args.mortgage_real, args.term, args.hold,
        args.own_cost, args.buy_tx_cost, args.sell_tx_cost, args.cum_inflation,
        a_catchup, args.years_to_close, args.rent_growth, 0.0,
        refi_target_rate=refi_target, refi_normalize_years=args.refi_normalize_years, refi_cost=args.refi_cost
    )
    target_portfolio = target_buy_wealth * target_mult

    low, high = -0.5, 3.0
    for _ in range(50):
        mid = (low + high) / 2
        _, rent_w = simulate_one(
            args.price, args.rent, args.down_pct, args.mortgage_real, args.term, args.hold,
            args.own_cost, args.buy_tx_cost, args.sell_tx_cost, args.cum_inflation,
            a_catchup, args.years_to_close, args.rent_growth, mid,
            refi_target_rate=refi_target, refi_normalize_years=args.refi_normalize_years, refi_cost=args.refi_cost
        )
        if rent_w < target_portfolio:
            low = mid
        else:
            high = mid

    result = (low + high) / 2
    # Search brackets are deliberately wide (-50% to +300% real return) so the
    # bisection always has room to converge. But a mathematically-found
    # crossing point outside any historically plausible stock-market range
    # (roughly -30% to +40% real, annualized) isn't a meaningful hurdle --
    # it means one side structurally dominates for any realistic assumption.
    # Flag both true boundary hits and "found but absurd" results the same way.
    REALISTIC_MIN, REALISTIC_MAX = -0.30, 0.40
    saturated = (result <= REALISTIC_MIN) or (result >= REALISTIC_MAX)
    return result, saturated


def main():
    p = argparse.ArgumentParser(description="Turkey Buy vs Rent Evaluator (v2.4)")
    p.add_argument("--price", type=float, required=True)
    p.add_argument("--rent", type=float, required=True)
    p.add_argument("--down-pct", type=float, default=0.50)
    p.add_argument("--mortgage-real", type=float, default=None,
                    help="Real annual mortgage rate. If omitted, a fallback is used AND flagged in STDOUT -- "
                         "always compute and pass a fresh value when you have current rate data.")
    p.add_argument("--term", type=int, default=10)
    p.add_argument("--hold", type=int, default=10)
    p.add_argument("--own-cost", type=float, default=0.015)
    p.add_argument("--buy-tx-cost", type=float, default=0.02)
    p.add_argument("--sell-tx-cost", type=float, default=0.04)
    p.add_argument("--cum-inflation", type=float, default=1.8,
                    help="Cumulative inflation factor over the hold period. Only affects results when --hold < 5 "
                         "(capital gains tax basis indexing) and the nominal-return conversion of hurdle rates.")
    p.add_argument("--current-pr", type=float, default=None)
    p.add_argument("--normal-pr", type=float, default=18.0)
    p.add_argument("--years-to-close", type=int, default=7)
    p.add_argument("--rent-growth", type=float, default=0.01)
    p.add_argument("--stock-return", type=float, default=0.05)
    p.add_argument("--refi-target-real", type=float, default=0.04,
                    help="Long-run normalized real mortgage rate used for the refinancing path.")
    p.add_argument("--refi-normalize-years", type=int, default=5,
                    help="Years over which the market real mortgage rate converges toward --refi-target-real.")
    p.add_argument("--refi-cost", type=float, default=0.02,
                    help="Refinancing cost as a fraction of remaining principal (default 2%%).")
    p.add_argument("--export-html", type=str, default=None,
                    help="Reserved -- HTML playground is now a separate static file (see ui/playground.html), "
                         "not generated by this script.")
    args = p.parse_args()

    validate_inputs(args)

    mortgage_real_is_fallback = args.mortgage_real is None
    if mortgage_real_is_fallback:
        args.mortgage_real = FALLBACK_MORTGAGE_REAL

    if args.current_pr is None:
        args.current_pr = args.price / (args.rent * 12.0)

    a_catchup = derived_catchup_rate(args.current_pr, args.normal_pr, args.rent_growth, args.years_to_close)

    # Annualized inflation rate implied by --cum-inflation, used only to
    # convert real hurdle rates to nominal for display (Fisher equation).
    annual_inflation = args.cum_inflation ** (1.0 / max(1, args.hold)) - 1.0

    h_tie, sat_tie = find_hurdle_rate(args, a_catchup, target_mult=1.0)
    h_pass15, sat_15 = find_hurdle_rate(args, a_catchup, target_mult=1.15)
    h_pass35, sat_35 = find_hurdle_rate(args, a_catchup, target_mult=1.35)

    def to_nominal(real_rate):
        return (1 + real_rate) * (1 + annual_inflation) - 1

    buy_dyn, rent_dyn = simulate_one(
        args.price, args.rent, args.down_pct, args.mortgage_real, args.term, args.hold,
        args.own_cost, args.buy_tx_cost, args.sell_tx_cost, args.cum_inflation,
        a_catchup, args.years_to_close, args.rent_growth, args.stock_return,
        refi_target_rate=args.refi_target_real, refi_normalize_years=args.refi_normalize_years, refi_cost=args.refi_cost
    )
    diff_dyn = (buy_dyn - rent_dyn) * 100
    verdict = "BUY" if diff_dyn >= 0 else "RENT"

    initial_outlay = (args.down_pct + args.buy_tx_cost) * args.price
    monthly_pmt = monthly_payment(1.0 - args.down_pct, args.mortgage_real, args.term) * args.price
    gross_amortization_years = args.price / (args.rent * 12.0)
    refi_year_selected, refi_rate_selected = choose_refi_plan(
        1.0 - args.down_pct, args.mortgage_real, args.term, args.refi_target_real,
        args.refi_normalize_years, args.refi_cost
    )

    if mortgage_real_is_fallback:
        print(f"RESULT|WARNING|MORTGAGE_RATE_DEFAULTED|used={args.mortgage_real*100:.2f}% (not supplied -- "
              f"treat this run as illustrative only, re-run with a researched --mortgage-real)")

    print(f"RESULT|VERDICT|{verdict}")
    print(f"RESULT|HORIZON_YEARS|{args.hold}")
    print(f"RESULT|PRICE|{args.price:.0f}")
    print(f"RESULT|RENT_MONTHLY|{args.rent:.0f}")
    print(f"RESULT|GROSS_AMORTIZATION_YEARS|{gross_amortization_years:.1f}")
    print(f"RESULT|INITIAL_OUTLAY|{initial_outlay:.0f}")
    print(f"RESULT|MONTHLY_PAYMENT|{monthly_pmt:.0f}")
    print(f"RESULT|REFI|diff_pct={diff_dyn:+.1f}|selected_year={refi_year_selected if refi_year_selected else 'NONE'}|selected_real_rate={(f'{refi_rate_selected*100:.2f}%' if refi_rate_selected is not None else 'NONE')}")
    print(f"RESULT|HURDLE|TIE_REAL={h_tie*100:+.2f}%|TIE_NOMINAL={to_nominal(h_tie)*100:+.2f}%|SATURATED={sat_tie}")
    print(f"RESULT|HURDLE|PASS_15_REAL={h_pass15*100:+.2f}%|PASS_15_NOMINAL={to_nominal(h_pass15)*100:+.2f}%|SATURATED={sat_15}")
    print(f"RESULT|HURDLE|PASS_35_REAL={h_pass35*100:+.2f}%|PASS_35_NOMINAL={to_nominal(h_pass35)*100:+.2f}%|SATURATED={sat_35}")
    print(f"RESULT|BENCHMARK|SP500_NET_REAL=7.80%")
    if not sat_tie:
        print(f"RESULT|ALPHA|TIE_VS_SP500={(h_tie-0.078)*100:+.2f}pp")
    if not sat_15:
        print(f"RESULT|ALPHA|PASS_15_VS_SP500={(h_pass15-0.078)*100:+.2f}pp")
    if not sat_35:
        print(f"RESULT|ALPHA|PASS_35_VS_SP500={(h_pass35-0.078)*100:+.2f}pp")

    print("---")
    print(f"Gayrimenkul & Kredi Ozeti: {args.price:.0f} TL | Aylik Kira: {args.rent:.0f} TL | "
          f"Brut Amortisman: {gross_amortization_years:.1f} Yil | "
          f"Baslangic Nakit Cikisi: {initial_outlay:.0f} TL | Aylik Taksit: {monthly_pmt:.0f} TL")
    print(f"DECISION MATRIX ({args.hold}-Year Horizon):")
    for label, (rate, sat) in [("TIE with Buying", (h_tie, sat_tie)),
                                ("BEAT Buying by +15%", (h_pass15, sat_15)),
                                ("CRUSH Buying by +35%", (h_pass35, sat_35))]:
        if sat:
            print(f" - To {label}: NO FINITE HURDLE in a realistic range -- one side structurally dominates "
                  f"regardless of stock performance at these inputs.")
        else:
            print(f" - To {label}: Renter needs real return TUFE {rate*100:+.1f}% "
                  f"(nominal ~{to_nominal(rate)*100:+.1f}%)")
    print(f" - Benchmark Ref (S&P 500 20-Yr Net): TUFE +7.80%")


if __name__ == "__main__":
    main()
