# complaint_app.py
import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import uuid

# Hide Streamlit style elements
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stActionButton > button[title="Open source on GitHub"] {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Constants
COMPLAINT_SHEET_COLUMNS = [
    "Ticket ID",
    "Raised By (Employee Name)",
    "Raised By (Employee Code)",
    "Raised By (Designation)",
    "Raised By (Email)",
    "Raised By (Phone)",
    "Concerned Person",
    "Concerned Person Code",
    "Concerned Person Designation",
    "Category",
    "Subject",
    "Details",
    "Status",
    "Date Raised",
    "Time Raised",
    "Resolution Notes",
    "Date Resolved",
    "Priority"
]

# Categories and priorities
COMPLAINT_CATEGORIES = [
    "Expense", "Salary", "Complaint", "Product Issues", 
    "Product Damage", "Product Missing", "Product Delivery", 
    "HR", "Attendance", "Facilities", "IT Support", "Other"
]

PRIORITY_LEVELS = ["Low", "Medium", "High", "Critical"]

# Establish Google Sheets connection
conn = st.connection("gsheets", type=GSheetsConnection)

# Load employee data
Person = pd.read_csv('Invoice - Person.csv')

def generate_ticket_id():
    return f"TKT-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"

def log_complaint_to_gsheet(conn, complaint_data):
    try:
        existing_data = conn.read(worksheet="Complaints", usecols=list(range(len(COMPLAINT_SHEET_COLUMNS))), ttl=5)
        existing_data = existing_data.dropna(how="all")
        updated_data = pd.concat([existing_data, complaint_data], ignore_index=True)
        conn.update(worksheet="Complaints", data=updated_data)
        return True, None
    except Exception as e:
        return False, str(e)

def authenticate_employee(employee_name, passkey):
    try:
        employee_code = Person[Person['Employee Name'] == employee_name]['Employee Code'].values[0]
        return str(passkey) == str(employee_code)
    except:
        return False

def raise_complaint_page(employee_name, employee_code, designation):
    st.title("Raise Ticket")
    
    with st.form("complaint_form"):
        # Employee contact info
        col1, col2 = st.columns(2)
        with col1:
            employee_email = st.text_input(
                "Your Email*",
                placeholder="your.email@company.com",
                help="Please provide your contact email"
            )
        with col2:
            employee_phone = st.text_input(
                "Your Phone Number*",
                placeholder="9876543210",
                help="Please provide your contact number"
            )
        
        # Concerned person selection
        concerned_person = st.selectbox(
            "Concerned Person*",
            Person['Employee Name'].tolist(),
            help="Select the person/department you're raising this complaint about"
        )
        
        # Get concerned person details
        concerned_details = Person[Person['Employee Name'] == concerned_person].iloc[0]
        
        # Complaint details
        col1, col2 = st.columns(2)
        with col1:
            category = st.selectbox(
                "Departments",
                COMPLAINT_CATEGORIES,
                help="Select the most relevant category for your complaint"
            )
        with col2:
            priority = st.selectbox(
                "Priority*",
                PRIORITY_LEVELS,
                index=1,  # Default to Medium
                help="How urgent is this issue?"
            )
        
        subject = st.text_input(
            "Subject*",
            max_chars=100,
            placeholder="Brief description of your Ticket",
            help="Keep it concise but descriptive"
        )
        
        details = st.text_area(
            "Details*",
            height=200,
            placeholder="Please provide detailed information about your Ticket",
            help="Include all relevant details to help resolve your issue quickly"
        )
        
        st.markdown("<small>*Required fields</small>", unsafe_allow_html=True)
        
        submitted = st.form_submit_button("Submit Ticket")
        
        if submitted:
            if not subject or not details or not employee_email or not employee_phone:
                st.error("Please fill in all required fields (marked with *)")
            elif not employee_email.strip() or "@" not in employee_email:
                st.error("Please enter a valid email address")
            elif not employee_phone.strip().isdigit() or len(employee_phone.strip()) < 10:
                st.error("Please enter a valid 10-digit phone number")
            else:
                with st.spinner("Submitting your Ticket"):
                    ticket_id = generate_ticket_id()
                    current_date = datetime.now().strftime("%d-%m-%Y")
                    current_time = datetime.now().strftime("%H:%M:%S")
                    
                    complaint_data = {
                        "Ticket ID": ticket_id,
                        "Raised By (Employee Name)": employee_name,
                        "Raised By (Employee Code)": employee_code,
                        "Raised By (Designation)": designation,
                        "Raised By (Email)": employee_email.strip(),
                        "Raised By (Phone)": employee_phone.strip(),
                        "Concerned Person": concerned_person,
                        "Concerned Person Code": concerned_details['Employee Code'],
                        "Concerned Person Designation": concerned_details['Designation'],
                        "Category": category,
                        "Subject": subject,
                        "Details": details,
                        "Status": "Open",
                        "Date Raised": current_date,
                        "Time Raised": current_time,
                        "Resolution Notes": "",
                        "Date Resolved": "",
                        "Priority": priority
                    }
                    
                    # Convert to DataFrame
                    complaint_df = pd.DataFrame([complaint_data])
                    
                    # Log to Google Sheets
                    success, error = log_complaint_to_gsheet(conn, complaint_df)
                    
                    if success:
                        st.success(f"""
                        Complaint submitted successfully!
                        
                        **Ticket ID:** {ticket_id}
                        **Priority:** {priority}
                        """)
                        st.balloons()
                    else:
                        st.error(f"Failed to submit complaint: {error}")

def view_complaints_page(employee_name):
    st.title("Previous Tickets")
    
    try:
        # Read complaints data
        complaints_data = conn.read(worksheet="Complaints", usecols=list(range(len(COMPLAINT_SHEET_COLUMNS))), ttl=5)
        complaints_data = complaints_data.dropna(how="all")
        
        if complaints_data.empty:
            st.info("No Tickets found in the system.")
            return
            
        # Filter for current employee
        my_complaints = complaints_data[
            complaints_data['Raised By (Employee Name)'] == employee_name
        ].sort_values(by="Date Raised", ascending=False)
        
        if my_complaints.empty:
            st.info("You haven't raised any complaints yet.")
            return
            
        # Display stats
        open_count = len(my_complaints[my_complaints['Status'] == "Open"])
        resolved_count = len(my_complaints[my_complaints['Status'] == "Resolved"])
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Complaints", len(my_complaints))
        col2.metric("Open", open_count)
        col3.metric("Resolved", resolved_count)
        
        # Filter options
        st.subheader("Filter Complaints")
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.selectbox(
                "Status",
                ["All", "Open", "Resolved"],
                key="status_filter"
            )
        with col2:
            priority_filter = st.selectbox(
                "Priority",
                ["All"] + PRIORITY_LEVELS,
                key="priority_filter"
            )
        with col3:
            category_filter = st.selectbox(
                "Category",
                ["All"] + COMPLAINT_CATEGORIES,
                key="category_filter"
            )
        
        # Apply filters
        filtered_complaints = my_complaints.copy()
        if status_filter != "All":
            filtered_complaints = filtered_complaints[filtered_complaints['Status'] == status_filter]
        if priority_filter != "All":
            filtered_complaints = filtered_complaints[filtered_complaints['Priority'] == priority_filter]
        if category_filter != "All":
            filtered_complaints = filtered_complaints[filtered_complaints['Category'] == category_filter]
        
        # Display complaints
        for _, row in filtered_complaints.iterrows():
            with st.expander(f"{row['Subject']} - {row['Status']} ({row['Priority']})"):
                # Header with status and priority
                status_color = "red" if row['Status'] == "Open" else "green"
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>Ticket ID:</strong> {row['Ticket ID']}<br>
                        <strong>Date Raised:</strong> {row['Date Raised']} at {row['Time Raised']}
                    </div>
                    <div style="color: {status_color}; font-weight: bold;">
                        {row['Status']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                st.write("---")
                
                # Main content
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Your Contact Email:** {row['Raised By (Email)']}")
                    st.write(f"**Your Phone Number:** {row['Raised By (Phone)']}")
                    st.write(f"**Category:** {row['Category']}")
                with col2:
                    st.write(f"**Concerned Person:** {row['Concerned Person']} ({row['Concerned Person Designation']})")
                    st.write(f"**Priority:** {row['Priority']}")
                    if row['Date Resolved']:
                        st.write(f"**Date Resolved:** {row['Date Resolved']}")
                
                st.write("---")
                st.write("**Details:**")
                st.write(row['Details'])
                
                # Resolution notes if resolved
                if row['Status'] == "Resolved" and row['Resolution Notes']:
                    st.write("---")
                    st.write("**Resolution Notes:**")
                    st.write(row['Resolution Notes'])
        
        # Download option
        if not filtered_complaints.empty:
            csv = filtered_complaints.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Download Filtered Complaints",
                csv,
                "my_complaints.csv",
                "text/csv",
                key='download-complaints-csv'
            )
            
    except Exception as e:
        st.error(f"Error retrieving complaints: {str(e)}")

def main():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'employee_name' not in st.session_state:
        st.session_state.employee_name = None
    if 'employee_code' not in st.session_state:
        st.session_state.employee_code = None
    if 'designation' not in st.session_state:
        st.session_state.designation = None

    if not st.session_state.authenticated:
        st.title("Ticket System - Login")
        
        employee_names = Person['Employee Name'].tolist()
        employee_name = st.selectbox("Select Your Name", employee_names, key="employee_select")
        passkey = st.text_input("Password", type="password", key="passkey_input")
        
        if st.button("Log in", key="login_button"):
            if authenticate_employee(employee_name, passkey):
                st.session_state.authenticated = True
                st.session_state.employee_name = employee_name
                st.session_state.employee_code = Person[Person['Employee Name'] == employee_name]['Employee Code'].values[0]
                st.session_state.designation = Person[Person['Employee Name'] == employee_name]['Designation'].values[0]
                st.rerun()
            else:
                st.error("Invalid Employee Code. Please try again.")
    else:
        st.sidebar.title(f"Welcome, {st.session_state.employee_name}")
        st.sidebar.write(f"Designation: {st.session_state.designation}")
        st.sidebar.write(f"Employee Code: {st.session_state.employee_code}")
        
        if st.sidebar.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.employee_name = None
            st.session_state.employee_code = None
            st.session_state.designation = None
            st.rerun()
        
        tab1, tab2 = st.tabs(["Raise Ticket", "Previous Ticket"])
        with tab1:
            raise_complaint_page(
                st.session_state.employee_name,
                st.session_state.employee_code,
                st.session_state.designation
            )
        with tab2:
            view_complaints_page(st.session_state.employee_name)

if __name__ == "__main__":
    main()
