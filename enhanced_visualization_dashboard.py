import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="Executive HR Analytics Dashboard",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS
def apply_custom_css():
    """Apply custom CSS styling"""
    css = """
    <style>
    .metric-card {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin: 5px 0;
    }
    
    .metric-label {
        font-size: 1rem;
        color: #7f8c8d;
        margin-bottom: 0;
    }
    
    .section-header {
        color: #2c3e50;
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
    }
    
    .section-header-icon {
        color: #16a085;
        margin-right: 8px;
    }
    
    .dashboard-title {
        text-align: center;
        padding: 10px;
        margin-bottom: 20px;
    }
    
    .dashboard-title h1 {
        color: #2c3e50;
        font-size: 1.8rem;
        margin: 0;
    }
    
    .dashboard-title p {
        color: #7f8c8d;
        font-size: 0.9rem;
        margin: 5px 0 0 0;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# Function to load data
def load_data(file_path):
    """Load data from Excel or CSV file"""
    try:
        if isinstance(file_path, str):
            if file_path.endswith('.csv'):
                return pd.read_csv(file_path)
            elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                return pd.read_excel(file_path)
            else:
                st.error(f"Unsupported file format: {file_path}")
                return None
        else:
            # Assume it's an uploaded file object
            file_name = getattr(file_path, 'name', '')
            if file_name.endswith('.csv'):
                return pd.read_csv(file_path)
            elif file_name.endswith('.xlsx') or file_name.endswith('.xls'):
                return pd.read_excel(file_path)
            else:
                st.error(f"Unsupported file format: {file_name}")
                return None
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

# Function to create a metric card
def metric_card(label, value, prefix="", suffix=""):
    """Create a styled metric card"""
    html = f"""
    <div class="metric-card">
        <p class="metric-label">{label}</p>
        <p class="metric-value">{prefix}{value}{suffix}</p>
    </div>
    """
    return html

# Function to create section header
def section_header(title, icon="📊"):
    """Create a styled section header with icon"""
    html = f"""
    <div class="section-header">
        <span class="section-header-icon">{icon}</span>
        {title}
    </div>
    """
    return html

# Function to detect department column
def detect_department_column(df):
    """Detect department column in dataframe"""
    if 'Department' in df.columns:
        return 'Department'
    elif 'Organizational Unit' in df.columns:
        return 'Organizational Unit'
    else:
        for col in df.columns:
            col_str = str(col).lower()
            if 'department' in col_str or 'dept' in col_str or 'org' in col_str or 'unit' in col_str:
                return col
    return None

# Function to detect job family column
def detect_job_family_column(df):
    """Detect job family column in dataframe"""
    if 'Job Family' in df.columns:
        return 'Job Family'
    else:
        for col in df.columns:
            col_str = str(col).lower()
            if 'job' in col_str and ('family' in col_str or 'role' in col_str or 'position' in col_str):
                return col
    return None

# Function to detect employee group column
def detect_employee_group_column(df):
    """Detect employee group column in dataframe"""
    if 'Employee Group' in df.columns:
        return 'Employee Group'
    else:
        for col in df.columns:
            col_str = str(col).lower()
            if ('employee' in col_str and 'group' in col_str) or 'employeegroup' in col_str or 'emp group' in col_str:
                return col
    return None

# Function to detect joining date column
def detect_joining_date_column(df):
    """Detect joining date column in dataframe"""
    if 'Joining Date' in df.columns:
        return 'Joining Date'
    else:
        for col in df.columns:
            col_str = str(col).lower()
            if ('join' in col_str or 'hire' in col_str or 'start' in col_str) and 'date' in col_str:
                return col
    return None

# Function to safely display a dataframe
def safe_dataframe_display(df):
    """Safely display a dataframe by converting problematic columns to strings"""
    try:
        # First attempt to display the original dataframe
        return st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.warning(f"Converting columns to string format for display compatibility: {str(e)}")
        # Create a copy to avoid modifying the original dataframe
        display_df = df.copy()
        
        # Convert all columns to strings to avoid PyArrow serialization issues
        for col in display_df.columns:
            try:
                display_df[col] = display_df[col].astype(str)
            except Exception as e:
                st.warning(f"Error converting column {col}: {str(e)}")
        
        # Try again with converted dataframe
        try:
            return st.dataframe(display_df, use_container_width=True)
        except Exception as e:
            st.error(f"Failed to display dataframe even after conversion: {str(e)}")
            st.info("Displaying first 5 rows as text instead:")
            st.text(str(display_df.head(5)))
            return None

# Function to create employees by department chart
def create_employees_by_department(df, dept_col):
    """Create horizontal bar chart showing employees by department"""
    if dept_col is None:
        return None
    
    try:
        # Count employees by department
        dept_counts = df[dept_col].value_counts().reset_index()
        dept_counts.columns = [dept_col, 'Count']
        
        # Calculate percentages
        total = dept_counts['Count'].sum()
        dept_counts['Percentage'] = (dept_counts['Count'] / total * 100).round(1)
        
        # Create text labels with count and percentage
        dept_counts['Label'] = dept_counts['Count'].astype(str) + ' (' + dept_counts['Percentage'].astype(str) + '%)'
        
        # Sort by count descending
        dept_counts = dept_counts.sort_values('Count', ascending=True)
        
        # Create horizontal bar chart
        fig = px.bar(
            dept_counts,
            y=dept_col,
            x='Count',
            orientation='h',
            text='Label',
            title=f'Employees by {dept_col}',
            height=300
        )
        
        # Improve layout
        fig.update_layout(
            margin=dict(l=0, r=0, t=30, b=0),
            title=dict(x=0.5, font=dict(size=14)),
            xaxis=dict(title=''),
            yaxis=dict(title='')
        )
        
        # Update traces
        fig.update_traces(
            textposition='outside',
            hovertemplate=f'<b>{dept_col}:</b> %{{y}}<br><b>Count:</b> %{{x}}<br><b>Percentage:</b> %{{customdata[0]}}%<extra></extra>',
            customdata=dept_counts[['Percentage']]
        )
        
        return fig
    except Exception as e:
        st.warning(f"Error creating department chart: {str(e)}")
        return None

# Function to create employee group split chart
def create_employee_group_split(df, emp_group_col):
    """Create donut chart showing employee group split"""
    if emp_group_col is None:
        return None
    
    try:
        # Count employees by group
        group_counts = df[emp_group_col].value_counts().reset_index()
        group_counts.columns = [emp_group_col, 'Count']
        
        # Calculate percentages
        total = group_counts['Count'].sum()
        group_counts['Percentage'] = (group_counts['Count'] / total * 100).round(1)
        
        # Create text labels with count and percentage
        group_counts['Label'] = group_counts[emp_group_col] + '<br>' + group_counts['Count'].astype(str) + ' (' + group_counts['Percentage'].astype(str) + '%)'
        
        # Create donut chart
        fig = px.pie(
            group_counts,
            names=emp_group_col,
            values='Count',
            title=f'{emp_group_col} Split',
            hole=0.4,
            height=300,
            custom_data=['Count', 'Percentage', 'Label']  # Include custom data for hover
        )
        
        # Improve layout
        fig.update_layout(
            margin=dict(l=0, r=0, t=30, b=0),
            title=dict(x=0.5, font=dict(size=14)),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            )
        )
        
        # Update traces to show both count and percentage
        fig.update_traces(
            texttemplate='%{label}<br>%{value} (%{percent})',
            textposition='inside',
            hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
        )
        
        return fig
    except Exception as e:
        st.warning(f"Error creating employee group chart: {str(e)}")
        return None

# Function to create talent distribution by job family chart
def create_talent_distribution(df, job_col):
    """Create horizontal bar chart showing talent distribution by job family"""
    if job_col is None:
        return None
    
    try:
        # Count employees by job family
        job_counts = df[job_col].value_counts().reset_index()
        job_counts.columns = [job_col, 'Count']
        
        # Calculate percentages
        total = job_counts['Count'].sum()
        job_counts['Percentage'] = (job_counts['Count'] / total * 100).round(1)
        
        # Create text labels with count and percentage
        job_counts['Label'] = job_counts['Count'].astype(str) + ' (' + job_counts['Percentage'].astype(str) + '%)'
        
        # Sort by count descending
        job_counts = job_counts.sort_values('Count', ascending=True)
        
        # Create horizontal bar chart
        fig = px.bar(
            job_counts,
            y=job_col,
            x='Count',
            orientation='h',
            text='Label',
            title=f'Headcount by {job_col}',
            height=400
        )
        
        # Improve layout
        fig.update_layout(
            margin=dict(l=0, r=0, t=30, b=0),
            title=dict(x=0.5, font=dict(size=14)),
            xaxis=dict(title=''),
            yaxis=dict(title='')
        )
        
        # Update traces
        fig.update_traces(
            textposition='outside',
            hovertemplate=f'<b>{job_col}:</b> %{{y}}<br><b>Count:</b> %{{x}}<br><b>Percentage:</b> %{{customdata[0]}}%<extra></extra>',
            customdata=job_counts[['Percentage']]
        )
        
        return fig
    except Exception as e:
        st.warning(f"Error creating job family chart: {str(e)}")
        return None

# Function to create tenure trend chart
def create_tenure_trend(df, joining_date_col):
    """Create line chart showing hiring trend over years"""
    if joining_date_col is None:
        return None
    
    try:
        # Convert joining date to datetime if not already
        if not pd.api.types.is_datetime64_any_dtype(df[joining_date_col]):
            df[joining_date_col] = pd.to_datetime(df[joining_date_col], errors='coerce')
        
        # Extract year and count hires by year
        df['Join Year'] = df[joining_date_col].dt.year
        hiring_trend = df.groupby('Join Year').size().reset_index(name='New Hires')
        
        # Create line chart
        fig = px.line(
            hiring_trend,
            x='Join Year',
            y='New Hires',
            markers=True,
            title='Hiring Trend Over Years',
            height=300
        )
        
        # Improve layout
        fig.update_layout(
            margin=dict(l=0, r=0, t=30, b=0),
            title=dict(x=0.5, font=dict(size=14)),
            xaxis=dict(title=''),
            yaxis=dict(title='')
        )
        
        # Update traces to show values on the chart
        fig.update_traces(
            texttemplate='%{y}',
            textposition='top center',
            hovertemplate='<b>Year:</b> %{x}<br><b>New Hires:</b> %{y}<extra></extra>'
        )
        
        return fig
    except Exception as e:
        st.warning(f"Error creating tenure trend chart: {str(e)}")
        return None

# Main function
def main():
    # Apply custom CSS
    apply_custom_css()
    
    # Sidebar for filters and options
    st.sidebar.title("🔎 Filter Employees")
    
    # Data upload
    st.sidebar.header("Dashboard Controls")
    st.sidebar.subheader("Upload HR Data")
    uploaded_file = st.sidebar.file_uploader("Drag and drop file here", type=["CSV", "XLSX", "XLS"], key="data_uploader")
    
    # Company name input
    company_name = st.sidebar.text_input("Company Name", "Your Company")

    # Load data
    if uploaded_file is not None:
        df = load_data(uploaded_file)
    else:
        st.warning("Please upload an HR data file to continue.")
        df = None

    # If data is loaded successfully
    if df is not None:
        # Pre-process dataframe to prevent PyArrow serialization errors
        try:
            # Make a copy to avoid modifying the original
            df_processed = df.copy()
            
            # Specifically handle the 'Pers.No.' column if it exists
            if 'Pers.No.' in df_processed.columns:
                st.sidebar.info("Found 'Pers.No.' column - converting to string type")
                df_processed['Pers.No.'] = df_processed['Pers.No.'].astype(str)
            
            # Check for any column with 'Pers' in the name
            for col in df_processed.columns:
                if 'Pers' in str(col):
                    st.sidebar.info(f"Found column '{col}' - converting to string type")
                    df_processed[col] = df_processed[col].astype(str)
            
            # Convert all column names to strings
            df_processed.columns = [str(col) for col in df_processed.columns]
            
            # Use the processed dataframe for all operations
            df = df_processed
            st.sidebar.success("Data pre-processing completed successfully")
        except Exception as e:
            st.sidebar.warning(f"Error during pre-processing: {str(e)}")
        
        # Display data loading success message
        st.sidebar.success(f"Data loaded successfully: {df.shape[0]} rows, {df.shape[1]} columns")
        
        # Show data types info in an expander
        with st.sidebar.expander("View Data Types Info"):
            # Convert dtypes to strings for display
            dtypes_df = pd.DataFrame(df.dtypes, columns=['Data Type'])
            dtypes_df['Data Type'] = dtypes_df['Data Type'].astype(str)
            st.dataframe(dtypes_df)
        
        # Detect columns
        dept_col = detect_department_column(df)
        job_col = detect_job_family_column(df)
        emp_group_col = detect_employee_group_column(df)
        joining_date_col = detect_joining_date_column(df)
        
        # Show detected columns in an expander
        with st.sidebar.expander("View Detected Columns"):
            st.write(f"Department Column: {dept_col}")
            st.write(f"Job Family Column: {job_col}")
            st.write(f"Employee Group Column: {emp_group_col}")
            st.write(f"Joining Date Column: {joining_date_col}")
        
        # Add filters based on detected columns
        filters_applied = False
        
        if dept_col:
            try:
                dept_options = sorted(df[dept_col].dropna().unique())
                selected_depts = st.sidebar.multiselect(f"{dept_col}", options=dept_options)
                if selected_depts:
                    df = df[df[dept_col].isin(selected_depts)]
                    filters_applied = True
            except Exception as e:
                st.sidebar.warning(f"Could not create filter for {dept_col}: {str(e)}")
        
        if job_col:
            try:
                job_options = sorted(df[job_col].dropna().unique())
                selected_jobs = st.sidebar.multiselect(f"{job_col}", options=job_options)
                if selected_jobs:
                    df = df[df[job_col].isin(selected_jobs)]
                    filters_applied = True
            except Exception as e:
                st.sidebar.warning(f"Could not create filter for {job_col}: {str(e)}")
        
        if emp_group_col:
            try:
                group_options = sorted(df[emp_group_col].dropna().unique())
                selected_groups = st.sidebar.multiselect(f"{emp_group_col}", options=group_options)
                if selected_groups:
                    df = df[df[emp_group_col].isin(selected_groups)]
                    filters_applied = True
            except Exception as e:
                st.sidebar.warning(f"Could not create filter for {emp_group_col}: {str(e)}")
        
        # Dashboard title
        st.markdown(f"""
        <div class="dashboard-title">
            <h1>Executive HR Analytics Dashboard</h1>
            <p>{company_name} • {datetime.now().strftime('%B %d, %Y')} • {len(df)} employees {' (filtered)' if filters_applied else ''}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Key HR Metrics
        st.markdown(section_header("🔑 Key HR Metrics"), unsafe_allow_html=True)
        
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        
        with metric_col1:
            st.markdown(metric_card("Total Employees", f"{len(df):,}"), unsafe_allow_html=True)
        
        with metric_col2:
            if dept_col:
                st.markdown(metric_card(f"Total {dept_col}s", f"{df[dept_col].nunique():,}"), unsafe_allow_html=True)
            else:
                st.markdown(metric_card("Departments", "N/A"), unsafe_allow_html=True)
        
        with metric_col3:
            if job_col:
                st.markdown(metric_card(f"Total {job_col}s", f"{df[job_col].nunique():,}"), unsafe_allow_html=True)
            else:
                st.markdown(metric_card("Job Families", "N/A"), unsafe_allow_html=True)
        
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Workforce Overview
        st.markdown(section_header("👥 Workforce Overview"), unsafe_allow_html=True)
        
        overview_col1, overview_col2 = st.columns(2)
        
        with overview_col1:
            if dept_col:
                dept_fig = create_employees_by_department(df, dept_col)
                if dept_fig:
                    st.plotly_chart(dept_fig, use_container_width=True, key="dept_overview")
            else:
                st.info("Department column not detected in the data.")
        
        with overview_col2:
            if emp_group_col:
                group_fig = create_employee_group_split(df, emp_group_col)
                if group_fig:
                    st.plotly_chart(group_fig, use_container_width=True, key="group_split")
            else:
                st.info("Employee Group column not detected in the data.")
        
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Talent Distribution
        st.markdown(section_header("🎯 Talent Distribution by Job Family"), unsafe_allow_html=True)
        
        if job_col:
            job_fig = create_talent_distribution(df, job_col)
            if job_fig:
                st.plotly_chart(job_fig, use_container_width=True, key="job_dist")
        else:
            st.info("Job Family column not detected in the data.")
        
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Tenure Trend
        st.markdown(section_header("📅 Tenure Trend"), unsafe_allow_html=True)
        
        if joining_date_col:
            tenure_fig = create_tenure_trend(df, joining_date_col)
            if tenure_fig:
                st.plotly_chart(tenure_fig, use_container_width=True, key="tenure_trend")
        else:
            st.info("Joining Date column not detected in the data.")
        
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Detailed Employee Table
        st.markdown(section_header("📋 Detailed Employee Table"), unsafe_allow_html=True)
        
        # Display the dataframe using the safe display function
        safe_dataframe_display(df)
        
        # Footer
        st.markdown("<hr>", unsafe_allow_html=True)
        st.caption("🚀 Built to showcase HR insights that fuel performance & promotion opportunities ✨")
    
    else:
        st.info("Please upload an HR data file to view the dashboard.")

if __name__ == "__main__":
    main()
