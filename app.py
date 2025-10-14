import streamlit as st
import pandas as pd
import plotly.express as px
from database import add_transaction, get_all_transactions, session, Transaction

st.set_page_config(page_title="Smart Finance Tracker", layout="wide")
st.title("💰 Smart Finance Tracker")

# --- Predefined Categories ---
credit_categories = ["Salary", "Credit"]
expense_categories = ["Food", "Rent", "Travel", "Entertainment", "Shopping", "Bills", "Other"]

# --- Sidebar Options ---
st.sidebar.subheader("Options")

# Clear all transactions
if st.sidebar.button("Clear All Transactions"):
    session.query(Transaction).delete()
    session.commit()
    st.sidebar.success("All transactions cleared!")

# --- Sidebar Filters ---
st.sidebar.subheader("Filter Transactions")
filter_type = st.sidebar.selectbox("Type", ["All", "Credit", "Expense"])
filter_category = st.sidebar.selectbox("Category", ["All"] + credit_categories + expense_categories)
filter_month = st.sidebar.selectbox("Month", ["All"])

# --- Add Transaction Form ---
st.subheader("Add Transaction")
with st.form(key='txn_form'):
    txn_type = st.selectbox("Type", ["Credit", "Expense"])
    if txn_type == "Credit":
        category = st.selectbox("Credit Category", credit_categories)
    else:
        category = st.selectbox("Expense Category", expense_categories)
    
    amount = st.number_input("Amount", min_value=0.0, step=0.01)
    note = st.text_input("Note (optional)")
    
    col1, col2 = st.columns(2)
    with col1:
        submit = st.form_submit_button("Add Transaction")
    with col2:
        reset = st.form_submit_button("Clear Form")
    
    if submit:
        add_transaction(txn_type, category, amount, note)
        st.success(f"{txn_type} transaction added!")
    if reset:
        st.experimental_rerun()  # Clears the form inputs

# --- Load Data ---
data = get_all_transactions()
if data:
    df = pd.DataFrame([{
        "Type": t.type,
        "Category": t.category,
        "Amount": t.amount,
        "Date": pd.to_datetime(t.date)
    } for t in data])
else:
    df = pd.DataFrame(columns=["Type","Category","Amount","Date"])

# Add Month column for filtering
if not df.empty:
    df["Month"] = df["Date"].dt.to_period("M").astype(str)
    # Update month filter options dynamically
    months = ["All"] + sorted(df["Month"].unique().tolist())
    filter_month = st.sidebar.selectbox("Month", months)

# --- Apply Filters ---
filtered_df = df.copy()
if filter_type != "All":
    filtered_df = filtered_df[filtered_df["Type"] == filter_type]
if filter_category != "All":
    filtered_df = filtered_df[filtered_df["Category"] == filter_category]
if filter_month != "All":
    filtered_df = filtered_df[filtered_df["Month"] == filter_month]

# --- Summary Cards ---
total_credit = filtered_df[filtered_df["Type"]=="Credit"]["Amount"].sum()
total_expense = filtered_df[filtered_df["Type"]=="Expense"]["Amount"].sum()
savings = total_credit - total_expense

st.subheader("💡 Summary")
col1, col2, col3 = st.columns(3)
col1.metric("Total Credit", f"₹ {total_credit:,.2f}")
col2.metric("Total Expense", f"₹ {total_expense:,.2f}")
col3.metric("Savings", f"₹ {savings:,.2f}")

# --- Display Transactions ---
st.subheader("All Transactions")
st.dataframe(filtered_df)

# --- Download Button ---
if not filtered_df.empty:
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Transactions CSV",
        data=csv,
        file_name='transactions.csv',
        mime='text/csv'
    )

# --- Charts ---
st.subheader("Expenses by Category")
expense_df = filtered_df[filtered_df["Type"]=="Expense"]
if not expense_df.empty:
    fig1 = px.pie(expense_df, values="Amount", names="Category", title="Expenses by Category")
    st.plotly_chart(fig1, use_container_width=True)

st.subheader("Monthly Summary")
if not filtered_df.empty:
    monthly = filtered_df.groupby(["Month","Type"])["Amount"].sum().reset_index()
    fig2 = px.bar(monthly, x="Month", y="Amount", color="Type", barmode="group", title="Monthly Credit vs Expense")
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("Cumulative Savings Over Time")
if not filtered_df.empty:
    filtered_df = filtered_df.sort_values("Date")
    filtered_df["Credit"] = filtered_df["Amount"].where(filtered_df["Type"]=="Credit", 0)
    filtered_df["Expense"] = filtered_df["Amount"].where(filtered_df["Type"]=="Expense", 0)
    filtered_df["Cumulative Savings"] = (filtered_df["Credit"].cumsum() - filtered_df["Expense"].cumsum())
    fig3 = px.line(filtered_df, x="Date", y="Cumulative Savings", title="Cumulative Savings Over Time")
    st.plotly_chart(fig3, use_container_width=True)
