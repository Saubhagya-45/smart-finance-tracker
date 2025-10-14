import streamlit as st
import pandas as pd
import plotly.express as px
from database import add_transaction, get_all_transactions

st.set_page_config(page_title="Smart Finance Tracker", layout="wide")
st.title("💰 Smart Finance Tracker")

# --- Add Transaction Form ---
st.subheader("Add Transaction")
with st.form(key='txn_form'):
    txn_type = st.selectbox("Type", ["Income", "Expense"])
    category = st.text_input("Category")
    amount = st.number_input("Amount", min_value=0.0, step=0.01)
    note = st.text_input("Note (optional)")
    submit = st.form_submit_button("Add Transaction")
    
    if submit:
        add_transaction(txn_type, category, amount, note)
        st.success("Transaction added!")

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

# --- Display Transactions ---
st.subheader("All Transactions")
st.dataframe(df)

# --- Charts ---
st.subheader("Expenses by Category")
expense_df = df[df["Type"]=="Expense"]
if not expense_df.empty:
    fig1 = px.pie(expense_df, values="Amount", names="Category")
    st.plotly_chart(fig1, use_container_width=True)

st.subheader("Monthly Summary")
if not df.empty:
    df["Month"] = pd.to_datetime(df["Date"]).dt.to_period("M")
    monthly = df.groupby(["Month","Type"])["Amount"].sum().reset_index()
    fig2 = px.bar(monthly, x="Month", y="Amount", color="Type", barmode="group")
    st.plotly_chart(fig2, use_container_width=True)
