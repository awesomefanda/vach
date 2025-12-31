"""
Vach Web Interface
Streamlit-based UI for viewing tracked projects
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from src.database.operations import DatabaseOperations
from src.database.models import Project, ProjectUpdate
from config.settings import TARGET_CITY, PROJECT_TYPES

# Page config
st.set_page_config(
    page_title=f"Vach - {TARGET_CITY} Project Tracker",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .stat-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .project-card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=60)
def load_statistics():
    """Load database statistics"""
    db = DatabaseOperations()
    return db.get_statistics()


@st.cache_data(ttl=60)
def load_projects(filters=None):
    """Load projects from database"""
    db = DatabaseOperations()
    return db.get_all_projects(filters=filters)


def display_header():
    """Display page header"""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f'<h1 class="main-header">🔍 Vach</h1>', unsafe_allow_html=True)
        st.markdown(f"### Tracking {TARGET_CITY} Civic Projects")
        st.markdown("*Automated monitoring of public promises and project progress*")
    
    with col2:
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()


def display_stats():
    """Display key statistics"""
    stats = load_statistics()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📰 Total Articles",
            value=stats.get('total_articles', 0),
            delta=f"{stats.get('unprocessed_articles', 0)} unprocessed"
        )
    
    with col2:
        st.metric(
            label="📋 Total Projects",
            value=stats.get('total_projects', 0)
        )
    
    with col3:
        completed = stats.get('projects_by_status', {}).get('completed', 0)
        st.metric(
            label="✅ Completed",
            value=completed
        )
    
    with col4:
        in_progress = stats.get('projects_by_status', {}).get('in_progress', 0)
        st.metric(
            label="🚧 In Progress",
            value=in_progress
        )


def display_status_chart(stats):
    """Display project status distribution"""
    status_data = stats.get('projects_by_status', {})
    
    if not status_data or sum(status_data.values()) == 0:
        st.info("No projects data available yet")
        return
    
    # Filter out zero values
    status_data = {k: v for k, v in status_data.items() if v > 0}
    
    df = pd.DataFrame(list(status_data.items()), columns=['Status', 'Count'])
    
    # Create pie chart
    fig = px.pie(
        df,
        values='Count',
        names='Status',
        title='Projects by Status',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    st.plotly_chart(fig, use_container_width=True)


def display_sidebar_filters():
    """Display sidebar filters"""
    st.sidebar.header("🔍 Filters")
    
    # Load projects for filter options
    all_projects = load_projects()
    
    if not all_projects:
        st.sidebar.info("No projects to display yet. Run the scrapers and processor first.")
        return None
    
    # Extract unique values
    locations = list(set(p.location for p in all_projects if p.location))
    types = PROJECT_TYPES
    statuses = ['announced', 'approved', 'in_progress', 'delayed', 'completed', 'cancelled']
    
    # Filters
    selected_location = st.sidebar.multiselect(
        "📍 Location",
        options=sorted(locations),
        default=[]
    )
    
    selected_type = st.sidebar.multiselect(
        "🏗️ Project Type",
        options=types,
        default=[]
    )
    
    selected_status = st.sidebar.multiselect(
        "📊 Status",
        options=statuses,
        default=[]
    )
    
    # Search
    search_term = st.sidebar.text_input("🔎 Search projects", "")
    
    return {
        'location': selected_location,
        'type': selected_type,
        'status': selected_status,
        'search': search_term
    }


def filter_projects(projects, filters):
    """Apply filters to projects"""
    if not filters:
        return projects
    
    filtered = projects
    
    # Location filter
    if filters['location']:
        filtered = [p for p in filtered if p.location in filters['location']]
    
    # Type filter
    if filters['type']:
        filtered = [p for p in filtered if p.project_type in filters['type']]
    
    # Status filter
    if filters['status']:
        filtered = [p for p in filtered if p.status in filters['status']]
    
    # Search filter
    if filters['search']:
        search_lower = filters['search'].lower()
        filtered = [
            p for p in filtered
            if search_lower in (p.project_name or '').lower()
            or search_lower in (p.description or '').lower()
            or search_lower in (p.location or '').lower()
        ]
    
    return filtered


def display_project_card(project):
    """Display a single project card"""
    # Status emoji
    status_emoji = {
        'announced': '📢',
        'approved': '✅',
        'in_progress': '🚧',
        'delayed': '⏰',
        'completed': '✔️',
        'cancelled': '❌'
    }
    
    emoji = status_emoji.get(project.status, '📋')
    
    with st.expander(f"{emoji} **{project.project_name}** - {project.location or 'Location TBD'}"):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"**Description:** {project.description or 'No description available'}")
            
            if project.official:
                st.markdown(f"**Official:** {project.official}")
        
        with col2:
            st.markdown(f"**Status:** `{project.status.upper()}`")
            st.markdown(f"**Type:** {project.project_type or 'N/A'}")
            
            if project.budget:
                st.markdown(f"**Budget:** {project.budget}")
            
            if project.promised_date:
                st.markdown(f"**Promised:** {project.promised_date}")
        
        # Timeline
        db = DatabaseOperations()
        # Get updates manually since we need the session
        from src.database.models import get_session, close_session
        session = get_session()
        try:
            updates = session.query(ProjectUpdate).filter_by(
                project_id=project.id
            ).order_by(ProjectUpdate.update_date).all()
            
            if updates:
                st.markdown("**📅 Timeline:**")
                for update in updates:
                    date_str = update.update_date.strftime('%Y-%m-%d')
                    st.markdown(
                        f"- **{date_str}**: {update.status} "
                        f"([source]({update.source_url}))"
                    )
                    if update.notes:
                        st.markdown(f"  *{update.notes}*")
        finally:
            close_session(session)
        
        # Metadata
        st.markdown("---")
        st.caption(
            f"First seen: {project.first_seen.strftime('%Y-%m-%d')} | "
            f"Last updated: {project.last_updated.strftime('%Y-%m-%d')} | "
            f"Confidence: {project.confidence_score:.0%}"
        )


def display_projects(projects):
    """Display list of projects"""
    if not projects:
        st.info("No projects match your filters")
        return
    
    st.markdown(f"### Showing {len(projects)} projects")
    
    # Sort options
    sort_col, order_col = st.columns([3, 1])
    
    with sort_col:
        sort_by = st.selectbox(
            "Sort by",
            options=['last_updated', 'first_seen', 'project_name', 'status'],
            format_func=lambda x: x.replace('_', ' ').title()
        )
    
    with order_col:
        order = st.radio("Order", options=['Descending', 'Ascending'], horizontal=True)
    
    # Sort projects
    reverse = (order == 'Descending')
    sorted_projects = sorted(
        projects,
        key=lambda p: getattr(p, sort_by) if hasattr(p, sort_by) else '',
        reverse=reverse
    )
    
    # Display projects
    for project in sorted_projects:
        display_project_card(project)


def main():
    """Main application"""
    # Header
    display_header()
    
    st.markdown("---")
    
    # Stats
    display_stats()
    
    st.markdown("---")
    
    # Sidebar filters
    filters = display_sidebar_filters()
    
    # Main content area
    tab1, tab2, tab3 = st.tabs(["📋 Projects", "📊 Analytics", "ℹ️ About"])
    
    with tab1:
        # Load and filter projects
        all_projects = load_projects()
        
        if filters:
            projects = filter_projects(all_projects, filters)
        else:
            projects = all_projects
        
        # Display projects
        display_projects(projects)
    
    with tab2:
        st.subheader("📊 Analytics")
        
        stats = load_statistics()
        
        col1, col2 = st.columns(2)
        
        with col1:
            display_status_chart(stats)
        
        with col2:
            # Project types distribution
            if all_projects:
                type_counts = {}
                for p in all_projects:
                    ptype = p.project_type or 'unknown'
                    type_counts[ptype] = type_counts.get(ptype, 0) + 1
                
                df_types = pd.DataFrame(
                    list(type_counts.items()),
                    columns=['Type', 'Count']
                )
                
                fig = px.bar(
                    df_types,
                    x='Type',
                    y='Count',
                    title='Projects by Type',
                    color='Count',
                    color_continuous_scale='Blues'
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.subheader("ℹ️ About Vach")
        
        st.markdown("""
        **Vach** is an automated civic accountability tracker that monitors government projects
        and promises in San Jose, California.
        
        ### How it works:
        
        1. **📰 Data Collection**: Automatically scrapes news articles and government websites
        2. **🤖 AI Processing**: Uses local LLM to extract project information
        3. **📊 Tracking**: Monitors project status changes over time
        4. **🔍 Transparency**: Makes information easily searchable and accessible
        
        ### Data Sources:
        - Local news outlets (Mercury News, San Jose Spotlight)
        - San Jose government press releases
        - San Jose Open Data portal
        - City Council meeting records
        
        ### Project Status:
        This is a prototype system. Data is collected and processed automatically,
        but may contain errors. Always verify important information with official sources.
        
        ### Feedback:
        Found an issue? Have suggestions? Please provide feedback to help improve Vach.
        """)
        
        # System info
        st.markdown("---")
        st.markdown("### 🔧 System Information")
        
        stats = load_statistics()
        st.json({
            "Total Articles": stats.get('total_articles', 0),
            "Processed Articles": stats.get('processed_articles', 0),
            "Total Projects": stats.get('total_projects', 0),
            "Last Updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })


if __name__ == "__main__":
    main()