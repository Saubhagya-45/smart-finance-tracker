import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker

# ----------------------------
# DATABASE SETUP
# ----------------------------
Base = declarative_base()

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    type = Column(String)
    category = Column(String)
    amount = Column(Float)
    note = Column(String)

engine = create_engine("sqlite:///finance_tracker.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

st.set_page_config(page_title="Smart Finance Tracker", page_icon="💰", layout="centered")
st.title("💼 Smart Finance Tracker")
st.caption("Track your income, expenses, and manage your finances effortlessly.")

# ----------------------------
# ADD TRANSACTION FORM
# ----------------------------
st.subheader("➕ Add New Transaction")

# Predefined categories
credit_categories = [
    "Salary", "Freelance Income", "Investment Return",
    "Gift Received", "Cashback / Refund", "Other Credit"
]
expense_categories = [
    "Food & Dining", "Rent / Accommodation", "Travel / Commute",
    "Entertainment / Subscriptions", "Shopping", "Bills & Utilities",
    "Health / Fitness", "Education", "Other Expense"
]

txn_type = st.radio("Select Transaction Type", ["Credit", "Expense"], horizontal=True)

# Show dropdown dynamically
if txn_type == "Credit":
    category = st.selectbox("Select Credit Category", credit_categories)
else:
    category = st.selectbox("Select Expense Category", expense_categories)

amount = st.number_input("Enter Amount (₹)", min_value=0.0, step=100.0)
note = st.text_input("Note (optional)")

if st.button("Add Transaction"):
    if amount <= 0:
        st.warning("Please enter a valid amount.")
    else:
        new_txn = Transaction(
            type=txn_type,
            category=category,
            amount=amount,
            note=note
        )
        session.add(new_txn)
        session.commit()
        st.success(f"{'💰' if txn_type == 'Credit' else '💸'} {txn_type} of ₹{amount:.2f} added under '{category}'!")
        st.rerun()

# ----------------------------
# DISPLAY TRANSACTIONS
# ----------------------------
st.subheader("📊 Transaction History")
transactions = session.query(Transaction).all()

if transactions:
    df = pd.DataFrame(
        [(t.id, t.type, t.category, t.amount, t.note) for t in transactions],
        columns=["ID", "Type", "Category", "Amount", "Note"]
    )

    # Summary metrics
    total_credit = df[df["Type"] == "Credit"]["Amount"].sum()
    total_expense = df[df["Type"] == "Expense"]["Amount"].sum()
    balance = total_credit - total_expense

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Total Credit", f"₹{total_credit:,.2f}")
    col2.metric("💸 Total Expense", f"₹{total_expense:,.2f}")
    col3.metric("🧾 Balance", f"₹{balance:,.2f}")

    # Filter by category
    selected_category = st.selectbox(
        "Filter by Category",
        ["All"] + sorted(df["Category"].unique().tolist())
    )
    if selected_category != "All":
        df = df[df["Category"] == selected_category]

    st.dataframe(df[["Type", "Category", "Amount", "Note"]], use_container_width=True)

    # Charts
    fig1 = px.bar(df, x="Category", y="Amount", color="Type", barmode="group", title="Category-wise Breakdown")
    st.plotly_chart(fig1, use_container_width=True)

    fig2 = px.pie(df, names="Type", values="Amount", title="Income vs Expense", color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("No transactions added yet.")

# ----------------------------
# RESET ALL TRANSACTIONS
# ----------------------------
st.subheader("⚠️ Reset All Transactions")
confirm_reset = st.checkbox("I want to delete ALL transactions")
if confirm_reset:
    if st.button("Reset All Transactions"):
        session.query(Transaction).delete()
        session.commit()
        st.success("All transactions cleared successfully!")
        st.rerun()
