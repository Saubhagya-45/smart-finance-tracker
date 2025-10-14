import streamlit as st
import pandas as pd
import plotly.express as px
from database import add_transaction, get_all_transactions

st.set_page_config(page_title="Smart Finance Tracker", layout="wide")
st.title("💰 Smart Finance Tracker")

# --- Predefined Categories ---
credit_categories = ["Salary", "Credit"]  # Added one more category
expense_categories = ["Food", "Rent", "Travel", "Entertainment", "Shopping", "Bills", "Other"]

# --- Add Transaction Form ---
st.subheader("Add Transaction")
with st.form(key='txn_form'):
    txn_type = st.selectbox("Type", ["Credit", "Expense"])
    
    # Separate dropdowns for Credit and Expense
    if txn_type == "Credit":
        category = st.selectbox("Credit Category", credit_categories)
    else:
        category = st.selectbox("Expense Category", expense_categories)
    
    amount = st.number_input("Amount", min_value=0.0, step=0.01)
    note = st.text_input("Note (optional)")
    submit = st.form_submit_button("Add Transaction")
    
    if submit:
        add_transaction(txn_type, category, amount, note)
        st.success(f"{txn_type} transaction added!")

# --- Load Data ---
data = get_all_transactions()
if data:
    df = pd.DataFrame([{
        "Type": t.type,
        "Category": t.category,
        "Amount": t.amount,
        "Date": t.date,
        "Note": t.note
    } for t in data])
else:
    df = pd.DataFrame(columns=["Type","Category","Amount","Date","Note"])

# --- Summary Cards ---
total_credit = df[df["Type"]=="Credit"]["Amount"].sum()
total_expense = df[df["Type"]=="Expense"]["Amount"].sum()
savings = total_credit - total_expense

st.subheader("💡 Summary")
col1, col2, col3 = st.columns(3)
col1.metric("Total Credit", f"₹ {total_credit:,.2f}")
col2.metric("Total Expense", f"₹ {total_expense:,.2f}")
col3.metric("Savings", f"₹ {savings:,.2f}")

# --- Display Transactions ---
st.subheader("All Transactions")
st.dataframe(df)

# --- Charts ---
st.subheader("Expenses by Category")
expense_df = df[df["Type"]=="Expense"]
if not expense_df.empty:
    fig1 = px.pie(expense_df, values="Amount", names="Category", title="Expenses by Category")
    st.plotly_chart(fig1, use_container_width=True)

st.subheader("Monthly Summary")
if not df.empty:
    # FIX: Convert Period to string for Plotly
    df["Month"] = pd.to_datetime(df["Date"]).dt.to_period("M").astype(str)
    monthly = df.groupby(["Month","Type"])["Amount"].sum().reset_index()
    fig2 = px.bar(monthly, x="Month", y="Amount", color="Type", barmode="group", title="Monthly Credit vs Expense")
    st.plotly_chart(fig2, use_container_width=True)
