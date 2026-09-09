# Data Sources and Licensing

## Application Modelling Data

The probability-of-default modelling workflow uses OpenML `credit-g` (`data_id=31`), originally published as the UCI Statlog German Credit dataset under CC BY 4.0. Raw data are downloaded at runtime and are not committed to this repository.

## Australian Macroeconomic Data

The portfolio workflow downloads selected public series from the Reserve Bank of Australia statistical tables:

| Variable | Table | Series ID | Attribution |
| --- | --- | --- | --- |
| Cash rate target | F1.1 | FIRMMCRT | Source: Reserve Bank of Australia |
| Unemployment rate | H5 | GLFSURSA | Source: Australian Bureau of Statistics |
| Year-ended inflation | G1 | GCPIAGYP | Based on Australian Bureau of Statistics data |
| Personal credit growth | D1 | DGFACOP12 | Source: Reserve Bank of Australia |

- RBA statistical tables: <https://www.rba.gov.au/statistics/tables/>
- RBA copyright and data conditions: <https://www.rba.gov.au/copyright/>
- ABS privacy and legal terms: <https://www.abs.gov.au/privacy-and-legals>

RBA cash-rate and financial data are used under the RBA's stated financial-data conditions with attribution and no suggestion of endorsement. ABS material is attributed in accordance with its CC BY 4.0 terms. The repository caches source files under `data/raw/`, which is excluded from version control.

## Monthly Account Performance Data

No public Australian lender account-level dataset with the necessary repayment and delinquency fields is represented as real customer data here. The project therefore generates a deterministic synthetic portfolio with Australian product/state labels and joins it to the public macroeconomic series.

Synthetic fields include origination month, product, state, balance, interest rate, monthly repayments, delinquency status, days past due, default, write-off, recovery, PD, LGD, EAD, and expected loss. This data supports reproducible portfolio analytics without privacy, consent, or licensing risk. It must not be interpreted as observed Australian borrower behaviour.

