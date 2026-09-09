# Portfolio Analytics Methodology

## Scope

This layer demonstrates account-management risk analytics after origination. It uses 3,000 deterministic synthetic Australian-labelled accounts joined to public RBA/ABS macroeconomic series. Results are portfolio demonstrations, not estimates of an Australian lender's actual loss experience.

## Delinquency and Roll Rates

Monthly status is represented as `CURRENT`, `DPD30`, `DPD60`, `DPD90`, or `DEFAULT`. The roll-rate matrix uses each account's next observed monthly status and reports transition counts and row-normalised transition rates. Cure and deterioration paths are therefore visible separately.

## Vintage Analysis

Accounts are grouped by origination quarter. For each months-on-book point, the output reports active accounts, monthly defaults, cumulative defaults, exposure, and cumulative defaults divided by original cohort size. Comparing cohorts at the same seasoning point avoids confusing account age with underwriting quality.

## Expected Loss

The demonstration uses:

`Expected Loss = stressed PD × LGD × EAD`

PD is adjusted with observed cash-rate and unemployment stress in the synthetic account generator. LGD is product-sensitive and EAD is the closing account balance. This is an analytical simplification and not an implementation of accounting impairment requirements.

## Stress Scenarios

| Scenario | PD multiplier | LGD uplift |
| --- | ---: | ---: |
| Base | 1.00 | 0.00 |
| Moderate | 1.35 | 0.05 |
| Severe | 1.80 | 0.12 |

The scenario multipliers are transparent portfolio assumptions, not RBA forecasts. They show sensitivity of losses to worsening default frequency and recovery severity.

## Population Stability

The PSI compares the first six and latest six reporting months using PD bands fixed from the reference sample. The current run produces a high PSI because later macro conditions shift stressed PDs out of the two lowest reference bands, while account maturity and attrition also change the active population. It should be interpreted as a monitoring trigger requiring decomposition, not proof that a model has failed.

## Latest Demonstration Results

- Latest exposure: AUD 7.49 million.
- 30+ DPD balance rate: 2.87%.
- 90+ DPD balance rate: 1.72%.
- Simulated defaults: 231.
- Base expected loss: AUD 232,814.
- Severe expected loss: AUD 520,680, or 123.6% above base.
- PSI: 2.404, indicating a material shift in the synthetic monitored population.

