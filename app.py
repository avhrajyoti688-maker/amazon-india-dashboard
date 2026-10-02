"""
Amazon India Management Dashboard  |  Sapphire IQ
Run with:  streamlit run app.py
Requires:  pip install streamlit pandas plotly openpyxl
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# --------------------------------------------------------------------------
# 0. PAGE SETUP & STYLE
# --------------------------------------------------------------------------
st.set_page_config(page_title="Amazon India Dashboard", page_icon="📊", layout="wide")

DATA_FILE = "Amazon_Sales_Data_India.xlsx"   # keep next to app.py
SALES_COLOR, PROFIT_COLOR = "#1A3CFF", "#00B386"
STATUS_COLORS = {"Delivered": "#00B386", "Shipped": "#1A3CFF",
                 "Returned": "#F5A623", "Cancelled": "#E5484D"}

st.markdown(
    """
    <style>
      .block-container {padding-top: 1.5rem;}
      div[data-testid="stMetric"] {background:#F5F7FF; border:1px solid #DDE3FF;
                                   border-radius:12px; padding:12px 16px;}
      .section-bar {background:#1A3CFF; color:white; padding:10px 18px;
                    border-radius:12px; font-size:1.25rem; font-weight:700;
                    margin:1.5rem 0 0.8rem 0;}
    </style>
    """,
    unsafe_allow_html=True,
)


def section(title: str) -> None:
    st.markdown(f'<div class="section-bar">{title}</div>', unsafe_allow_html=True)


# --------------------------------------------------------------------------
# 1. HELPERS
# --------------------------------------------------------------------------
def inr(value: float) -> str:
    """Format rupees the Indian way: ₹1.56 Cr, ₹7.7 L, ₹12,345."""
    sign = "-" if value < 0 else ""
    v = abs(value)
    if v >= 1e7:
        return f"{sign}₹{v / 1e7:,.2f} Cr"
    if v >= 1e5:
        return f"{sign}₹{v / 1e5:,.2f} L"
    return f"{sign}₹{v:,.0f}"


def pct(numerator: float, denominator: float) -> float:
    """Safe percentage (returns 0 instead of crashing when denominator is 0)."""
    return (numerator / denominator * 100) if denominator else 0.0


def style(fig: go.Figure, height: int = 380) -> go.Figure:
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=50, b=10),
                      legend=dict(orientation="h", y=-0.2),
                      plot_bgcolor="white", font=dict(size=13))
    fig.update_yaxes(gridcolor="#EEF0F6")
    return fig


# --------------------------------------------------------------------------
# 2. DATA LOADING (cached so Streamlit does not re-read Excel on every click)
# --------------------------------------------------------------------------
@st.cache_data(show_spinner="Loading data...")
def load_data(source) -> pd.DataFrame:
    df = pd.read_excel(source)
    df["Order_Date"] = pd.to_datetime(df["Order_Date"], errors="coerce")
    df = df.dropna(subset=["Order_Date"]).drop_duplicates(subset="Order_ID")
    for col in ["Quantity", "Unit_Price_INR", "Discount_Pct",
                "Total_Sales_INR", "Profit_INR"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    for col in ["Category", "Product", "Payment_Method", "Fulfillment",
                "Order_Status", "Ship_State"]:
        df[col] = df[col].astype(str).str.strip()
    df["Month"] = df["Order_Date"].dt.to_period("M").dt.to_timestamp()
    return df


if Path(DATA_FILE).exists():
    raw = load_data(DATA_FILE)
else:
    up = st.file_uploader("Upload Amazon_Sales_Data_India.xlsx", type=["xlsx"])
    if up is None:
        st.info("Place the Excel file next to app.py, or upload it above.")
        st.stop()
    raw = load_data(up)

# --------------------------------------------------------------------------
# 3. SIDEBAR FILTERS
# --------------------------------------------------------------------------
st.sidebar.header("🔎 Filters")
min_d, max_d = raw["Order_Date"].min().date(), raw["Order_Date"].max().date()
date_sel = st.sidebar.date_input("Date range", (min_d, max_d),
                                 min_value=min_d, max_value=max_d)
# date_input returns 1 date while the user is still picking the 2nd one
start_d, end_d = (date_sel[0], date_sel[1]) if len(date_sel) == 2 else (date_sel[0], max_d)

categories = sorted(raw["Category"].unique())
states = sorted(raw["Ship_State"].unique())
cat_sel = st.sidebar.multiselect("Category", categories, default=categories)
state_sel = st.sidebar.multiselect("State", states, default=states)
st.sidebar.caption("Every number and chart updates with these filters.")

df = raw[
    raw["Order_Date"].dt.date.between(start_d, end_d)
    & raw["Category"].isin(cat_sel)
    & raw["Ship_State"].isin(state_sel)
].copy()

# --------------------------------------------------------------------------
# 4. HEADER
# --------------------------------------------------------------------------
st.title("Amazon India Dashboard")
st.caption(f"Showing {start_d:%d %b %Y} to {end_d:%d %b %Y}  |  "
           f"{len(cat_sel)} categories  |  {len(state_sel)} states")

if df.empty:
    st.warning("No orders match the current filters. Please widen your selection.")
    st.stop()

# --------------------------------------------------------------------------
# SECTION 1: OVERALL SALES & PROFIT
# --------------------------------------------------------------------------
section("1) Overall Sales & Profit Performance")

total_sales = df["Total_Sales_INR"].sum()
total_profit = df["Profit_INR"].sum()
total_orders = df["Order_ID"].nunique()
total_units = int(df["Quantity"].sum())
aov = total_sales / total_orders if total_orders else 0
margin = pct(total_profit, total_sales)

c = st.columns(6)
c[0].metric("Total Sales", inr(total_sales))
c[1].metric("Total Profit", inr(total_profit))
c[2].metric("Total Orders", f"{total_orders:,}")
c[3].metric("Units Sold", f"{total_units:,}")
c[4].metric("Avg Order Value", f"₹{aov:,.0f}")
c[5].metric("Profit Margin", f"{margin:.1f}%")

monthly = (df.groupby("Month")[["Total_Sales_INR", "Profit_INR"]].sum()
             .reset_index().sort_values("Month"))
fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(go.Scatter(x=monthly["Month"], y=monthly["Total_Sales_INR"],
                         name="Sales (left axis)", mode="lines+markers",
                         line=dict(color=SALES_COLOR, width=3)), secondary_y=False)
fig.add_trace(go.Scatter(x=monthly["Month"], y=monthly["Profit_INR"],
                         name="Profit (right axis)", mode="lines+markers",
                         line=dict(color=PROFIT_COLOR, width=3)), secondary_y=True)
fig.update_yaxes(title_text="Sales (₹)", secondary_y=False)
fig.update_yaxes(title_text="Profit (₹)", secondary_y=True, showgrid=False)
fig.update_layout(title="Monthly Sales & Profit Trend")
st.plotly_chart(style(fig, 420), use_container_width=True)

if len(monthly) >= 2:
    best = monthly.loc[monthly["Total_Sales_INR"].idxmax()]
    half = len(monthly) // 2
    first, last = monthly["Total_Sales_INR"].iloc[:half].mean(), monthly["Total_Sales_INR"].iloc[half:].mean()
    direction = "higher" if last >= first else "lower"
    st.info(f"**Quick read:** Best month was {best['Month']:%b %Y} ({inr(best['Total_Sales_INR'])}). "
            f"Average monthly sales in the later half of this period are "
            f"{abs(pct(last - first, first)):.1f}% {direction} than the earlier half.")

# --------------------------------------------------------------------------
# SECTION 2: CATEGORY & PRODUCT
# --------------------------------------------------------------------------
section("2) Category & Product Performance")

cat = (df.groupby("Category")
         .agg(Sales=("Total_Sales_INR", "sum"), Profit=("Profit_INR", "sum"),
              Units=("Quantity", "sum"))
         .reset_index().sort_values("Sales", ascending=False))

left, right = st.columns([3, 2])
with left:
    melted = cat.melt(id_vars="Category", value_vars=["Sales", "Profit"],
                      var_name="Measure", value_name="Amount (₹)")
    fig = px.bar(melted, x="Category", y="Amount (₹)", color="Measure", barmode="group",
                 color_discrete_map={"Sales": SALES_COLOR, "Profit": PROFIT_COLOR},
                 title="Category-wise Sales & Profit")
    st.plotly_chart(style(fig), use_container_width=True)
with right:
    fig = px.pie(cat, names="Category", values="Units", hole=0.55,
                 title="Share of Units Sold by Category")
    fig.update_traces(textinfo="percent")
    st.plotly_chart(style(fig), use_container_width=True)

top10 = (df.groupby(["Product", "Category"])["Total_Sales_INR"].sum()
           .reset_index().nlargest(10, "Total_Sales_INR").sort_values("Total_Sales_INR"))
fig = px.bar(top10, x="Total_Sales_INR", y="Product", orientation="h", color="Category",
             title="Top 10 Products by Sales", labels={"Total_Sales_INR": "Sales (₹)"})
st.plotly_chart(style(fig, 440), use_container_width=True)

top_cat = cat.iloc[0]
best_margin = cat.assign(M=cat["Profit"] / cat["Sales"]).sort_values("M").iloc[-1]
st.info(f"**Quick read:** {top_cat['Category']} brings in the most sales "
        f"({pct(top_cat['Sales'], total_sales):.0f}% of the total). "
        f"{best_margin['Category']} keeps the most profit per rupee sold "
        f"({pct(best_margin['Profit'], best_margin['Sales']):.1f}%).")

# --------------------------------------------------------------------------
# SECTION 3: ORDER STATUS & REVENUE LOSS
# --------------------------------------------------------------------------
section("3) Order Status & Revenue Loss")

status_counts = df["Order_Status"].value_counts()
n = {s: int(status_counts.get(s, 0)) for s in STATUS_COLORS}
return_rate = pct(n["Returned"], total_orders)
cancel_rate = pct(n["Cancelled"], total_orders)

c = st.columns(6)
c[0].metric("Delivered Orders", f"{n['Delivered']:,}")
c[1].metric("Shipped Orders", f"{n['Shipped']:,}")
c[2].metric("Returned Orders", f"{n['Returned']:,}")
c[3].metric("Cancelled Orders", f"{n['Cancelled']:,}")
c[4].metric("Return Rate", f"{return_rate:.1f}%")
c[5].metric("Cancellation Rate", f"{cancel_rate:.1f}%")

lost = df[df["Order_Status"].isin(["Returned", "Cancelled"])]
lost_value = lost["Total_Sales_INR"].sum()
st.metric("Revenue Lost to Returns + Cancellations", inr(lost_value),
          f"{pct(lost_value, total_sales):.1f}% of total sales", delta_color="inverse")

left, right = st.columns(2)
with left:
    sdf = status_counts.rename_axis("Status").reset_index(name="Orders")
    fig = px.pie(sdf, names="Status", values="Orders", hole=0.55, color="Status",
                 color_discrete_map=STATUS_COLORS, title="Order Status Breakdown")
    st.plotly_chart(style(fig), use_container_width=True)
with right:
    loss_cat = (lost.groupby(["Category", "Order_Status"])["Total_Sales_INR"].sum()
                    .reset_index())
    fig = px.bar(loss_cat, x="Category", y="Total_Sales_INR", color="Order_Status",
                 barmode="stack", color_discrete_map=STATUS_COLORS,
                 labels={"Total_Sales_INR": "Revenue lost (₹)"},
                 title="Revenue Lost by Category (Returns & Cancellations)")
    st.plotly_chart(style(fig), use_container_width=True)

if not lost.empty:
    worst = lost.groupby("Category")["Total_Sales_INR"].sum().idxmax()
    st.info(f"**Quick read:** About {pct(n['Returned'] + n['Cancelled'], total_orders):.1f}% of orders "
            f"never turn into revenue. The biggest loss is in **{worst}**. "
            f"Returned and cancelled orders carry zero profit in this data.")

# --------------------------------------------------------------------------
# SECTION 4: PAYMENT, FULFILLMENT & GEOGRAPHY
# --------------------------------------------------------------------------
section("4) Payment, Fulfillment & Geographic Performance")


def grouped_sales_profit(group_col: str, title: str) -> go.Figure:
    g = (df.groupby(group_col)[["Total_Sales_INR", "Profit_INR"]].sum()
           .reset_index().sort_values("Total_Sales_INR", ascending=False))
    m = g.melt(id_vars=group_col, var_name="Measure", value_name="Amount (₹)")
    m["Measure"] = m["Measure"].map({"Total_Sales_INR": "Sales", "Profit_INR": "Profit"})
    fig = px.bar(m, x=group_col, y="Amount (₹)", color="Measure", barmode="group",
                 color_discrete_map={"Sales": SALES_COLOR, "Profit": PROFIT_COLOR},
                 title=title, labels={group_col: ""})
    return style(fig)


left, right = st.columns(2)
with left:
    st.plotly_chart(grouped_sales_profit("Payment_Method", "Sales & Profit by Payment Method"),
                    use_container_width=True)
with right:
    st.plotly_chart(grouped_sales_profit("Fulfillment", "Sales & Profit by Fulfillment Method"),
                    use_container_width=True)

geo = (df.groupby("Ship_State")
         .agg(Sales=("Total_Sales_INR", "sum"), Profit=("Profit_INR", "sum"),
              Orders=("Order_ID", "nunique"))
         .reset_index())
metric_choice = st.radio("State view", ["Sales", "Profit", "Orders"], horizontal=True)
top_states = geo.nlargest(10, metric_choice).sort_values(metric_choice)
fig = px.bar(top_states, x=metric_choice, y="Ship_State", orientation="h",
             color=metric_choice, color_continuous_scale="Blues",
             title=f"Top 10 States by {metric_choice}", labels={"Ship_State": ""})
fig.update_coloraxes(showscale=False)
st.plotly_chart(style(fig, 440), use_container_width=True)

pay = df.groupby("Payment_Method")["Total_Sales_INR"].sum()
ful = df.groupby("Fulfillment")["Total_Sales_INR"].sum()
st_top = geo.nlargest(1, "Sales").iloc[0]
st.info(f"**Quick read:** {pay.idxmax()} is the biggest payment method "
        f"({pct(pay.max(), total_sales):.0f}% of sales); {ful.idxmax()} is the biggest fulfillment "
        f"channel ({pct(ful.max(), total_sales):.0f}%). {st_top['Ship_State']} is the top state "
        f"({pct(st_top['Sales'], total_sales):.0f}% of sales).")

with st.expander("View filtered data (first 500 rows)"):
    st.dataframe(df.drop(columns="Month").head(500), use_container_width=True)
