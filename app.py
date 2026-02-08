import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Page setup
st.set_page_config(
    page_title="Adaptive CSV Dashboard",
    layout="wide"
)

st.title("📊 Adaptive CSV Dashboard")
st.write("Upload any CSV file. The dashboard adapts to your data.")

# File upload
file = st.file_uploader("Upload CSV file", type=["csv"])

if file:
    # Read CSV safely
    try:
        df = pd.read_csv(file)
    except UnicodeDecodeError:
        file.seek(0)
        df = pd.read_csv(file, encoding="latin1")

    # Clean column names
    df.columns = (
        df.columns
        .astype(str)
        .str.replace("\xa0", " ", regex=False)
        .str.strip()
    )

    # Preview
    st.subheader("🔍 Data Preview")
    st.dataframe(df.head(), use_container_width=True)

    # Detect numeric columns
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    if not numeric_cols:
        st.error("No numeric columns found in this CSV.")
        st.stop()

    # Sidebar controls
    st.sidebar.header("⚙️ Dashboard Controls")

    value_col = st.sidebar.selectbox(
        "Metric Column",
        numeric_cols
    )

    group_col = st.sidebar.selectbox(
        "Group By Column",
        df.columns
    )

    date_col = st.sidebar.selectbox(
        "Date Column (optional)",
        ["None"] + df.columns.tolist()
    )

    # Date filtering
    filtered_df = df.copy()

    if date_col != "None":
        filtered_df[date_col] = pd.to_datetime(
            filtered_df[date_col],
            errors="coerce"
        )
        filtered_df = filtered_df.dropna(subset=[date_col])

        if not filtered_df.empty:
            st.sidebar.subheader("📅 Date Range")

            min_date = filtered_df[date_col].min().date()
            max_date = filtered_df[date_col].max().date()

            start_date, end_date = st.sidebar.date_input(
                "Select date range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )

            filtered_df = filtered_df[
                (filtered_df[date_col].dt.date >= start_date) &
                (filtered_df[date_col].dt.date <= end_date)
            ]

    if filtered_df.empty:
        st.warning("No data available after filtering.")
        st.stop()

    # KPIs
    st.subheader("📌 Key Metrics")
    k1, k2, k3 = st.columns(3)

    k1.metric("Total", f"{filtered_df[value_col].sum():,.2f}")
    k2.metric("Average", f"{filtered_df[value_col].mean():,.2f}")
    k3.metric("Max", f"{filtered_df[value_col].max():,.2f}")

    # Charts layout
    st.subheader("📊 Visualizations")
    c1, c2, c3 = st.columns(3)

    # 1️⃣ Time Series 
    with c1:
        with st.container(border=True):
            st.markdown("### 📈 Time Series")

            if date_col == "None":
                st.info("Select a date column to view time series.")
            else:
                ts_df = (
                    filtered_df
                    .groupby(filtered_df[date_col].dt.date)[value_col]
                    .sum()
                    .reset_index()
                )

                if len(ts_df) < 2:
                    st.warning("Not enough data for time series.")
                else:
                    fig, ax = plt.subplots(figsize=(5, 3))
                    ax.plot(
                        ts_df[date_col],
                        ts_df[value_col],
                        marker="o"
                    )
                    ax.set_xlabel("Date")
                    ax.set_ylabel(value_col)
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    st.pyplot(fig, clear_figure=True)

    # 2️⃣ Grouped Bar Chart (PAGED for many Order IDs)
    with c2:
        with st.container(border=True):
            st.markdown("### 📊 Grouped Bar (Paged)")

            bar_df = (
                filtered_df
                .groupby(group_col, dropna=False)[value_col]
                .sum()
                .reset_index()
                .sort_values(value_col, ascending=False)
            )

            if bar_df.empty:
                st.warning("No data to display.")
            else:
                bars_per_page = st.slider(
                    "Bars per view",
                    min_value=5,
                    max_value=40,
                    value=15,
                    step=5
                )

                total_pages = (len(bar_df) - 1) // bars_per_page + 1

                page = st.slider(
                    "Page",
                    min_value=1,
                    max_value=total_pages,
                    value=1
                )

                start = (page - 1) * bars_per_page
                end = start + bars_per_page
                page_df = bar_df.iloc[start:end]

                fig2, ax2 = plt.subplots(figsize=(6, 4))

                # Horizontal bars for long IDs
                ax2.barh(
                    page_df[group_col].astype(str),
                    page_df[value_col]
                )
                ax2.invert_yaxis()

                ax2.set_xlabel(value_col)
                ax2.set_ylabel(group_col)
                ax2.set_title(f"Page {page} of {total_pages}")

                plt.tight_layout()
                st.pyplot(fig2, clear_figure=True)

    # 3️⃣ Distribution
    with c3:
        with st.container(border=True):
            st.markdown("### 📉 Distribution")

            fig3, ax3 = plt.subplots(figsize=(5, 3))
            ax3.hist(filtered_df[value_col], bins=10)
            ax3.set_xlabel(value_col)
            ax3.set_ylabel("Frequency")
            plt.tight_layout()
            st.pyplot(fig3, clear_figure=True)

else:
    st.info("Upload a CSV file to get started.")
