import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import plotly.express as px
import uuid

# -----------------------------
# PAGE CONFIG (MUST BE FIRST)
# -----------------------------
st.set_page_config(page_title="Smart Finance Tracker", layout="wide")

# -----------------------------
# SUPABASE CONFIG (SECURE)
# -----------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------------
# APP TITLE
# -----------------------------
st.title("💰 Smart Finance Tracker")

# -----------------------------
# TEST CONNECTION
# -----------------------------
try:
    supabase.table("transactions").select("*").limit(1).execute()
    st.success("✅ Connected to Supabase successfully!")
except Exception as e:
    st.error(f"❌ Supabase connection failed: {e}")

# -----------------------------
# SESSION USER ID
# -----------------------------
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

# -----------------------------
# TRANSACTION FORM
# -----------------------------
st.subheader("➕ Add Transaction")

transaction_type = st.radio(
    "Transaction Type",
    ["Credit", "Expense"],
    horizontal=True
)

if transaction_type == "Credit":
    category = st.selectbox(
        "Category",
        ["Salary", "Bonus", "Other Income"]
    )
else:
    category = st.selectbox(
        "Category",
        ["Food", "Transport", "Bills", "Shopping", "Entertainment", "Other"]
    )

amount = st.number_input("Amount (₹)", min_value=0.0, format="%.2f")
note = st.text_input("Note (optional)")

col1, col2 = st.columns(2)
add_btn = col1.button("💾 Add Transaction", use_container_width=True)
reset_btn = col2.button("🗑️ Reset All Transactions", use_container_width=True)

# -----------------------------
# ADD TRANSACTION
# -----------------------------
if add_btn:
    if amount > 0:
        try:
            data = {
                "user_id": st.session_state.user_id,
                "type": transaction_type,
                "category": category,
                "amount": amount,
                "note": note,
                "created_at": datetime.utcnow().isoformat()
            }
            supabase.table("transactions").insert(data).execute()
            st.success("✅ Transaction added!")
        except Exception as e:
            st.error(f"Error adding transaction: {e}")
    else:
        st.warning("⚠️ Amount must be greater than 0")

# -----------------------------
# RESET TRANSACTIONS
# -----------------------------
if reset_btn:
    try:
        supabase.table("transactions") \
            .delete() \
            .eq("user_id", st.session_state.user_id) \
            .execute()
        st.warning("🧹 All transactions deleted!")
    except Exception as e:
        st.error(f"Error deleting transactions: {e}")

# -----------------------------
# LOAD TRANSACTIONS
# -----------------------------
try:
    response = (
        supabase.table("transactions")
        .select("*")
        .eq("user_id", st.session_state.user_id)
        .order("created_at", desc=True)
        .execute()
    )
    transactions = response.data or []
except Exception as e:
    st.error(f"Error fetching transactions: {e}")
    transactions = []

# -----------------------------
# SUMMARY
# -----------------------------
if transactions:

    credit_sum = sum(t["amount"] for t in transactions if t["type"] == "Credit")
    expense_sum = sum(t["amount"] for t in transactions if t["type"] == "Expense")
    balance = credit_sum - expense_sum

    st.subheader("💰 Balance Summary")
    c1, c2, c3 = st.columns(3)
    c1.metric("💵 Total Credit", f"₹{credit_sum:.2f}")
    c2.metric("💸 Total Expense", f"₹{expense_sum:.2f}")
    c3.metric("🧾 Current Balance", f"₹{balance:.2f}")

    # -----------------------------
    # TABLE
    # -----------------------------
    df = pd.DataFrame(transactions)
    df["created_at"] = pd.to_datetime(df["created_at"]).dt.strftime(
        "%d %b %Y, %I:%M %p"
    )

    st.subheader("📊 Transaction History")
    st.dataframe(
        df[["type", "category", "amount", "note", "created_at"]],
        use_container_width=True
    )

    # -----------------------------
    # PIE CHART
    # -----------------------------
    pie_data = pd.DataFrame({
        "Type": ["Credit", "Expense"],
        "Amount": [credit_sum, expense_sum]
    })

    fig_pie = px.pie(
        pie_data,
        names="Type",
        values="Amount",
        title="📊 Credit vs Expense"
    )

    st.plotly_chart(fig_pie, use_container_width=True)

    # -----------------------------
    # BAR CHART
    # -----------------------------
    df_plot = pd.DataFrame(transactions)
    df_plot["created_at"] = pd.to_datetime(df_plot["created_at"])

    fig_bar = px.bar(
        df_plot,
        x="created_at",
        y="amount",
        color="type",
        title="💹 Transactions Over Time"
    )

    st.plotly_chart(fig_bar, use_container_width=True)

else:
    st.info("No transactions yet. Add one to get started!")
