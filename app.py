# --- Test connection ---
try:
    response = supabase.table("transactions").select("*").limit(1).execute()
    st.success("✅ Connected to Supabase successfully!")
except Exception as e:
    st.error(f"❌ Supabase connection failed: {e}")

import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client
import uuid

# ----------------------------
# SUPABASE SETUP
# ----------------------------
SUPABASE_URL = "https://nhwrefxpvbgftyxyxgpb.supabase.co"  # Replace with your Supabase URL
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5od3JlZnhwdmJnZnR5eHl4Z3BiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjAzNTg2MDEsImV4cCI6MjA3NTkzNDYwMX0.DJ78pIEUWeTayEK-ytS8QsbwgI08e0epAUeeDo4C9II"                   # Replace with your anon/public key

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    supabase_connected = True
except Exception:
    supabase_connected = False

# ----------------------------
# USER SESSION ID
# ----------------------------
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

# Fallback local storage if Supabase not connected
if "local_transactions" not in st.session_state:
    st.session_state.local_transactions = []

# ----------------------------
# APP SETUP
# ----------------------------
st.set_page_config(page_title="Smart Finance Tracker", page_icon="💰", layout="centered")
st.title("💼 Smart Finance Tracker")
st.caption("Track your income, expenses, and manage your finances privately.")

# ----------------------------
# ADD TRANSACTION FORM
# ----------------------------
st.subheader("➕ Add New Transaction")

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
        transaction = {
            "user_id": st.session_state.user_id,
            "type": txn_type,
            "category": category,
            "amount": amount,
            "note": note
        }

        if supabase_connected:
            try:
                supabase.table("transactions").insert(transaction).execute()
            except Exception:
                supabase_connected = False
                st.warning("Supabase connection failed. Saving locally instead.")
                st.session_state.local_transactions.append(transaction)
        else:
            st.session_state.local_transactions.append(transaction)

        st.success(f"{'💰' if txn_type == 'Credit' else '💸'} {txn_type} of ₹{amount:.2f} added under '{category}'!")
        st.rerun()

# ----------------------------
# FETCH TRANSACTIONS
# ----------------------------
st.subheader("📊 Your Transaction History")

transactions = []
if supabase_connected:
    try:
        response = supabase.table("transactions").select("*").eq("user_id", st.session_state.user_id).execute()
        transactions = response.data
    except Exception:
        supabase_connected = False
        st.warning("Supabase connection failed. Showing local session data.")
        transactions = st.session_state.local_transactions
else:
    transactions = st.session_state.local_transactions

if transactions:
    df = pd.DataFrame(transactions)

    # Summary metrics
    total_credit = df[df["type"] == "Credit"]["amount"].sum()
    total_expense = df[df["type"] == "Expense"]["amount"].sum()
    balance = total_credit - total_expense

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Total Credit", f"₹{total_credit:,.2f}")
    col2.metric("💸 Total Expense", f"₹{total_expense:,.2f}")
    col3.metric("🧾 Balance", f"₹{balance:,.2f}")

    # Filter by category
    selected_category = st.selectbox(
        "Filter by Category",
        ["All"] + sorted(df["category"].unique().tolist())
    )
    if selected_category != "All":
        df = df[df["category"] == selected_category]

    # Color only text based on type
    def color_text(row):
        return ['color: green' if row['type']=="Credit" else 'color: red' for _ in row]

    st.dataframe(
        df[["type", "category", "amount", "note"]].style.apply(color_text, axis=1),
        use_container_width=True
    )

    # Charts
    fig1 = px.bar(df, x="category", y="amount", color="type", barmode="group", title="Category-wise Breakdown")
    st.plotly_chart(fig1, use_container_width=True)

    fig2 = px.pie(df, names="type", values="amount", title="Income vs Expense", color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig2, use_container_width=True)

else:
    st.info("No transactions added yet.")

# ----------------------------
# RESET ALL TRANSACTIONS
# ----------------------------
st.subheader("⚠️ Reset All Your Transactions")
confirm_reset = st.checkbox("I want to delete ALL my transactions")

if confirm_reset:
    if st.button("Reset All Transactions"):
        if supabase_connected:
            try:
                supabase.table("transactions").delete().eq("user_id", st.session_state.user_id).execute()
            except Exception:
                st.warning("Supabase reset failed. Clearing local data instead.")
                st.session_state.local_transactions = []
        else:
            st.session_state.local_transactions = []
        st.success("All your transactions cleared successfully!")
        st.rerun()
