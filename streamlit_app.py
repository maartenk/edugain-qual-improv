#!/usr/bin/env python3
"""
Streamlit Web Dashboard for eduGAIN Privacy Statement and Security Contact Analysis

This web application provides an interactive dashboard for analyzing eduGAIN metadata
to identify entities missing privacy statement URLs and/or security contacts.

Usage:
    streamlit run streamlit_app.py

Features:
- Interactive data visualization with charts and tables
- Federation-level analysis and filtering
- Real-time data processing with caching
- Export capabilities for CSV data
- Responsive dashboard design
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import io
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Import functions from the existing privacy_security_analysis module
from privacy_security_analysis import (
    get_metadata,
    get_federation_mapping,
    analyze_privacy_security,
    parse_metadata,
    map_registration_authority,
)


def convert_entities_to_dicts(entities_list: List[List[str]]) -> List[Dict]:
    """Convert CSV-style entity list to dictionary format for Streamlit."""
    entities = []
    for entity_row in entities_list:
        # Expected format: [federation_name, ent_type, orgname, ent_id, has_privacy_yes_no, privacy_url, has_security_yes_no]
        entity = {
            "federation_name": entity_row[0],
            "entity_type": entity_row[1],
            "organization_name": entity_row[2],
            "entity_id": entity_row[3],
            "has_privacy_statement": entity_row[4] == "Yes",
            "privacy_statement_url": entity_row[5] if entity_row[5] else None,
            "has_security_contact": entity_row[6] == "Yes",
        }
        entities.append(entity)
    return entities


@st.cache_data(ttl=43200)  # Cache for 12 hours (same as metadata cache)
def load_and_analyze_data(
    use_local_file: bool = False, local_file_path: str = None, custom_url: str = None
) -> Tuple[List[Dict], Dict[str, str], Dict]:
    """Load and analyze eduGAIN metadata with caching."""
    try:
        # Get federation mapping
        federation_mapping = get_federation_mapping()

        # Get metadata and parse to XML Element
        if use_local_file and local_file_path:
            root = parse_metadata(None, local_file_path)
        else:
            xml_content = get_metadata(
                custom_url or "https://mds.edugain.org/edugain-v2.xml"
            )
            root = parse_metadata(xml_content)

        # Analyze the data
        entities_list, stats, federation_stats = analyze_privacy_security(
            root, federation_mapping
        )

        # Convert to dictionary format for Streamlit
        entities = convert_entities_to_dicts(entities_list)

        # Use the stats returned by analyze_privacy_security
        summary_stats = {
            "total_entities": stats["total_entities"],
            "total_sps": stats["total_sps"],
            "total_idps": stats["total_idps"],
            "sps_with_privacy": stats["sps_has_privacy"],
            "sps_without_privacy": stats["sps_missing_privacy"],
            "sps_with_security": stats["sps_has_security"],
            "idps_with_security": stats["idps_has_security"],
            "sps_with_both": stats["sps_has_both"],
            "sps_missing_both": stats["sps_missing_both"],
        }

        return entities, federation_mapping, summary_stats

    except Exception as e:
        st.error(f"Error loading data: {e}")
        return [], {}, {}


def create_summary_charts(stats: Dict, entities: List[Dict]) -> None:
    """Create summary charts for the dashboard."""

    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Entities", f"{stats['total_entities']:,}")

    with col2:
        st.metric("Service Providers", f"{stats['total_sps']:,}")

    with col3:
        st.metric("Identity Providers", f"{stats['total_idps']:,}")

    with col4:
        if stats["total_sps"] > 0:
            privacy_pct = (stats["sps_with_privacy"] / stats["total_sps"]) * 100
            st.metric("SPs with Privacy", f"{privacy_pct:.1f}%")

    # Privacy and Security Coverage Charts
    col1, col2 = st.columns(2)

    with col1:
        # Privacy Statement Coverage (SPs only)
        if stats["total_sps"] > 0:
            privacy_data = {
                "Status": ["With Privacy Statement", "Missing Privacy Statement"],
                "Count": [stats["sps_with_privacy"], stats["sps_without_privacy"]],
            }
            fig_privacy = px.pie(
                privacy_data,
                values="Count",
                names="Status",
                title="Service Provider Privacy Statement Coverage",
                color_discrete_map={
                    "With Privacy Statement": "#2E8B57",
                    "Missing Privacy Statement": "#DC143C",
                },
            )
            st.plotly_chart(fig_privacy, use_container_width=True)

    with col2:
        # Security Contact Coverage
        if stats["total_sps"] > 0 and stats["total_idps"] > 0:
            security_data = {
                "Entity Type": [
                    "SPs with Security",
                    "SPs without Security",
                    "IdPs with Security",
                    "IdPs without Security",
                ],
                "Count": [
                    stats["sps_with_security"],
                    stats["total_sps"] - stats["sps_with_security"],
                    stats["idps_with_security"],
                    stats["total_idps"] - stats["idps_with_security"],
                ],
            }
            fig_security = px.bar(
                security_data,
                x="Entity Type",
                y="Count",
                title="Security Contact Coverage by Entity Type",
                color="Entity Type",
                color_discrete_map={
                    "SPs with Security": "#2E8B57",
                    "SPs without Security": "#DC143C",
                    "IdPs with Security": "#4682B4",
                    "IdPs without Security": "#FF6347",
                },
            )
            st.plotly_chart(fig_security, use_container_width=True)


def create_federation_analysis(entities: List[Dict]) -> None:
    """Create federation-level analysis charts."""
    st.subheader("Federation Analysis")

    # Group entities by federation
    federation_stats = {}

    for entity in entities:
        fed_name = entity["federation_name"]
        entity_type = entity["entity_type"]

        if fed_name not in federation_stats:
            federation_stats[fed_name] = {
                "total_entities": 0,
                "sps": 0,
                "idps": 0,
                "sps_with_privacy": 0,
                "sps_with_security": 0,
                "idps_with_security": 0,
            }

        federation_stats[fed_name]["total_entities"] += 1

        if entity_type == "SP":
            federation_stats[fed_name]["sps"] += 1
            if entity["has_privacy_statement"]:
                federation_stats[fed_name]["sps_with_privacy"] += 1
            if entity["has_security_contact"]:
                federation_stats[fed_name]["sps_with_security"] += 1
        elif entity_type == "IdP":
            federation_stats[fed_name]["idps"] += 1
            if entity["has_security_contact"]:
                federation_stats[fed_name]["idps_with_security"] += 1

    # Convert to DataFrame for easier plotting
    fed_data = []
    for fed_name, stats in federation_stats.items():
        if stats["sps"] > 0:  # Only include federations with SPs for privacy stats
            privacy_pct = (stats["sps_with_privacy"] / stats["sps"]) * 100
        else:
            privacy_pct = 0

        fed_data.append(
            {
                "Federation": fed_name,
                "Total Entities": stats["total_entities"],
                "Service Providers": stats["sps"],
                "Identity Providers": stats["idps"],
                "SP Privacy %": privacy_pct,
                "SPs with Security": stats["sps_with_security"],
                "IdPs with Security": stats["idps_with_security"],
            }
        )

    df_fed = pd.DataFrame(fed_data)
    df_fed = df_fed.sort_values("Total Entities", ascending=False)

    # Top federations by entity count
    col1, col2 = st.columns(2)

    with col1:
        top_10_fed = df_fed.head(10)
        fig_fed_size = px.bar(
            top_10_fed,
            x="Total Entities",
            y="Federation",
            orientation="h",
            title="Top 10 Federations by Entity Count",
            color="Total Entities",
            color_continuous_scale="Blues",
        )
        fig_fed_size.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_fed_size, use_container_width=True)

    with col2:
        # Privacy statement compliance by federation (top 10 by SP count)
        top_sp_fed = df_fed[df_fed["Service Providers"] > 0].nlargest(
            10, "Service Providers"
        )
        fig_privacy_fed = px.bar(
            top_sp_fed,
            x="SP Privacy %",
            y="Federation",
            orientation="h",
            title="Privacy Statement Coverage - Top 10 SP Federations",
            color="SP Privacy %",
            color_continuous_scale="RdYlGn",
        )
        fig_privacy_fed.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_privacy_fed, use_container_width=True)

    # Federation details table
    st.subheader("Federation Details")

    # Add filtering options
    col1, col2 = st.columns(2)
    with col1:
        min_entities = st.slider("Minimum entities per federation", 1, 100, 10)
    with col2:
        entity_type_filter = st.selectbox(
            "Filter by entity type",
            ["All", "Service Providers Only", "Identity Providers Only"],
        )

    # Apply filters
    filtered_df = df_fed[df_fed["Total Entities"] >= min_entities]

    if entity_type_filter == "Service Providers Only":
        filtered_df = filtered_df[filtered_df["Service Providers"] > 0]
    elif entity_type_filter == "Identity Providers Only":
        filtered_df = filtered_df[filtered_df["Identity Providers"] > 0]

    # Display table
    st.dataframe(filtered_df.round(1), use_container_width=True, hide_index=True)


def create_entity_browser(entities: List[Dict]) -> None:
    """Create an interactive entity browser."""
    st.subheader("Entity Browser")

    # Convert to DataFrame
    df = pd.DataFrame(entities)

    # Filtering options
    col1, col2, col3 = st.columns(3)

    with col1:
        entity_types = st.multiselect(
            "Entity Types",
            options=df["entity_type"].unique(),
            default=df["entity_type"].unique(),
        )

    with col2:
        federations = st.multiselect(
            "Federations", options=sorted(df["federation_name"].unique()), default=[]
        )

    with col3:
        status_filter = st.selectbox(
            "Status Filter",
            [
                "All",
                "Missing Privacy Statement",
                "Missing Security Contact",
                "Missing Both",
            ],
        )

    # Apply filters
    filtered_df = df[df["entity_type"].isin(entity_types)]

    if federations:
        filtered_df = filtered_df[filtered_df["federation_name"].isin(federations)]

    if status_filter == "Missing Privacy Statement":
        filtered_df = filtered_df[
            (filtered_df["entity_type"] == "SP")
            & (~filtered_df["has_privacy_statement"])
        ]
    elif status_filter == "Missing Security Contact":
        filtered_df = filtered_df[~filtered_df["has_security_contact"]]
    elif status_filter == "Missing Both":
        filtered_df = filtered_df[
            (filtered_df["entity_type"] == "SP")
            & (~filtered_df["has_privacy_statement"])
            & (~filtered_df["has_security_contact"])
        ]

    # Display results
    st.write(f"Showing {len(filtered_df)} entities")

    # Prepare display DataFrame
    display_df = filtered_df[
        [
            "federation_name",
            "entity_type",
            "organization_name",
            "entity_id",
            "has_privacy_statement",
            "privacy_statement_url",
            "has_security_contact",
        ]
    ].copy()

    display_df.columns = [
        "Federation",
        "Type",
        "Organization",
        "Entity ID",
        "Has Privacy",
        "Privacy URL",
        "Has Security",
    ]

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # Export button
    if not filtered_df.empty:
        csv_buffer = io.StringIO()
        filtered_df.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()

        st.download_button(
            label="Download filtered data as CSV",
            data=csv_data,
            file_name=f"edugain_entities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="eduGAIN Privacy & Security Analysis",
        page_icon="🔒",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("🔒 eduGAIN Privacy & Security Analysis Dashboard")
    st.markdown(
        "Interactive analysis of privacy statements and security contacts in eduGAIN metadata"
    )

    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")

        data_source = st.radio(
            "Data Source",
            ["eduGAIN Metadata URL (Default)", "Custom URL", "Local File"],
        )

        use_local_file = False
        local_file_path = None
        custom_url = None

        if data_source == "Local File":
            uploaded_file = st.file_uploader(
                "Upload XML metadata file",
                type=["xml"],
                help="Upload a local eduGAIN metadata XML file",
            )
            if uploaded_file:
                # Save uploaded file temporarily
                with open("/tmp/uploaded_metadata.xml", "wb") as f:
                    f.write(uploaded_file.getvalue())
                use_local_file = True
                local_file_path = "/tmp/uploaded_metadata.xml"

        elif data_source == "Custom URL":
            custom_url = st.text_input(
                "Custom metadata URL", placeholder="https://example.com/metadata.xml"
            )

        st.markdown("---")
        st.markdown("### About")
        st.markdown(
            """
        This dashboard analyzes eduGAIN federation metadata to identify entities
        missing privacy statements and/or security contacts.

        - **Privacy statements**: Analyzed for Service Providers only
        - **Security contacts**: Analyzed for both SPs and IdPs
        - **Data**: Cached for 12 hours for performance
        """
        )

    # Load and analyze data
    with st.spinner("Loading and analyzing eduGAIN metadata..."):
        entities, federation_mapping, stats = load_and_analyze_data(
            use_local_file=use_local_file,
            local_file_path=local_file_path,
            custom_url=custom_url,
        )

    if not entities:
        st.error("No data available. Please check your configuration and try again.")
        return

    # Main dashboard tabs
    tab1, tab2, tab3 = st.tabs(
        ["📊 Overview", "🌐 Federation Analysis", "🔍 Entity Browser"]
    )

    with tab1:
        st.header("Overview")
        create_summary_charts(stats, entities)

        # Additional insights
        st.subheader("Key Insights")
        col1, col2 = st.columns(2)

        with col1:
            if stats["total_sps"] > 0:
                privacy_pct = (stats["sps_with_privacy"] / stats["total_sps"]) * 100
                st.info(
                    f"**Privacy Statement Coverage**: {privacy_pct:.1f}% of Service Providers have privacy statements"
                )

                security_sp_pct = (
                    stats["sps_with_security"] / stats["total_sps"]
                ) * 100
                st.info(
                    f"**SP Security Coverage**: {security_sp_pct:.1f}% of Service Providers have security contacts"
                )

        with col2:
            if stats["total_idps"] > 0:
                security_idp_pct = (
                    stats["idps_with_security"] / stats["total_idps"]
                ) * 100
                st.info(
                    f"**IdP Security Coverage**: {security_idp_pct:.1f}% of Identity Providers have security contacts"
                )

            if stats["total_sps"] > 0:
                both_pct = (stats["sps_with_both"] / stats["total_sps"]) * 100
                st.info(
                    f"**Complete Coverage**: {both_pct:.1f}% of Service Providers have both privacy and security"
                )

    with tab2:
        create_federation_analysis(entities)

    with tab3:
        create_entity_browser(entities)

    # Footer
    st.markdown("---")
    st.markdown(
        "*Data sourced from eduGAIN metadata aggregate. Dashboard updates every 12 hours.*"
    )


if __name__ == "__main__":
    main()
