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

TRAVEL_HOTEL_COLUMNS = [
    "Request ID",
    "Request Type",
    "Employee Name",
    "Employee Code",
    "Designation",
    "Email",
    "Phone",
    "Adhara Number",
    "Hotel Name",
    "Check In Date",
    "Check Out Date",
    "Travel Mode",
    "From Location",
    "To Location",
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

PRIORITY_LEVELS = ["Low", "Medium", "High", "Critical"]
TRAVEL_MODES = ["Bus", "Train", "Flight", "Taxi", "Other"]

# Establish Google Sheets connection
conn = st.connection("gsheets", type=GSheetsConnection)

# Load employee data
Person = pd.read_csv('Invoice - Person.csv')

def generate_ticket_id():
    return f"TKT-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"

def generate_request_id():
    return f"REQ-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"

def log_ticket_to_gsheet(conn, ticket_data):
    try:
        existing_data = conn.read(worksheet="Tickets", usecols=list(range(len(TICKET_SHEET_COLUMNS))), ttl=5)
        existing_data = existing_data.dropna(how="all")
        updated_data = pd.concat([existing_data, ticket_data], ignore_index=True)
        conn.update(worksheet="Tickets", data=updated_data)
        return True, None
    except Exception as e:
        return False, str(e)

def log_travel_hotel_request(conn, request_data):
    try:
        existing_data = conn.read(worksheet="TravelHotelRequests", usecols=list(range(len(TRAVEL_HOTEL_COLUMNS))), ttl=5)
        existing_data = existing_data.dropna(how="all")
        updated_data = pd.concat([existing_data, request_data], ignore_index=True)
        conn.update(worksheet="TravelHotelRequests", data=updated_data)
        return True, None
    except Exception as e:
        return False, str(e)

def authenticate_employee(employee_name, passkey):
    try:
        employee_code = Person[Person['Employee Name'] == employee_name]['Employee Code'].values[0]
        return str(passkey) == str(employee_code)
    except:
        return False

def raise_ticket_page(employee_name, employee_code, designation):
    st.title("Raise New Ticket")
    
    with st.form("ticket_form"):
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
        
        # Ticket details
        category = st.selectbox(
            "Category*",
            TICKET_CATEGORIES,
            help="Select the most relevant category for your ticket"
        )
        
        if category in ["Hotel", "Travel", "Travel & Hotel"]:
            # Travel/Hotel specific fields
            st.subheader("Travel/Hotel Booking Details")
            adhara_number = st.text_input(
                "Adhara Number*",
                placeholder="Enter your Adhara number",
                help="Required for travel/hotel bookings"
            )
            
            if category == "Hotel":
                hotel_name = st.text_input("Hotel Name*")
                col1, col2 = st.columns(2)
                with col1:
                    check_in_date = st.date_input("Check In Date*")
                with col2:
                    check_out_date = st.date_input("Check Out Date*")
                remarks = st.text_area("Remarks")
                
                # Set default values for travel fields
                travel_mode = ""
                from_location = ""
                to_location = ""
                
            elif category == "Travel":
                travel_mode = st.selectbox("Travel Mode*", TRAVEL_MODES)
                col1, col2 = st.columns(2)
                with col1:
                    from_location = st.text_input("From*", placeholder="Starting location")
                with col2:
                    to_location = st.text_input("To*", placeholder="Destination")
                remarks = st.text_area("Remarks")
                
                # Set default values for hotel fields
                hotel_name = ""
                check_in_date = ""
                check_out_date = ""
                
            elif category == "Travel & Hotel":
                # Hotel section
                st.markdown("**Hotel Details**")
                hotel_name = st.text_input("Hotel Name*")
                col1, col2 = st.columns(2)
                with col1:
                    check_in_date = st.date_input("Check In Date*")
                with col2:
                    check_out_date = st.date_input("Check Out Date*")
                
                # Travel section
                st.markdown("**Travel Details**")
                travel_mode = st.selectbox("Travel Mode*", TRAVEL_MODES)
                col1, col2 = st.columns(2)
                with col1:
                    from_location = st.text_input("From*", placeholder="Starting location")
                with col2:
                    to_location = st.text_input("To*", placeholder="Destination")
                remarks = st.text_area("Remarks")
            
            # For travel/hotel bookings, subject is auto-generated
            subject = f"{category} Booking Request"
            details = f"Travel/Hotel booking request - {remarks}" if remarks else "Travel/Hotel booking request"
            priority = "Medium"  # Default for travel/hotel requests
            
        else:
            # Regular ticket fields
            col1, col2 = st.columns(2)
            with col1:
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
            
            # Set default values for travel/hotel fields
            adhara_number = ""
            hotel_name = ""
            check_in_date = ""
            check_out_date = ""
            travel_mode = ""
            from_location = ""
            to_location = ""
            remarks = ""
        
        st.markdown("<small>*Required fields</small>", unsafe_allow_html=True)
        
        submitted = st.form_submit_button("Submit Request" if category in ["Hotel", "Travel", "Travel & Hotel"] else "Submit Ticket")
        
        if submitted:
            if not employee_email or not employee_phone:
                st.error("Please fill in all required fields (marked with *)")
            elif not employee_email.strip() or "@" not in employee_email:
                st.error("Please enter a valid email address")
            elif not employee_phone.strip().isdigit() or len(employee_phone.strip()) < 10:
                st.error("Please enter a valid 10-digit phone number")
            elif category in ["Hotel", "Travel", "Travel & Hotel"] and not adhara_number.strip():
                st.error("Please enter your Adhara number for travel/hotel bookings")
            else:
                with st.spinner("Submitting your request..."):
                    current_date = datetime.now().strftime("%d-%m-%Y")
                    current_time = datetime.now().strftime("%H:%M:%S")
                    
                    if category in ["Hotel", "Travel", "Travel & Hotel"]:
                        # Handle travel/hotel booking
                        request_id = generate_request_id()
                        
                        request_data = {
                            "Request ID": request_id,
                            "Request Type": category,
                            "Employee Name": employee_name,
                            "Employee Code": employee_code,
                            "Designation": designation,
                            "Email": employee_email.strip(),
                            "Phone": employee_phone.strip(),
                            "Adhara Number": adhara_number.strip(),
                            "Hotel Name": hotel_name if category in ["Hotel", "Travel & Hotel"] else "",
                            "Check In Date": check_in_date.strftime("%d-%m-%Y") if category in ["Hotel", "Travel & Hotel"] and check_in_date else "",
                            "Check Out Date": check_out_date.strftime("%d-%m-%Y") if category in ["Hotel", "Travel & Hotel"] and check_out_date else "",
                            "Travel Mode": travel_mode if category in ["Travel", "Travel & Hotel"] else "",
                            "From Location": from_location if category in ["Travel", "Travel & Hotel"] else "",
                            "To Location": to_location if category in ["Travel", "Travel & Hotel"] else "",
                            "Remarks": remarks,
                            "Status": "Pending",
                            "Date Requested": current_date,
                            "Time Requested": current_time
                        }
                        
                        # Convert to DataFrame
                        request_df = pd.DataFrame([request_data])
                        
                        # Log to Google Sheets
                        success, error = log_travel_hotel_request(conn, request_df)
                        
                        if success:
                            st.success(f"""
                            Your {category.lower()} request has been submitted successfully! 
                            
                            **Request ID:** {request_id}
                            """)
                            st.balloons()
                        else:
                            st.error(f"Failed to submit request: {error}")
                    
                    else:
                        # Handle regular ticket
                        if not subject or not details:
                            st.error("Please fill in all required fields (marked with *)")
                            return
                            
                        ticket_id = generate_ticket_id()
                        
                        ticket_data = {
                            "Ticket ID": ticket_id,
                            "Raised By (Employee Name)": employee_name,
                            "Raised By (Employee Code)": employee_code,
                            "Raised By (Designation)": designation,
                            "Raised By (Email)": employee_email.strip(),
                            "Raised By (Phone)": employee_phone.strip(),
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

def view_tickets_page(employee_name):
    st.title("My Requests")
    
    # Tab for regular tickets and travel/hotel requests
    tab1, tab2 = st.tabs(["Tickets", "Travel/Hotel Requests"])
    
    with tab1:
        try:
            # Read tickets data
            tickets_data = conn.read(worksheet="Tickets", usecols=list(range(len(TICKET_SHEET_COLUMNS))), ttl=5)
            tickets_data = tickets_data.dropna(how="all")
            
            if not tickets_data.empty:
                # Filter for current employee
                my_tickets = tickets_data[
                    tickets_data['Raised By (Employee Name)'] == employee_name
                ].sort_values(by="Date Raised", ascending=False)
                
                if not my_tickets.empty:
                    # Display stats
                    open_count = len(my_tickets[my_tickets['Status'] == "Open"])
                    resolved_count = len(my_tickets[my_tickets['Status'] == "Resolved"])
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total Tickets", len(my_tickets))
                    col2.metric("Open", open_count)
                    col3.metric("Resolved", resolved_count)
                    
                    # Filter options
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
                            ["All"] + [cat for cat in TICKET_CATEGORIES if cat not in ["Hotel", "Travel", "Travel & Hotel"]],
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
                    if not filtered_tickets.empty:
                        csv = filtered_tickets.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            "Download Filtered Tickets",
                            csv,
                            "my_tickets.csv",
                            "text/csv",
                            key='download-tickets-csv'
                        )
                else:
                    st.info("You haven't raised any tickets yet.")
            else:
                st.info("No tickets found in the system.")
                
        except Exception as e:
            st.error(f"Error retrieving tickets: {str(e)}")
    
    with tab2:
        try:
            # Read travel/hotel requests data
            requests_data = conn.read(worksheet="TravelHotelRequests", usecols=list(range(len(TRAVEL_HOTEL_COLUMNS))), ttl=5)
            requests_data = requests_data.dropna(how="all")
            
            if not requests_data.empty:
                # Filter for current employee
                my_requests = requests_data[
                    requests_data['Employee Name'] == employee_name
                ].sort_values(by="Date Requested", ascending=False)
                
                if not my_requests.empty:
                    # Display stats
                    pending_count = len(my_requests[my_requests['Status'] == "Pending"])
                    approved_count = len(my_requests[my_requests['Status'] == "Approved"])
                    rejected_count = len(my_requests[my_requests['Status'] == "Rejected"])
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Total Requests", len(my_requests))
                    col2.metric("Pending", pending_count)
                    col3.metric("Approved", approved_count)
                    
                    # Filter options
                    st.subheader("Filter Requests")
                    col1, col2 = st.columns(2)
                    with col1:
                        status_filter = st.selectbox(
                            "Status",
                            ["All", "Pending", "Approved", "Rejected"],
                            key="request_status_filter"
                        )
                    with col2:
                        type_filter = st.selectbox(
                            "Request Type",
                            ["All", "Hotel", "Travel", "Travel & Hotel"],
                            key="request_type_filter"
                        )
                    
                    # Apply filters
                    filtered_requests = my_requests.copy()
                    if status_filter != "All":
                        filtered_requests = filtered_requests[filtered_requests['Status'] == status_filter]
                    if type_filter != "All":
                        filtered_requests = filtered_requests[filtered_requests['Request Type'] == type_filter]
                    
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
                            
                            # Common details
                            st.write(f"**Your Contact Email:** {row['Email']}")
                            st.write(f"**Your Phone Number:** {row['Phone']}")
                            st.write(f"**Adhara Number:** {row['Adhara Number']}")
                            
                            # Hotel details if applicable
                            if row['Request Type'] in ["Hotel", "Travel & Hotel"]:
                                st.write("---")
                                st.write("**Hotel Details:**")
                                st.write(f"**Hotel Name:** {row['Hotel Name']}")
                                st.write(f"**Check In Date:** {row['Check In Date']}")
                                st.write(f"**Check Out Date:** {row['Check Out Date']}")
                            
                            # Travel details if applicable
                            if row['Request Type'] in ["Travel", "Travel & Hotel"]:
                                st.write("---")
                                st.write("**Travel Details:**")
                                st.write(f"**Travel Mode:** {row['Travel Mode']}")
                                st.write(f"**From:** {row['From Location']}")
                                st.write(f"**To:** {row['To Location']}")
                            
                            # Remarks
                            if row['Remarks']:
                                st.write("---")
                                st.write("**Remarks:**")
                                st.write(row['Remarks'])
                    
                    # Download option
                    if not filtered_requests.empty:
                        csv = filtered_requests.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            "Download Filtered Requests",
                            csv,
                            "my_travel_hotel_requests.csv",
                            "text/csv",
                            key='download-requests-csv'
                        )
                else:
                    st.info("You haven't made any travel/hotel requests yet.")
            else:
                st.info("No travel/hotel requests found in the system.")
                
        except Exception as e:
            st.error(f"Error retrieving travel/hotel requests: {str(e)}")

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
        
        tab1, tab2 = st.tabs(["Raise New Request", "My Requests"])
        with tab1:
            raise_ticket_page(
                st.session_state.employee_name,
                st.session_state.employee_code,
                st.session_state.designation
            )
        with tab2:
            view_tickets_page(st.session_state.employee_name)

if __name__ == "__main__":
    main()
