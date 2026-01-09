## Quant B — Portfolio Module

The Quant B module implements a multi-asset portfolio analysis and backtesting tool.
It allows users to build, analyze and monitor diversified portfolios using historical market data.

### Features
- Selection of at least three financial assets
- Equal-weight or custom-weight portfolio allocation
- Portfolio backtesting with periodic rebalancing (weekly, monthly, quarterly)
- Performance metrics:
  - Annualized return
  - Annualized volatility
  - Sharpe ratio
  - Maximum drawdown
  - Diversification effect
- Asset correlation matrix
- Interactive visualizations (prices, cumulative performance)
- Automated daily portfolio reports exported as CSV files

### Daily Portfolio Report
In addition to the live Streamlit dashboard, the Quant B module includes an automated daily portfolio reporting tool.
Dashboard : https://quant-dashboard-appl-portfolio.streamlit.app/
The report can also be generated from the command line:
```bash
python -m src.portfolio.daily_report 
```
 The report is saved in the reports/ directory and includes key portfolio performance metrics.
### Data Source
Market data is retrieved using Yahoo Finance via the yfinance Python library.

### Academic Context
This module was developed independently as part of the Quant B assignment and later integrated into a single Streamlit dashboard with the Quant A module, as required by the course.













