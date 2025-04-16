# ticket_app.py
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
TICKET_SHEET_COLUMNS = [
    "Ticket ID",
    "Raised By (Employee Name)",
    "Raised By (Employee Code)",
    "Raised By (Designation)",
    "Raised By (Email)",
    "Raised By (Phone)",
    "Raised By (Adhaar)",
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

TRAVEL_SHEET_COLUMNS = [
    "Request ID",
    "Employee Name",
    "Employee Code",
    "Designation",
    "Email",
    "Phone",
    "Adhaar Number",
    "Request Type",
    "Travel Mode",
    "From Location",
    "To Location",
    "Start Date",
    "End Date",
    "Hotel Name",
    "Check In Date",
    "Check Out Date",
    "Remarks",
    "Status",
    "Date Requested",
    "Time Requested"
]

# Categories and priorities
TICKET_CATEGORIES = [
    "HR Department",
    "MIS & Back Office",
    "Digital & Marketing",
    "Travel",
    "Hotel",
    "Travel & Hotel",
    "Co-founders",
    "Accounts",
    "Admin Department",
    "Product - Delivery/Quantity/Quality/Missing",
    "Others"
]

TRAVEL_MODES = ["Bus", "Train", "Flight", "Taxi", "Other"]
PRIORITY_LEVELS = ["Low", "Medium", "High", "Critical"]

# Establish Google Sheets connection
conn = st.connection("gsheets", type=GSheetsConnection)

# Load employee data
Person = pd.read_csv('Invoice - Person.csv')

def generate_ticket_id():
    return f"TKT-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"

def generate_travel_request_id():
    return f"TRV-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"

def log_ticket_to_gsheet(conn, ticket_data):
    try:
        existing_data = conn.read(worksheet="Tickets", usecols=list(range(len(TICKET_SHEET_COLUMNS))), ttl=5)
        existing_data = existing_data.dropna(how="all")
        updated_data = pd.concat([existing_data, ticket_data], ignore_index=True)
        conn.update(worksheet="Tickets", data=updated_data)
        return True, None
    except Exception as e:
        return False, str(e)

def log_travel_request_to_gsheet(conn, travel_data):
    try:
        existing_data = conn.read(worksheet="TravelRequests", usecols=list(range(len(TRAVEL_SHEET_COLUMNS))), ttl=5)
        existing_data = existing_data.dropna(how="all")
        updated_data = pd.concat([existing_data, travel_data], ignore_index=True)
        conn.update(worksheet="TravelRequests", data=updated_data)
        return True, None
    except Exception as e:
        return False, str(e)

def authenticate_employee(employee_name, passkey):
    try:
        employee_code = Person[Person['Employee Name'] == employee_name]['Employee Code'].values[0]
        return str(passkey) == str(employee_code)
    except:
        return False

def raise_ticket_page(employee_name, employee_code, designation, email, phone, adhaar):
    st.title("Raise New Ticket")
    
    with st.form("ticket_form"):
        # Employee contact info (pre-filled from session state)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.text_input("Your Email*", value=email, disabled=True)
        with col2:
            st.text_input("Your Phone Number*", value=phone, disabled=True)
        with col3:
            st.text_input("Your Adhaar Number", value=adhaar, disabled=True)
        
        # Ticket details
        col1, col2 = st.columns(2)
        with col1:
            category = st.selectbox(
                "Department",
                TICKET_CATEGORIES,
                help="Select the most relevant category for your ticket"
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
            placeholder="Brief description of your ticket",
            help="Keep it concise but descriptive"
        )
        
        details = st.text_area(
            "Details*",
            height=200,
            placeholder="Please provide detailed information about your ticket...",
            help="Include all relevant details to help resolve your issue quickly"
        )
        
        st.markdown("<small>*Required fields</small>", unsafe_allow_html=True)
        
        submitted = st.form_submit_button("Submit Ticket")
        
        if submitted:
            if not subject or not details:
                st.error("Please fill in all required fields (marked with *)")
            else:
                with st.spinner("Submitting your ticket..."):
                    ticket_id = generate_ticket_id()
                    current_date = datetime.now().strftime("%d-%m-%Y")
                    current_time = datetime.now().strftime("%H:%M:%S")
                    
                    ticket_data = {
                        "Ticket ID": ticket_id,
                        "Raised By (Employee Name)": employee_name,
                        "Raised By (Employee Code)": employee_code,
                        "Raised By (Designation)": designation,
                        "Raised By (Email)": email,
                        "Raised By (Phone)": phone,
                        "Raised By (Adhaar)": adhaar,
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
                    ticket_df = pd.DataFrame([ticket_data])
                    
                    # Log to Google Sheets
                    success, error = log_ticket_to_gsheet(conn, ticket_df)
                    
                    if success:
                        st.success(f"""
                        Your ticket has been submitted successfully! We will update you within 48 hours regarding this matter.
                        
                        **Ticket ID:** {ticket_id}
                        **Priority:** {priority}
                        """)
                        st.balloons()
                    else:
                        st.error(f"Failed to submit ticket: {error}")

def travel_request_page(employee_name, employee_code, designation, email, phone, adhaar):
    st.title("Travel & Hotel Booking Request")
    
    request_type = st.radio("Request Type", ["Hotel", "Travel", "Travel & Hotel"])
    
    with st.form("travel_request_form"):
        # Employee contact info (pre-filled)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.text_input("Your Email*", value=email, disabled=True)
        with col2:
            st.text_input("Your Phone Number*", value=phone, disabled=True)
        with col3:
            st.text_input("Your Adhaar Number", value=adhaar, disabled=True)
        
        # Common fields
        if request_type in ["Travel", "Travel & Hotel"]:
            st.subheader("Travel Details")
            col1, col2 = st.columns(2)
            with col1:
                travel_mode = st.selectbox("Travel Mode", TRAVEL_MODES)
                from_location = st.text_input("From Location*")
            with col2:
                to_location = st.text_input("To Location*")
                start_date = st.date_input("Start Date*")
                end_date = st.date_input("End Date*")
            
            travel_remarks = st.text_area("Travel Remarks")
        
        if request_type in ["Hotel", "Travel & Hotel"]:
            st.subheader("Hotel Details")
            col1, col2 = st.columns(2)
            with col1:
                hotel_name = st.text_input("Hotel Name*")
                check_in_date = st.date_input("Check-in Date*")
            with col2:
                check_out_date = st.date_input("Check-out Date*")
            
            hotel_remarks = st.text_area("Hotel Remarks")
        
        remarks = st.text_area("Additional Remarks")
        
        submitted = st.form_submit_button("Submit Request")
        
        if submitted:
            required_fields_valid = True
            
            if request_type in ["Travel", "Travel & Hotel"]:
                if not from_location or not to_location or not start_date or not end_date:
                    st.error("Please fill all required travel fields")
                    required_fields_valid = False
                if start_date > end_date:
                    st.error("End date cannot be before start date")
                    required_fields_valid = False
            
            if request_type in ["Hotel", "Travel & Hotel"]:
                if not hotel_name or not check_in_date or not check_out_date:
                    st.error("Please fill all required hotel fields")
                    required_fields_valid = False
                if check_in_date > check_out_date:
                    st.error("Check-out date cannot be before check-in date")
                    required_fields_valid = False
            
            if required_fields_valid:
                with st.spinner("Submitting your request..."):
                    request_id = generate_travel_request_id()
                    current_date = datetime.now().strftime("%d-%m-%Y")
                    current_time = datetime.now().strftime("%H:%M:%S")
                    
                    travel_data = {
                        "Request ID": request_id,
                        "Employee Name": employee_name,
                        "Employee Code": employee_code,
                        "Designation": designation,
                        "Email": email,
                        "Phone": phone,
                        "Adhaar Number": adhaar,
                        "Request Type": request_type,
                        "Travel Mode": travel_mode if request_type in ["Travel", "Travel & Hotel"] else "",
                        "From Location": from_location if request_type in ["Travel", "Travel & Hotel"] else "",
                        "To Location": to_location if request_type in ["Travel", "Travel & Hotel"] else "",
                        "Start Date": start_date.strftime("%d-%m-%Y") if request_type in ["Travel", "Travel & Hotel"] else "",
                        "End Date": end_date.strftime("%d-%m-%Y") if request_type in ["Travel", "Travel & Hotel"] else "",
                        "Hotel Name": hotel_name if request_type in ["Hotel", "Travel & Hotel"] else "",
                        "Check In Date": check_in_date.strftime("%d-%m-%Y") if request_type in ["Hotel", "Travel & Hotel"] else "",
                        "Check Out Date": check_out_date.strftime("%d-%m-%Y") if request_type in ["Hotel", "Travel & Hotel"] else "",
                        "Remarks": f"Travel Remarks: {travel_remarks}\nHotel Remarks: {hotel_remarks}\nAdditional Remarks: {remarks}",
                        "Status": "Pending",
                        "Date Requested": current_date,
                        "Time Requested": current_time
                    }
                    
                    # Convert to DataFrame
                    travel_df = pd.DataFrame([travel_data])
                    
                    # Log to Google Sheets
                    success, error = log_travel_request_to_gsheet(conn, travel_df)
                    
                    if success:
                        st.success(f"""
                        Your {request_type.lower()} request has been submitted successfully!
                        
                        **Request ID:** {request_id}
                        """)
                        st.balloons()
                    else:
                        st.error(f"Failed to submit request: {error}")

def view_tickets_page(employee_name):
    st.title("My Tickets & Requests")
    
    try:
        # Read tickets data
        tickets_data = conn.read(worksheet="Tickets", usecols=list(range(len(TICKET_SHEET_COLUMNS))), ttl=5)
        tickets_data = tickets_data.dropna(how="all")
        
        # Read travel requests data
        travel_data = conn.read(worksheet="TravelRequests", usecols=list(range(len(TRAVEL_SHEET_COLUMNS))), ttl=5)
        travel_data = travel_data.dropna(how="all")
        
        if tickets_data.empty and travel_data.empty:
            st.info("No tickets or requests found in the system.")
            return
            
        # Filter for current employee
        my_tickets = tickets_data[
            tickets_data['Raised By (Employee Name)'] == employee_name
        ].sort_values(by="Date Raised", ascending=False) if not tickets_data.empty else pd.DataFrame()
        
        my_travel_requests = travel_data[
            travel_data['Employee Name'] == employee_name
        ].sort_values(by="Date Requested", ascending=False) if not travel_data.empty else pd.DataFrame()
        
        if my_tickets.empty and my_travel_requests.empty:
            st.info("You haven't raised any tickets or requests yet.")
            return
            
        # Display stats
        ticket_open_count = len(my_tickets[my_tickets['Status'] == "Open"]) if not my_tickets.empty else 0
        ticket_resolved_count = len(my_tickets[my_tickets['Status'] == "Resolved"]) if not my_tickets.empty else 0
        travel_pending_count = len(my_travel_requests[my_travel_requests['Status'] == "Pending"]) if not my_travel_requests.empty else 0
        travel_approved_count = len(my_travel_requests[my_travel_requests['Status'] == "Approved"]) if not my_travel_requests.empty else 0
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Tickets", len(my_tickets))
        col2.metric("Open Tickets", ticket_open_count)
        col3.metric("Pending Travel Requests", travel_pending_count)
        col4.metric("Approved Travel Requests", travel_approved_count)
        
        # Display tickets and requests in tabs
        tab1, tab2 = st.tabs(["Tickets", "Travel & Hotel Requests"])
        
        with tab1:
            if my_tickets.empty:
                st.info("You haven't raised any tickets yet.")
            else:
                # Filter options for tickets
                st.subheader("Filter Tickets")
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
                        ["All"] + TICKET_CATEGORIES,
                        key="category_filter"
                    )
                
                # Apply filters
                filtered_tickets = my_tickets.copy()
                if status_filter != "All":
                    filtered_tickets = filtered_tickets[filtered_tickets['Status'] == status_filter]
                if priority_filter != "All":
                    filtered_tickets = filtered_tickets[filtered_tickets['Priority'] == priority_filter]
                if category_filter != "All":
                    filtered_tickets = filtered_tickets[filtered_tickets['Category'] == category_filter]
                
                # Display tickets
                for _, row in filtered_tickets.iterrows():
                    with st.expander(f"{row['Subject']} - {row['Status']} ({row['Priority']})"):
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
                            st.write(f"**Priority:** {row['Priority']}")
                            if row['Date Resolved']:
                                st.write(f"**Date Resolved:** {row['Date Resolved']}")
                        
                        st.write("---")
                        st.write("**Details:**")
                        st.write(row['Details'])
                        
                        if row['Status'] == "Resolved" and row['Resolution Notes']:
                            st.write("---")
                            st.write("**Resolution Notes:**")
                            st.write(row['Resolution Notes'])
                
                # Download option
                if not filtered_tickets.empty:
                    csv = filtered_tickets.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "Download Filtered Tickets",
                        csv,
                        "my_tickets.csv",
                        "text/csv",
                        key='download-tickets-csv'
                    )
        
        with tab2:
            if my_travel_requests.empty:
                st.info("You haven't made any travel or hotel requests yet.")
            else:
                # Filter options for travel requests
                st.subheader("Filter Requests")
                col1, col2 = st.columns(2)
                with col1:
                    request_type_filter = st.selectbox(
                        "Request Type",
                        ["All", "Hotel", "Travel", "Travel & Hotel"],
                        key="request_type_filter"
                    )
                with col2:
                    request_status_filter = st.selectbox(
                        "Status",
                        ["All", "Pending", "Approved", "Rejected"],
                        key="request_status_filter"
                    )
                
                # Apply filters
                filtered_requests = my_travel_requests.copy()
                if request_type_filter != "All":
                    filtered_requests = filtered_requests[filtered_requests['Request Type'] == request_type_filter]
                if request_status_filter != "All":
                    filtered_requests = filtered_requests[filtered_requests['Status'] == request_status_filter]
                
                # Display requests
                for _, row in filtered_requests.iterrows():
                    with st.expander(f"{row['Request Type']} - {row['Status']}"):
                        status_color = "orange" if row['Status'] == "Pending" else "green" if row['Status'] == "Approved" else "red"
                        st.markdown(f"""
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong>Request ID:</strong> {row['Request ID']}<br>
                                <strong>Date Requested:</strong> {row['Date Requested']} at {row['Time Requested']}
                            </div>
                            <div style="color: {status_color}; font-weight: bold;">
                                {row['Status']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.write("---")
                        
                        # Main content
                        if row['Request Type'] in ["Travel", "Travel & Hotel"]:
                            st.subheader("Travel Details")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Travel Mode:** {row['Travel Mode']}")
                                st.write(f"**From:** {row['From Location']}")
                            with col2:
                                st.write(f"**To:** {row['To Location']}")
                                st.write(f"**Dates:** {row['Start Date']} to {row['End Date']}")
                        
                        if row['Request Type'] in ["Hotel", "Travel & Hotel"]:
                            st.subheader("Hotel Details")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Hotel Name:** {row['Hotel Name']}")
                            with col2:
                                st.write(f"**Dates:** {row['Check In Date']} to {row['Check Out Date']}")
                        
                        st.write("---")
                        st.write("**Remarks:**")
                        st.write(row['Remarks'])
                
                # Download option
                if not filtered_requests.empty:
                    csv = filtered_requests.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "Download Filtered Requests",
                        csv,
                        "my_travel_requests.csv",
                        "text/csv",
                        key='download-requests-csv'
                    )
                    
    except Exception as e:
        st.error(f"Error retrieving data: {str(e)}")

def main():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'employee_name' not in st.session_state:
        st.session_state.employee_name = None
    if 'employee_code' not in st.session_state:
        st.session_state.employee_code = None
    if 'designation' not in st.session_state:
        st.session_state.designation = None
    if 'employee_email' not in st.session_state:
        st.session_state.employee_email = None
    if 'employee_phone' not in st.session_state:
        st.session_state.employee_phone = None
    if 'employee_adhaar' not in st.session_state:
        st.session_state.employee_adhaar = None

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
                st.session_state.employee_email = Person[Person['Employee Name'] == employee_name]['Email'].values[0]
                st.session_state.employee_phone = Person[Person['Employee Name'] == employee_name]['Phone'].values[0]
                st.session_state.employee_adhaar = Person[Person['Employee Name'] == employee_name]['Adhaar'].values[0]
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
            st.session_state.employee_email = None
            st.session_state.employee_phone = None
            st.session_state.employee_adhaar = None
            st.rerun()
        
        tab1, tab2, tab3 = st.tabs(["Raise New Ticket", "Travel & Hotel", "My Tickets & Requests"])
        with tab1:
            raise_ticket_page(
                st.session_state.employee_name,
                st.session_state.employee_code,
                st.session_state.designation,
                st.session_state.employee_email,
                st.session_state.employee_phone,
                st.session_state.employee_adhaar
            )
        with tab2:
            travel_request_page(
                st.session_state.employee_name,
                st.session_state.employee_code,
                st.session_state.designation,
                st.session_state.employee_email,
                st.session_state.employee_phone,
                st.session_state.employee_adhaar
            )
        with tab3:
            view_tickets_page(st.session_state.employee_name)

if __name__ == "__main__":
    main()
