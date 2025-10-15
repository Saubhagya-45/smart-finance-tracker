import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import plotly.express as px
import uuid  # for unique session IDs

# --- Supabase Configuration ---
SUPABASE_URL = "https://nhwrefxpvbgftyxyxgpb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5od3JlZnhwdmJnZnR5eHl4Z3BiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjAzNTg2MDEsImV4cCI6MjA3NTkzNDYwMX0.DJ78pIEUWeTayEK-ytS8QsbwgI08e0epAUeeDo4C9II"

# Create Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Test connection
try:
    supabase.table("transactions").select("*").limit(1).execute()
    st.success("✅ Connected to Supabase successfully!")
except Exception as e:
    st.error(f"❌ Supabase connection failed: {e}")

# --- Streamlit App ---
st.set_page_config(page_title="Smart Finance Tracker", layout="wide")
st.title("💰 Smart Finance Tracker")

# --- Session-based User ID ---
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())  # unique ID for each session

# --- Transaction Form ---
st.subheader("➕ Add Transaction")
transaction_type = st.radio("Transaction Type", ["Credit", "Expense"], horizontal=True)

if transaction_type == "Credit":
    category = st.selectbox("Category", ["Salary", "Bonus", "Other Income"])
else:
    category = st.selectbox("Category", ["Food", "Transport", "Bills", "Shopping", "Entertainment", "Other"])

amount = st.number_input("Amount (₹)", min_value=0.0, format="%.2f")
note = st.text_input("Note (optional)")

col1, col2 = st.columns(2)
with col1:
    add_btn = st.button("💾 Add Transaction", use_container_width=True)
with col2:
    reset_btn = st.button("🗑️ Reset All Transactions", use_container_width=True)

# --- Add Transaction ---
if add_btn:
    if amount > 0:
        try:
            data = {
                "user_id": st.session_state.user_id,
                "type": transaction_type,
                "category": category,
                "amount": amount,
                "note": note,
                "created_at": datetime.now().isoformat()
            }
            supabase.table("transactions").insert(data).execute()
            st.success("✅ Transaction added successfully!")
        except Exception as e:
            st.error(f"Error adding transaction: {e}")
    else:
        st.warning("⚠️ Please enter an amount greater than 0.")

# --- Reset Transactions ---
if reset_btn:
    try:
        supabase.table("transactions").delete().eq("user_id", st.session_state.user_id).execute()
        st.warning("🧹 All transactions deleted!")
    except Exception as e:
        st.error(f"Error deleting transactions: {e}")

# --- Load Transactions ---
try:
    response = supabase.table("transactions") \
        .select("*") \
        .eq("user_id", st.session_state.user_id) \
        .order("created_at", desc=True) \
        .execute()
    transactions = response.data if response.data else []
except Exception as e:
    st.error(f"Error fetching transactions: {e}")
    transactions = []

# --- Balance Summary ---
if transactions:
    credit_sum = sum([t["amount"] for t in transactions if t["type"] == "Credit"])
    expense_sum = sum([t["amount"] for t in transactions if t["type"] == "Expense"])
    balance = credit_sum - expense_sum

    st.subheader("💰 Balance Summary")
    col1, col2, col3 = st.columns(3)
    col1.metric("💵 Total Credit", f"₹{credit_sum:.2f}")
    col2.metric("💸 Total Expense", f"₹{expense_sum:.2f}")
    col3.metric("🧾 Current Balance", f"₹{balance:.2f}")

# --- Transaction History Table ---
if transactions:
    df = pd.DataFrame(transactions)
    df["created_at"] = pd.to_datetime(df["created_at"]).dt.strftime("%d %b %Y, %I:%M %p")

    # Add styled Amount column
    df["Amount"] = df.apply(
        lambda row: f"₹{row['amount']:.2f}",
        axis=1
    )
    # Select columns and rename
    df_display = df[["type","category","Amount","note","created_at"]]
    df_display.columns = ["Type", "Category", "Amount", "Note", "Date"]

    # Color Amount based on type
    def highlight_amount(val, t):
        color = "green" if t=="Credit" else "red"
        return f"color: {color}"

    styled_df = df_display.style.apply(
        lambda x: [f"color: {'green' if x['Type']=='Credit' else 'red'}" if col=="Amount" else "" for col in x.index],
        axis=1
    )

    st.subheader("📊 Transaction History")
    st.dataframe(styled_df, use_container_width=True)

    # --- Pie Chart ---
    pie_data = pd.DataFrame({
        "Type": ["Credit", "Expense"],
        "Amount": [credit_sum, expense_sum]
    })
    fig_pie = px.pie(
        pie_data,
        names="Type",
        values="Amount",
        color="Type",
        color_discrete_map={"Credit":"green","Expense":"red"},
        title="📊 Credit vs Expense"
    )
    st.plotly_chart(fig_pie, use_container_width=True)

    # --- Transactions Over Time Graph ---
    df_plot = pd.DataFrame(transactions)
    df_plot['created_at'] = pd.to_datetime(df_plot['created_at'])
    fig_bar = px.bar(
        df_plot,
        x='created_at',
        y='amount',
        color='type',
        labels={'created_at':'Date','amount':'Amount','type':'Transaction Type'},
        title='💹 Transactions Over Time'
    )
    st.plotly_chart(fig_bar, use_container_width=True)

else:
    st.info("No transactions yet. Add one to get started!")
