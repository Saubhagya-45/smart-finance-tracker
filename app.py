import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# --- Database Setup ---
engine = create_engine("sqlite:///finance.db")
Base = declarative_base()

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    type = Column(String)
    category = Column(String)
    amount = Column(Float)
    note = Column(String)
    date = Column(DateTime, default=datetime.now)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# --- Streamlit Config ---
st.set_page_config(page_title="Smart Finance Tracker", page_icon="💰", layout="wide")
st.title("💸 Smart Finance Tracker")
st.caption("Track your income, expenses, and savings effortlessly!")

# --- Helper Function to Load Data ---
def load_data():
    try:
        df = pd.read_sql("SELECT * FROM transactions", engine)
    except Exception:
        df = pd.DataFrame(columns=["type", "category", "amount", "date", "note"])
    if df.empty:
        df = pd.DataFrame(columns=["type", "category", "amount", "date", "note"])
    return df

# --- Add Transaction Form ---
st.subheader("➕ Add New Transaction")
with st.form("add_transaction_form"):
    txn_type = st.radio("Select Transaction Type", ["Credit 💰", "Expense 💸"], horizontal=True)

    if "Credit" in txn_type:
        category = st.selectbox("Select Credit Category", ["Salary", "Credit"])
        icon = "💰"
        txn_type_clean = "Credit"
    else:
        category = st.selectbox(
            "Select Expense Category",
            ["Food", "Rent", "Travel", "Entertainment", "Shopping", "Bills", "Other"]
        )
        icon = "💸"
        txn_type_clean = "Expense"

    amount = st.number_input("Enter Amount (₹)", min_value=0.0, step=100.0)
    note = st.text_input("Note (optional)")

    submitted = st.form_submit_button("Add Transaction")
    if submitted:
        if amount <= 0:
            st.warning("Please enter a valid amount.")
        else:
            new_txn = Transaction(type=txn_type_clean, category=category, amount=amount, note=note)
            session.add(new_txn)
            session.commit()
            st.success(f"{icon} {txn_type_clean} of ₹{amount:.2f} added under '{category}'!")

# --- Reset Form Button ---
if st.button("🧹 Reset Form"):
    st.session_state.clear()
    st.success("Form cleared!")

# --- Load Transactions ---
df = load_data()

# --- Reset All Transactions ---
st.subheader("⚠️ Reset All Transactions")
confirm_reset = st.checkbox("I want to delete ALL transactions")
if confirm_reset and st.button("Reset All Transactions"):
    session.query(Transaction).delete()
    session.commit()
    st.success("All transactions have been cleared!")
    df = load_data()

# --- Sidebar Filters ---
st.sidebar.header("🔍 Filters")
if not df.empty:
    df["month"] = pd.to_datetime(df["date"]).dt.strftime("%B")

filter_type = st.sidebar.selectbox("Type", ["All", "Credit", "Expense"])
filter_category = st.sidebar.selectbox("Category", ["All"] + (list(df["category"].unique()) if not df.empty else []))
filter_month = st.sidebar.selectbox("Month", ["All"] + (list(df["month"].unique()) if not df.empty else []))

# --- Apply Filters ---
if not df.empty:
    filtered_df = df.copy()
    if filter_type != "All":
        filtered_df = filtered_df[filtered_df["type"] == filter_type]
    if filter_category != "All":
        filtered_df = filtered_df[filtered_df["category"] == filter_category]
    if filter_month != "All":
        filtered_df = filtered_df[filtered_df["month"] == filter_month]
else:
    filtered_df = df.copy()

# --- Summary Section ---
if not filtered_df.empty:
    total_credit = filtered_df[filtered_df["type"] == "Credit"]["amount"].sum()
    total_expense = filtered_df[filtered_df["type"] == "Expense"]["amount"].sum()
    savings = total_credit - total_expense

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Total Credit", f"₹{total_credit:,.2f}")
    col2.metric("💸 Total Expense", f"₹{total_expense:,.2f}")
    col3.metric("💼 Net Savings", f"₹{savings:,.2f}")

    st.divider()

    # --- Transaction Table ---
    st.subheader("📋 Transactions")
    st.dataframe(
        filtered_df[["type", "category", "amount", "date", "note"]]
        .rename(columns={"type": "Type", "category": "Category", "amount": "Amount (₹)", "date": "Date", "note": "Note"})
        .sort_values("Date", ascending=False)
    )

    # --- Charts ---
    col1, col2 = st.columns(2)
    with col1:
        exp_df = filtered_df[filtered_df["type"] == "Expense"]
        if not exp_df.empty:
            fig = px.pie(exp_df, names="category", values="amount", title="Expense Breakdown by Category")
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        if not filtered_df.empty:
            monthly_df = filtered_df.copy()
            monthly_df["month"] = pd.to_datetime(monthly_df["date"]).dt.strftime("%b")
            fig2 = px.bar(
                monthly_df,
                x="month",
                y="amount",
                color="type",
                barmode="group",
                title="Monthly Credit vs Expense"
            )
            st.plotly_chart(fig2, use_container_width=True)

    # --- Savings Trend ---
    df_sorted = filtered_df.sort_values("date")
    df_sorted["savings"] = df_sorted.apply(
        lambda row: row["amount"] if row["type"] == "Credit" else -row["amount"], axis=1
    ).cumsum()

    st.subheader("📈 Savings Over Time")
    fig3 = px.line(df_sorted, x="date", y="savings", title="Cumulative Savings Trend")
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.info("No transactions yet. Start by adding a Credit or Expense above!")
