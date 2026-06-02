import streamlit as st

RTL_CSS = """
<style>
[data-testid="stAppViewContainer"] {
    direction: rtl;
    text-align: right;
}
[data-testid="stSidebar"] {
    direction: rtl;
    text-align: right;
}
[data-testid="stMarkdownContainer"] {
    text-align: right;
}
[data-testid="stMetricValue"] {
    text-align: right;
}
.stTabs [data-baseweb="tab-list"] {
    direction: rtl;
}
.stDataFrame {
    direction: rtl;
}
div[data-testid="column"] {
    direction: rtl;
    text-align: right;
}
</style>
"""

def inject_rtl():
    st.markdown(RTL_CSS, unsafe_allow_html=True)
