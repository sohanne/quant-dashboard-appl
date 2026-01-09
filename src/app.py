import streamlit as st
from ui.portfolio_page import render_portfolio_page

def main():
    st.set_page_config(page_title="Quant Dashboard - Quant B", layout="wide")
    st.title("Quant Dashboard — Portfolio (Quant B)")

    st.sidebar.info(
        "Quant B module:\n"
        "- Multi-asset portfolio\n"
        "- Custom weights & rebalancing\n"
        "- Metrics & correlations\n"
        "- Daily reports via cron"
    )

    render_portfolio_page()

if __name__ == "__main__":
    main()
