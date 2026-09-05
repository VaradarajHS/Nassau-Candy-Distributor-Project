import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path



st.set_page_config(
    page_title="Nassau Candy Profitability Dashboard",
    page_icon="📊",
    layout="wide"
)



st.markdown("""
<style>

.main-title {
    font-size: 32px;
    font-weight: 700;
    margin-bottom: 5px;
}

.subtitle {
    font-size: 16px;
    color: #666666;
    margin-bottom: 25px;
}

.section-title {
    font-size: 24px;
    font-weight: 650;
    margin-top: 25px;
    margin-bottom: 15px;
}

</style>
""", unsafe_allow_html=True)



st.markdown(
    '<div class="main-title">Product Line Profitability & Margin Performance Analysis</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Nassau Candy Distribution — Profitability & Margin Performance Dashboard</div>',
    unsafe_allow_html=True
)



@st.cache_data
def load_data():

    # Automatically find the Downloads folder on your Mac
    downloads_folder = Path.home() / "Downloads"

    file_path = downloads_folder / "Nassau Candy Distributor.csv"

    if not file_path.exists():
        raise FileNotFoundError(
            f"Could not find:\n{file_path}"
        )

    df = pd.read_csv(file_path)

    return df



try:

    raw_df = load_data()

except FileNotFoundError:

    st.error(
        "❌ Dataset not found.\n\n"
        "Please make sure this file is inside your Downloads folder:\n\n"
        "**Nassau Candy Distributor.csv**"
    )

    st.stop()

except Exception as e:

    st.error(f"❌ Error loading dataset: {e}")

    st.stop()



required_columns = [
    "Order Date",
    "Division",
    "Product Name",
    "Sales",
    "Units",
    "Gross Profit",
    "Cost"
]

missing_columns = [
    col for col in required_columns
    if col not in raw_df.columns
]

if missing_columns:

    st.error(
        "The following required columns are missing:\n\n"
        + ", ".join(missing_columns)
    )

    st.stop()



df = raw_df.copy()



df["Order Date"] = pd.to_datetime(
    df["Order Date"],
    dayfirst=True,
    errors="coerce"
)



numeric_columns = [
    "Sales",
    "Units",
    "Gross Profit",
    "Cost"
]

for column in numeric_columns:

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    ).fillna(0)



df["Gross Margin (%)"] = np.where(
    df["Sales"] != 0,
    (df["Gross Profit"] / df["Sales"]) * 100,
    0
)


df["Profit per Unit"] = np.where(
    df["Units"] != 0,
    df["Gross Profit"] / df["Units"],
    0
)


df["Cost % of Sales"] = np.where(
    df["Sales"] != 0,
    (df["Cost"] / df["Sales"]) * 100,
    0
)



st.sidebar.header("Dashboard Controls")

st.sidebar.success(
    "Dataset loaded automatically from Downloads"
)

st.sidebar.divider()

st.sidebar.subheader("Filters")



valid_dates = df["Order Date"].dropna()

if len(valid_dates) > 0:

    min_date = valid_dates.min().date()
    max_date = valid_dates.max().date()

    date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if len(date_range) == 2:

        start_date = pd.Timestamp(date_range[0])
        end_date = pd.Timestamp(date_range[1]) + pd.Timedelta(days=1)

        df = df[
            (df["Order Date"] >= start_date)
            &
            (df["Order Date"] < end_date)
        ]



