# General Insurance Pricing & Claims Reserving | Python + R

A reproducible intermediate-level actuarial portfolio project, with **two independent analyses**:

1. **Pricing (Python):** French Motor Third-Party Liability (freMTPL2), policy-level frequency and claim amounts; Poisson frequency GLM with log exposure offset and Gamma claim-severity GLM; pure premium and illustrative expense-loaded premium.
2. **Reserving (R):** `ChainLadder::RAA`, a published cumulative paid-loss development triangle; manual volume-weighted age-to-age factors, deterministic Chain Ladder ultimate claims and outstanding paid-loss reserve, cross-checked against the `ChainLadder` package.

**Data provenance:** freMTPL2 is a published motor insurance teaching/research dataset distributed through the R package CASdatasets. RAA is a published historical triangle distributed through the ChainLadder R package. It is used as a standard actuarial example; this project does **not** claim the triangle comes from the same insurer or portfolio as freMTPL2, nor independently verify the original underlying individual transactions. No synthetic observations are represented as real insurance results. Synthetic data are used **only in unit tests**.

## Requirements

Python 3.10+ and R 4.2+ with internet access for the first dataset/package installation. The data are **not bundled**; they are fetched by the user through their source R packages. Package licenses and dataset usage terms should be checked before redistribution.

## Reproduce

From the repository root:

```bash
python -m pip install -r requirements.txt
Rscript r/01_export_pricing_data.R
python -m python.pricing --frequency data/freMTPL2freq.csv --severity data/freMTPL2sev.csv
Rscript r/02_reserving.R
python -m pytest -q
```

If CASdatasets is not available from the specified repository, install it using the current instructions on the CASdatasets project site. The data export script is intentionally kept separate from the pricing script so data provenance is explicit.

## Outputs

- `outputs/pricing_summary.csv`: observed portfolio metrics and total modelled pure premium
- `outputs/policy_prices.csv`: annualised expected frequency, severity and pure premium per policy
- `outputs/frequency_model.txt` and `severity_model.txt`: GLM diagnostics and coefficients
- `outputs/development_factors.csv`: volume-weighted link ratios
- `outputs/reserve_estimates.csv`: origin-year latest paid, ultimate and outstanding reserves

## Actuarial decisions and limitations

- **Frequency** is modelled as Poisson claim count with log(exposure) offset. The offset accounts for unequal policy exposure periods.
- **Severity** is modelled as positive claim amount per reported claim, weighted by claim counts. This is an approximation using policy-aggregated claims and does not model claim-level severity variation separately.
- **Pure premium** = predicted annual claim frequency × predicted average claim severity. An **illustrative** 25% expense ratio produces a loaded indication, not an actual market quote or insurer-approved rate.
- Models use simple linear predictors and a small number of explanatory variables. Before production use, add a holdout validation set, calibration, residual checks, exposure caps and treatment of large losses, inflation and coverage differences.
- The reserving method uses volume-weighted deterministic Chain Ladder and assumes historical development patterns continue. The result is **unpaid paid-loss reserve**, not necessarily pure IBNR: it can include case outstanding and IBNR. No tail factor is added. Uncertainty, claims inflation, changes in claims handling and case reserves are not modelled.
- **Do not add the pricing and reserving results together**: the portfolios, currencies and valuation bases differ.

## Testing and status

Run `python -m pytest -q` for automated Python checks. The test fixtures are simulated and check identities, data validation, GLM output and expense loading; they do not validate the fit on the full real dataset. The R script contains `stopifnot` assertions, including a comparison of manually calculated ultimate losses against the package implementation. Run it in an R installation before describing the R portion as executed or validated.

## CV wording (use after you have run and understood the project)

> Developed an actuarial portfolio project in Python and R using published insurance datasets; fitted Poisson and Gamma GLMs for claim frequency/severity pricing and calculated pure premium indications; implemented and validated deterministic Chain Ladder reserve estimates using claims development triangles.

## Sources

- CASdatasets: https://cas.uqam.ca/
- ChainLadder R package: https://cran.r-project.org/package=ChainLadder
- statsmodels GLM documentation: https://www.statsmodels.org/stable/glm.html
