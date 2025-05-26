import streamlit as st
from calculator_core import ESSSampleSizeCalculator, SurveyParameters
import plotly.express as px
import pandas as pd
from auth_lib import authenticate_user
import json

# Initialize components
calculator = ESSSampleSizeCalculator()
authenticate_user()

# --- Page Config ---
st.set_page_config(
    page_title="ESS Sample Size Calculator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS Styling ---
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- Main UI ---
def main():
    # Header with logo
    st.markdown("""
    <div class="header">
        <img src="app/static/ess_logo.png" width=120>
        <h1>Sample Size Determination</h1>
    </div>
    """, unsafe_allow_html=True)

    # Survey selection
    survey_type = st.selectbox(
        "Select Survey Type",
        options=calculator.get_survey_types(),
        format_func=lambda x: x['name'],
        help="Choose the survey type from ESS standards"
    )

    with st.form("parameters"):
        col1, col2 = st.columns(2)
        
        with col1:
            pop_size = st.number_input(
                "Total EAs in Population",
                min_value=1,
                value=15000,
                step=1000
            )
            confidence = st.select_slider(
                "Confidence Level",
                options=[90, 95, 99],
                value=95
            )
            margin_error = st.slider(
                "Margin of Error (%)",
                min_value=1,
                max_value=20,
                value=5
            )
            
        with col2:
            cluster_size = st.number_input(
                "Households per EA",
                min_value=5,
                max_value=50,
                value=25
            )
            icc = st.slider(
                "Intra-class Correlation (ICC)",
                min_value=0.01,
                max_value=0.5,
                value=0.15,
                step=0.01
            )
            non_response = st.slider(
                "Non-response Rate (%)",
                min_value=0,
                max_value=30,
                value=10
            )

        # Power analysis section
        with st.expander("⚡ Power Analysis (Optional)"):
            effect_size = st.slider(
                "Effect Size to Detect",
                min_value=0.1,
                max_value=1.0,
                value=0.5,
                step=0.05
            )
            alpha = st.slider(
                "Significance Level (α)",
                min_value=0.01,
                max_value=0.1,
                value=0.05,
                step=0.01
            )
            power = st.slider(
                "Statistical Power",
                min_value=0.7,
                max_value=0.99,
                value=0.8,
                step=0.01
            )

        if st.form_submit_button("Calculate Sample Size"):
            params = SurveyParameters(
                survey_type=survey_type['id'],
                population_size=pop_size,
                confidence_level=confidence,
                margin_error=margin_error/100,
                avg_cluster_size=cluster_size,
                icc=icc,
                non_response_rate=non_response/100,
                effect_size=effect_size,
                alpha=alpha,
                power=power
            )
            
            results = calculator.calculate_sample(params)
            display_results(results)

def display_results(results: dict):
    """Interactive results visualization"""
    st.markdown("## 📊 Results Summary")
    
    # Key metrics cards
    cols = st.columns(3)
    metrics = [
        ("Base Sample (SRS)", results['base_sample_size']),
        ("Design Effect", results['design_effect']),
        ("Final EAs Needed", results['final_sample_size'])
    ]
    
    for col, (label, value) in zip(cols, metrics):
        with col:
            st.metric(label, value)
    
    # Visualization
    fig = px.bar(
        x=["Simple Random", "Cluster Adjusted", "With Non-Response"],
        y=[
            results['base_sample_size'],
            results['adjusted_sample_size'],
            results['final_sample_size']
        ],
        labels={"x": "Calculation Stage", "y": "Sample Size"},
        title="Sample Size Progression",
        color_discrete_sequence=["#4CAF50", "#FFC107", "#2196F3"]
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # DEFF explanation
    with st.expander("ℹ️ Design Effect Analysis"):
        st.markdown(f"""
        - **ICC**: {results['icc']} (similarity within EAs)
        - **Cluster Size**: {results['cluster_size']} households/EA
        - **Variance Inflation**: {results['design_effect']:.2f}x
        """)
        
        # ICC sensitivity analysis
        icc_range = [x/100 for x in range(1, 31)]
        deff_values = [1 + (results['cluster_size'] - 1) * icc for icc in icc_range]
        
        fig = px.line(
            x=icc_range, y=deff_values,
            title="Design Effect vs ICC",
            labels={"x": "ICC", "y": "Design Effect"}
        )
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()