divisions = sorted(
    df["Division"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)

selected_divisions = st.sidebar.multiselect(
    "Division",
    divisions,
    default=divisions
)

if selected_divisions:

    df = df[
        df["Division"].isin(selected_divisions)
    ]



margin_threshold = st.sidebar.slider(
    "Margin Threshold (%)",
    min_value=0,
    max_value=100,
    value=30,
    step=5
)



product_search = st.sidebar.text_input(
    "Product Search"
)

if product_search:

    df = df[
        df["Product Name"]
        .astype(str)
        .str.contains(
            product_search,
            case=False,
            na=False
        )
    ]



if df.empty:

    st.warning(
        "⚠️ No records match the selected filters."
    )

    st.stop()



product_summary = (
    df.groupby(
        "Product Name",
        as_index=False
    )
    .agg(
        Sales=("Sales", "sum"),
        Cost=("Cost", "sum"),
        Units=("Units", "sum"),
        Gross_Profit=("Gross Profit", "sum")
    )
)


product_summary["Gross Margin (%)"] = np.where(
    product_summary["Sales"] != 0,
    product_summary["Gross_Profit"]
    / product_summary["Sales"] * 100,
    0
)


product_summary["Profit per Unit"] = np.where(
    product_summary["Units"] != 0,
    product_summary["Gross_Profit"]
    / product_summary["Units"],
    0
)


product_summary["Cost % of Sales"] = np.where(
    product_summary["Sales"] != 0,
    product_summary["Cost"]
    / product_summary["Sales"] * 100,
    0
)


product_summary.rename(
    columns={
        "Product Name": "Product",
        "Gross_Profit": "Gross Profit"
    },
    inplace=True
)



division_summary = (
    df.groupby(
        "Division",
        as_index=False
    )
    .agg(
        Sales=("Sales", "sum"),
        Cost=("Cost", "sum"),
        Units=("Units", "sum"),
        Gross_Profit=("Gross Profit", "sum")
    )
)


division_summary["Gross Margin (%)"] = np.where(
    division_summary["Sales"] != 0,
    division_summary["Gross_Profit"]
    / division_summary["Sales"] * 100,
    0
)


division_summary["Profit per Unit"] = np.where(
    division_summary["Units"] != 0,
    division_summary["Gross_Profit"]
    / division_summary["Units"],
    0
)


division_summary.rename(
    columns={
        "Gross_Profit": "Gross Profit"
    },
    inplace=True
)



def get_recommendation(row):

    cost_pct = row["Cost % of Sales"]
    margin = row["Gross Margin (%)"]

    if cost_pct > 80 and margin < margin_threshold:

        return "Discontinuation Review"

    elif cost_pct > 50 and margin < margin_threshold:

        return "Repricing"

    elif cost_pct > 50 and margin >= margin_threshold:

        return "Cost Renegotiation"

    else:

        return "Monitor"


def get_risk(row):

    cost_pct = row["Cost % of Sales"]
    margin = row["Gross Margin (%)"]

    if cost_pct > 80 and margin < margin_threshold:

        return "High Risk"

    elif cost_pct > 50 and margin < margin_threshold:

        return "Medium Risk"

    elif cost_pct > 50:

        return "Cost Risk"

    elif margin < margin_threshold:

        return "Margin Risk"

    else:

        return "Healthy"


product_summary["Recommendation"] = (
    product_summary.apply(
        get_recommendation,
        axis=1
    )
)


product_summary["Risk Flag"] = (
    product_summary.apply(
        get_risk,
        axis=1
    )
)



st.markdown(
    '<div class="section-title">Product Profitability Overview</div>',
    unsafe_allow_html=True
)


total_sales = df["Sales"].sum()

total_cost = df["Cost"].sum()

total_profit = df["Gross Profit"].sum()

total_units = df["Units"].sum()


overall_margin = (
    total_profit / total_sales * 100
    if total_sales != 0
    else 0
)


profit_per_unit = (
    total_profit / total_units
    if total_units != 0
    else 0
)


cost_percentage = (
    total_cost / total_sales * 100
    if total_sales != 0
    else 0
)



k1, k2, k3, k4, k5 = st.columns(5)


k1.metric(
    "Revenue",
    f"${total_sales:,.0f}"
)


k2.metric(
    "Gross Profit",
    f"${total_profit:,.0f}"
)


k3.metric(
    "Gross Margin",
    f"{overall_margin:.1f}%"
)


k4.metric(
    "Profit / Unit",
    f"${profit_per_unit:,.2f}"
)


k5.metric(
    "Cost % of Sales",
    f"{cost_percentage:.1f}%"
)



st.markdown(
    '<div class="section-title">Product-Level Margin Leaderboard</div>',
    unsafe_allow_html=True
)


leaderboard = (
    product_summary
    .sort_values(
        "Gross Margin (%)",
        ascending=False
    )
    .copy()
)


leaderboard_display = leaderboard[
    [
        "Product",
        "Sales",
        "Cost",
        "Gross Profit",
        "Gross Margin (%)",
        "Profit per Unit",
        "Cost % of Sales",
        "Risk Flag",
        "Recommendation"
    ]
]


st.dataframe(
    leaderboard_display.style.format({
        "Sales": "${:,.0f}",
        "Cost": "${:,.0f}",
        "Gross Profit": "${:,.0f}",
        "Gross Margin (%)": "{:.1f}%",
        "Profit per Unit": "${:,.2f}",
        "Cost % of Sales": "{:.1f}%"
    }),
    use_container_width=True,
    hide_index=True
)



st.markdown(
    '<div class="section-title">Profit Contribution</div>',
    unsafe_allow_html=True
)


top_profit = (
    product_summary
    .sort_values(
        "Gross Profit",
        ascending=False
    )
    .head(15)
)


fig_profit = px.bar(
    top_profit,
    x="Gross Profit",
    y="Product",
    orientation="h",
    title="Top 15 Products by Gross Profit"
)


fig_profit.update_layout(
    yaxis={
        "categoryorder": "total ascending"
    }
)


st.plotly_chart(
    fig_profit,
    use_container_width=True
)



st.markdown(
    '<div class="section-title">Division Performance Dashboard</div>',
    unsafe_allow_html=True
)


# Revenue vs Profit

fig_division = px.bar(
    division_summary,
    x="Division",
    y=[
        "Sales",
        "Gross Profit"
    ],
    barmode="group",
    title="Revenue vs Profit by Division"
)


st.plotly_chart(
    fig_division,
    use_container_width=True
)



fig_margin_division = px.bar(
    division_summary.sort_values(
        "Gross Margin (%)",
        ascending=False
    ),
    x="Division",
    y="Gross Margin (%)",
    title="Gross Margin by Division"
)


fig_margin_division.add_hline(
    y=margin_threshold,
    line_dash="dash",
    annotation_text=f"Threshold: {margin_threshold}%"
)


st.plotly_chart(
    fig_margin_division,
    use_container_width=True
)




st.subheader("Division Performance Summary")


division_display = division_summary[
    [
        "Division",
        "Sales",
        "Cost",
        "Gross Profit",
        "Gross Margin (%)",
        "Profit per Unit"
    ]
]


st.dataframe(
    division_display.style.format({
        "Sales": "${:,.0f}",
        "Cost": "${:,.0f}",
        "Gross Profit": "${:,.0f}",
        "Gross Margin (%)": "{:.1f}%",
        "Profit per Unit": "${:,.2f}"
    }),
    use_container_width=True,
    hide_index=True
)



st.markdown(
    '<div class="section-title">Cost vs Margin Diagnostics</div>',
    unsafe_allow_html=True
)


fig_scatter = px.scatter(
    product_summary,
    x="Cost % of Sales",
    y="Gross Margin (%)",
    size="Sales",
    hover_name="Product",
    hover_data=[
        "Sales",
        "Gross Profit",
        "Profit per Unit",
        "Recommendation",
        "Risk Flag"
    ],
    title="Cost vs Margin Diagnostic"
)




fig_scatter.add_vline(
    x=50,
    line_dash="dash",
    annotation_text="50% Cost Threshold"
)


fig_scatter.add_vline(
    x=80,
    line_dash="dash",
    annotation_text="80% Cost Threshold"
)




fig_scatter.add_hline(
    y=margin_threshold,
    line_dash="dash",
    annotation_text=f"{margin_threshold}% Margin Threshold"
)


st.plotly_chart(
    fig_scatter,
    use_container_width=True
)



st.subheader("Margin Risk Flags")


risk_summary = (
    product_summary
    .groupby("Risk Flag")
    .size()
    .reset_index(name="Products")
)


fig_risk = px.bar(
    risk_summary,
    x="Risk Flag",
    y="Products",
    title="Products by Risk Category"
)


st.plotly_chart(
    fig_risk,
    use_container_width=True
)



st.markdown(
    '<div class="section-title">Profit Concentration Analysis</div>',
    unsafe_allow_html=True
)


pareto = (
    product_summary
    .sort_values(
        "Gross Profit",
        ascending=False
    )
    .copy()
)


total_pareto_profit = pareto["Gross Profit"].sum()


if total_pareto_profit != 0:

    pareto["Profit Contribution (%)"] = (
        pareto["Gross Profit"]
        / total_pareto_profit
        * 100
    )

    pareto["Cumulative Profit (%)"] = (
        pareto["Profit Contribution (%)"]
        .cumsum()
    )

else:

    pareto["Profit Contribution (%)"] = 0

    pareto["Cumulative Profit (%)"] = 0


fig_pareto = px.bar(
    pareto,
    x="Product",
    y="Gross Profit",
    title="Pareto Analysis — Product Profit Contribution"
)


fig_pareto.add_scatter(
    x=pareto["Product"],
    y=pareto["Cumulative Profit (%)"],
    name="Cumulative Profit %",
    yaxis="y2",
    mode="lines+markers"
)


fig_pareto.update_layout(
    yaxis=dict(
        title="Gross Profit"
    ),
    yaxis2=dict(
        title="Cumulative Profit (%)",
        overlaying="y",
        side="right",
        range=[0, 100]
    ),
    xaxis_tickangle=-45
)


st.plotly_chart(
    fig_pareto,
    use_container_width=True
)



products_80 = pareto[
    pareto["Cumulative Profit (%)"] <= 80
]


if (
    len(products_80) == 0
    and len(pareto) > 0
):

    products_80 = pareto.iloc[[0]]


total_products = len(pareto)

number_products_80 = len(products_80)


concentration_percentage = (
    number_products_80
    / total_products
    * 100
    if total_products > 0
    else 0
)


st.info(
    f"Approximately **{number_products_80} of "
    f"{total_products} products "
    f"({concentration_percentage:.1f}%)** "
    f"account for the first 80% of cumulative gross profit."
)



st.markdown(
    '<div class="section-title">Dependency Indicators</div>',
    unsafe_allow_html=True
)


high_cost_products = len(
    product_summary[
        product_summary["Cost % of Sales"] > 50
    ]
)


low_margin_products = len(
    product_summary[
        product_summary["Gross Margin (%)"]
        < margin_threshold
    ]
)


high_risk_products = len(
    product_summary[
        product_summary["Risk Flag"]
        == "High Risk"
    ]
)


d1, d2, d3, d4 = st.columns(4)


d1.metric(
    "High-Cost Products",
    high_cost_products
)


d2.metric(
    "Low-Margin Products",
    low_margin_products
)


d3.metric(
    "High-Risk Products",
    high_risk_products
)


d4.metric(
    "Products Reviewed",
    len(product_summary)
)



st.markdown(
    '<div class="section-title">Management Recommendations</div>',
    unsafe_allow_html=True
)


recommendation_summary = (
    product_summary
    .groupby("Recommendation")
    .size()
    .reset_index(name="Products")
)


fig_recommendations = px.bar(
    recommendation_summary,
    x="Recommendation",
    y="Products",
    title="Recommended Management Actions"
)


st.plotly_chart(
    fig_recommendations,
    use_container_width=True
)



st.subheader("Product Action List")


action_list = (
    product_summary[
        [
            "Product",
            "Gross Margin (%)",
            "Cost % of Sales",
            "Gross Profit",
            "Profit per Unit",
            "Risk Flag",
            "Recommendation"
        ]
    ]
    .sort_values(
        [
            "Recommendation",
            "Gross Margin (%)"
        ]
    )
)


st.dataframe(
    action_list.style.format({
        "Gross Margin (%)": "{:.1f}%",
        "Cost % of Sales": "{:.1f}%",
        "Gross Profit": "${:,.0f}",
        "Profit per Unit": "${:,.2f}"
    }),
    use_container_width=True,
    hide_index=True
)



st.subheader("Priority Actions")


recommendations = [
    "Discontinuation Review",
    "Repricing",
    "Cost Renegotiation",
    "Monitor"
]


for recommendation_name in recommendations:

    action_df = product_summary[
        product_summary["Recommendation"]
        == recommendation_name
    ]

    if len(action_df) > 0:

        with st.expander(
            f"{recommendation_name} ({len(action_df)} products)"
        ):

            st.dataframe(
                action_df[
                    [
                        "Product",
                        "Sales",
                        "Cost",
                        "Gross Profit",
                        "Gross Margin (%)",
                        "Cost % of Sales",
                        "Risk Flag"
                    ]
                ].style.format({
                    "Sales": "${:,.0f}",
                    "Cost": "${:,.0f}",
                    "Gross Profit": "${:,.0f}",
                    "Gross Margin (%)": "{:.1f}%",
                    "Cost % of Sales": "{:.1f}%"
                }),
                use_container_width=True,
                hide_index=True
            )



st.markdown(
    '<div class="section-title">Margin Volatility</div>',
    unsafe_allow_html=True
)


if df["Order Date"].notna().any():

    time_margin = (
        df.dropna(subset=["Order Date"])
        .groupby(
            "Order Date",
            as_index=False
        )
        .agg(
            Sales=("Sales", "sum"),
            Gross_Profit=("Gross Profit", "sum")
        )
    )


    time_margin["Gross Margin (%)"] = np.where(
        time_margin["Sales"] != 0,
        time_margin["Gross_Profit"]
        / time_margin["Sales"]
        * 100,
        0
    )


    fig_volatility = px.line(
        time_margin,
        x="Order Date",
        y="Gross Margin (%)",
        title="Gross Margin Over Time"
    )


    fig_volatility.add_hline(
        y=margin_threshold,
        line_dash="dash",
        annotation_text="Margin Threshold"
    )


    st.plotly_chart(
        fig_volatility,
        use_container_width=True
    )


    margin_volatility = (
        time_margin["Gross Margin (%)"].std()
        if len(time_margin) > 1
        else 0
    )


    st.metric(
        "Margin Volatility",
        f"{margin_volatility:.2f} percentage points"
    )

else:

    st.info(
        "A valid Order Date column was not available, "
        "so margin volatility cannot be calculated."
    )



with st.expander("Data Quality & Dataset Information"):

    q1, q2, q3, q4 = st.columns(4)


    q1.metric(
        "Rows",
        f"{len(df):,}"
    )


    q2.metric(
        "Products",
        f"{df['Product Name'].nunique():,}"
    )


    q3.metric(
        "Divisions",
        f"{df['Division'].nunique():,}"
    )


    q4.metric(
        "Columns",
        f"{len(raw_df.columns):,}"
    )


    st.write("Detected Dataset Columns:")

    st.write(
        list(raw_df.columns)
    )



st.divider()

st.caption(
    "Nassau Candy Product Line Profitability & Margin Performance Analysis"
)