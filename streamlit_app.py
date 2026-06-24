import streamlit as st
import pandas as pd
import math
from pathlib import Path
from datetime import datetime
import plotly.express as px 

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title="Flux Time Series Dashboard",
    page_icon="📈",
    layout="wide"
)

# -----------------------------------------------------------------------------
# Declare some useful functions.

@st.cache_data
def get_flux_data(date_col='date', time_col='time', sep=','):

    #This uses caching to avoid having to read the file every time. If we were
    #reading from an HTTP endpoint instead of a file, it's a good idea to set
    #a maximum age to the cache with the TTL argument: @st.cache_data(ttl='1d')
    
    
    #Load data from CSV, Excel, TSV or TXT.
    #For Excel, use sep=None and let pandas detect.
    

    # Instead of a CSV on disk, you could read from an HTTP endpoint here too.
    DATA_FILENAME = Path(__file__).parent/'data/2026-06-10_smart3-01508_EP-Summary.txt'

    if DATA_FILENAME.name.endswith('.csv'):
        df = pd.read_csv(DATA_FILENAME, sep=sep)
    elif DATA_FILENAME.name.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(DATA_FILENAME)
    else:
        # fallback to tab-separated
        df = pd.read_csv(DATA_FILENAME, sep='\t')

    
    # Combine date and time columns into a datetime index.
    
    df = df.drop([0])
    df = df.drop(['DATAH','filename','DOY','daytime','file_records','used_records'], axis=1)

    # Ensure both columns are strings
    df[date_col] = df[date_col].astype(str)
    df[time_col] = df[time_col].astype(str)

    # Create a combined datetime column
    df['datetime'] = df[date_col] + ' ' + df[time_col]
    df['datetime'] = pd.to_datetime(df['datetime'], format='%Y-%m-%d %H:%M:%S')
    # Set as index and sort
    df = df.set_index('datetime').sort_index()

    # Drop the original date and time columns (they are now redundant)
    df = df.drop(columns=[date_col, time_col], errors='ignore')

    # Convert all remaining columns to float, coercing errors to NaN
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


flux_df = get_flux_data()

# -----------------------------------------------------------------------------
# Draw the actual page

# Set the title that appears at the top of the page.
'''
# :earth_americas: Eddy Covariance dashboard

By LIIS.LPO.
'''

# Add some spacing
''
''
st.markdown("### Choose Variables to Visualise")

numeric_cols = flux_df.select_dtypes(include=['number']).columns.tolist()
selected_vars = st.multiselect(
    "Select one or more numeric columns to plot",
    numeric_cols,
    default=numeric_cols[:2] if len(numeric_cols) >= 2 else numeric_cols
)

if not selected_vars:
    st.info("Select at least one variable to plot.")
    st.stop()


# Time range filter
st.markdown("### Filter by Time Range")

min_date = flux_df.index.min().to_pydatetime()
max_date = flux_df.index.max().to_pydatetime()

# Use datetime slider (Streamlit supports datetime objects)
date_range = st.slider(
    "Select time range",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date),
    format="YYYY-MM-DD HH:mm:ss"
)

filtered_df = flux_df.loc[date_range[0]:date_range[1]]

if filtered_df.empty:
    st.warning("No data in the selected time range.")
    st.stop()


# Plot with Plotly
st.markdown("### Time Series Plot")
fig = px.line(
    filtered_df,
    x=filtered_df.index,
    y=selected_vars,
    title="Values over Time",
    labels={"value": "Value", "variable": "Variable", "index": "Date & Time"},
    color_discrete_sequence=px.colors.qualitative.Plotly
)

fig.update_layout(
    xaxis_title="Date & Time",
    yaxis_title="Values",
    hovermode="x unified",  # shows all values at the same x
    legend_title="Variables",
    template="plotly_white"
)

st.plotly_chart(fig, use_container_width=True)

# Metrics: show latest value for each selected variable
st.markdown("### Latest Values")

# Get the last available row for each variable (if multiple rows at same time, take mean)
latest = filtered_df[selected_vars].iloc[-1]  # last row in filtered range

cols = st.columns(min(len(selected_vars), 4))  # max 4 per row
for i, var in enumerate(selected_vars):
    col = cols[i % 4]
    with col:
        value = latest[var]
        if math.isnan(value):
            st.metric(label=var, value="N/A")
        else:
            # Format nicely
            if abs(value) >= 1e6:
                display = f"{value/1e6:.1f}M"
            elif abs(value) >= 1e3:
                display = f"{value/1e3:.1f}K"
            else:
                display = f"{value:.2f}"
            st.metric(label=var, value=display)


# Optional: Show raw data
#with st.expander("View filtered data"):
#    st.dataframe(filtered_df[selected_vars], use_container_width=True)

