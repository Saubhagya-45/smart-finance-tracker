import streamlit as st
import pandas as pd
import plotly.express as px
from database import add_transaction, get_all_transactions, session, Transaction

st.set_page_config(page_title="Smart Finance Tracker", layout="wide")
st.title("💰 Smart Finance Tracker")

# --- Predefined Categories ---
credit_categories = ["Salary", "Credit"]
expense_categories = ["Food", "Rent", "Travel", "Entertainment", "Shopping", "Bills", "Other"]

# --- Sidebar Filters ---
st.sidebar.subheader("Filter Transactions")
filter_type = st.sidebar.selectbox("Type", ["All", "Credit", "Expense"])
filter_category = st.sidebar.selectbox("Category", ["All"] + credit_categories + expense_categories)

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
    months = ["All"] + sorted(df["Month"].unique().tolist())
    filter_month = st.sidebar.selectbox("Month", months)
else:
    filter_month = "All"

# --- Apply Filters ---
filtered_df = df.copy()
if filter_type != "All":
    filtered_df = filtered_df[filtered_df["Type"] == filter_type]
if filter_category != "All":
    filtered_df = filtered_df[filtered_df["Category"] == filter_category]
if filter_month != "All":
    filtered_df = filtered_df[filtered_df["Month"] == filter_month]

# --- Initialize session state for form fields ---
if "txn_type" not in st.session_state:
    st.session_state.txn_type = "Credit"
if "category" not in st.session_state:
    st.session_state.category = credit_categories[0]
if "amount" not in st.session_state:
    st.session_state.amount = 0.0
if "note" not in st.session_state:
    st.session_state.note = ""

# --- Add Transaction Form ---
st.subheader("Add Transaction")
with st.form(key="txn_form"):
    st.session_state.txn_type = st.selectbox(
        "Type", ["Credit", "Expense"], index=["Credit","Expense"].index(st.session_state.txn_type)
    )
    
    if st.session_state.txn_type == "Credit":
        st.session_state.category = st.selectbox(
            "Credit Category", credit_categories, index=credit_categories.index(st.session_state.category) if st.session_state.category in credit_categories else 0
        )
    else:
        st.session_state.category = st.selectbox(
            "Expense Category", expense_categories, index=expense_categories.index(st.session_state.category) if st.session_state.category in expense_categories else 0
        )
    
    st.session_state.amount = st.number_input("Amount", min_value=0.0, step=0.01, value=st.session_state.amount)
    st.session_state.note = st.text_input("Note (optional)", value=st.session_state.note)
    
    submitted = st.form_submit_button("Add Transaction")
    reset = st.form_submit_button("Reset Form")

    if submitted:
        add_transaction(
            st.session_state.txn_type,
            st.session_state.category,
            st.session_state.amount,
            st.session_state.note
        )
        st.success(f"{st.session_state.txn_type} transaction added!")
        st.session_state.amount = 0.0
        st.session_state.note = ""
    if reset:
        st.session_state.txn_type = "Credit"
        st.session_state.category = credit_categories[0]
        st.session_state.amount = 0.0
        st.session_state.note = ""

# --- Reset All Transactions Button ---
st.subheader("⚠️ Reset All Transactions")
if st.button("Reset All Transactions"):
    if st.confirm("Are you sure you want to delete ALL transactions?"):
        session.query(Transaction).delete()
        session.commit()
        st.success("All transactions have been cleared!")
        st.experimental_rerun()

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

# --- Download CSV ---
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
