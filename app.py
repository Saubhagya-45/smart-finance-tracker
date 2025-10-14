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
st.set_page_config(
    page_title="Smart Finance Tracker",
    page_icon="💰",
    layout="wide"
)
st.title("💸 Smart Finance Tracker")
st.caption("Track your income, expenses, and savings in one place — effortlessly!")

# --- Add Transaction Form ---
st.subheader("➕ Add New Transaction")
with st.form("add_transaction_form"):
    txn_type = st.selectbox("Select Transaction Type", ["Credit 💰", "Expense 💸"])

    if "Credit" in txn_type:
        category = st.selectbox("Select Credit Category", ["Salary", "Credit"])
        icon = "💰"
        color = "green"
        txn_type_clean = "Credit"
    else:
        category = st.selectbox(
            "Select Expense Category",
            ["Food", "Rent", "Travel", "Entertainment", "Shopping", "Bills", "Other"]
        )
        icon = "💸"
        color = "red"
        txn_type_clean = "Expense"

    amount = st.number_input("Enter Amount (₹)", min_value=0.0, step=100.0)
    note = st.text_input("Note (optional)")

    submitted = st.form_submit_button("Add Transaction")
    if submitted:
        if amount <= 0:
            st.warning("Please enter a valid amount.")
        else:
            new_txn = Transaction(
                type=txn_type_clean,
                category=category,
                amount=amount,
                note=note
            )
            session.add(new_txn)
            session.commit()
            st.success(f"{icon} {txn_type_clean} of ₹{amount:.2f} added under '{category}'!")

# --- Reset Form Button ---
if st.button("🧹 Reset Form"):
    st.session_state.clear()
    st.success("Form cleared!")

# --- Reset All Transactions ---
st.subheader("⚠️ Reset All Transactions")
confirm_reset = st.checkbox("I want to delete ALL transactions")
if confirm_reset:
    if st.button("Reset All Transactions"):
        session.query(Transaction).delete()
        session.commit()
        st.success("All transactions have been cleared!")
        df = pd.DataFrame(columns=["Type", "Category", "Amount", "Date"])
    else:
        df = pd.read_sql("SELECT * FROM transactions", engine)
else:
    df = pd.read_sql("SELECT * FROM transactions", engine)

# --- Sidebar Filters ---
st.sidebar.header("🔍 Filters")
filter_type = st.sidebar.selectbox("Type", ["All", "Credit", "Expense"])
filter_category = st.sidebar.selectbox(
    "Category", ["All"] + list(df["Category"].unique()) if not df.empty else ["All"]
)
filter_month = st.sidebar.selectbox(
    "Month", ["All"] + [datetime.strptime(str(d), "%Y-%m-%d %H:%M:%S").strftime("%B") for d in df["Date"]] if not df.empty else ["All"]
)

# --- Apply Filters ---
if not df.empty:
    df["Month"] = df["Date"].apply(lambda x: datetime.strptime(str(x), "%Y-%m-%d %H:%M:%S").strftime("%B"))
    if filter_type != "All":
        df = df[df["Type"] == filter_type]
    if filter_category != "All":
        df = df[df["Category"] == filter_category]
    if filter_month != "All":
        df = df[df["Month"] == filter_month]

# --- Summary Section ---
if not df.empty:
    total_credit = df[df["Type"] == "Credit"]["Amount"].sum()
    total_expense = df[df["Type"] == "Expense"]["Amount"].sum()
    savings = total_credit - total_expense

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Total Credit", f"₹{total_credit:,.2f}", delta_color="off")
    col2.metric("💸 Total Expense", f"₹{total_expense:,.2f}", delta_color="off")
    col3.metric("💼 Net Savings", f"₹{savings:,.2f}", delta_color="off")

    st.divider()

    # --- Transaction Table ---
    st.subheader("📋 Transactions")
    st.dataframe(df[["Type", "Category", "Amount", "Date", "Note"]])

    # --- Charts ---
    col1, col2 = st.columns(2)

    with col1:
        exp_df = df[df["Type"] == "Expense"]
        if not exp_df.empty:
            fig = px.pie(exp_df, names="Category", values="Amount", title="Expense Breakdown by Category")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        monthly_df = df.copy()
        monthly_df["Month"] = monthly_df["Date"].apply(lambda x: datetime.strptime(str(x), "%Y-%m-%d %H:%M:%S").strftime("%b"))
        if not monthly_df.empty:
            fig2 = px.bar(
                monthly_df,
                x="Month",
                y="Amount",
                color="Type",
                barmode="group",
                title="Monthly Credit vs Expense"
            )
            st.plotly_chart(fig2, use_container_width=True)

    # --- Savings Trend ---
    df_sorted = df.sort_values("Date")
    df_sorted["Savings"] = df_sorted.apply(
        lambda row: row["Amount"] if row["Type"] == "Credit" else -row["Amount"], axis=1
    ).cumsum()

    st.subheader("📈 Savings Over Time")
    fig3 = px.line(df_sorted, x="Date", y="Savings", title="Cumulative Savings Trend")
    st.plotly_chart(fig3, use_container_width=True)

else:
    st.info("No transactions yet. Start by adding a Credit or Expense above!")
