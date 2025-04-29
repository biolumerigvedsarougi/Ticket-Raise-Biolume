import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import uuid
from PIL import Image
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
    "Booking Date",
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
    "Co-founders",
    "Accounts",
    "Admin Department",
    "Travel Issue",
    "Product - Delivery/Quantity/Quality/Missing",
    "Others"
]

PRIORITY_LEVELS = ["Low", "Medium", "High", "Critical"]
TRAVEL_MODES = ["Bus", "Train", "Flight", "Taxi", "Other"]
REQUEST_TYPES = ["Hotel", "Travel", "Travel & Hotel"]

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

def raise_new_request_page(employee_name, employee_code, designation):
    st.title("Raise Support Ticket")
    
    tab1, tab2 = st.tabs(["Raise New Ticket", "My Support Requests"])
    
    with tab1:
        st.subheader("Raise New Support Ticket")
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
                if not subject or not details or not employee_email or not employee_phone:
                    st.error("Please fill in all required fields (marked with *)")
                elif not employee_email.strip() or "@" not in employee_email:
                    st.error("Please enter a valid email address")
                elif not employee_phone.strip().isdigit() or len(employee_phone.strip()) < 10:
                    st.error("Please enter a valid 10-digit phone number")
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
                        
                        ticket_df = pd.DataFrame([ticket_data])
                        success, error = log_ticket_to_gsheet(conn, ticket_df)
                        
                        if success:
                            st.success(f"""
                            Your ticket has been submitted successfully! 
                            We will update you within 48 hours regarding this matter.
                            
                            **Ticket ID:** {ticket_id}
                            **Priority:** {priority}
                            """)
                            st.balloons()
                        else:
                            st.error(f"Failed to submit ticket: {error}")
    
    with tab2:
        view_my_support_requests(employee_name)

def travel_hotel_booking_page(employee_name, employee_code, designation):
    st.title("Travel & Hotel Booking")
    
    tab1, tab2, tab3 = st.tabs(["Travel Request", "Hotel Booking Request", "My Booking Requests"])
    
    with tab1:
        st.subheader("New Travel Request")
        with st.form("travel_form"):
            # Employee contact info
            col1, col2 = st.columns(2)
            with col1:
                employee_email = st.text_input(
                    "Your Email*",
                    value=st.session_state.get('employee_email', ''),
                    placeholder="your.email@company.com",
                    help="Please provide your contact email"
                )
            with col2:
                employee_phone = st.text_input(
                    "Your Phone Number*",
                    value=st.session_state.get('employee_phone', ''),
                    placeholder="9876543210",
                    help="Please provide your contact number"
                )
            
            adhara_number = st.text_input(
                "Aadhaar Number*",
                placeholder="Enter your Aadhaar number",
                help="Required for travel bookings"
            )
            
            # Travel details
            travel_mode = st.selectbox("Travel Mode*", TRAVEL_MODES)
            booking_date = st.date_input("Booking Date*", min_value=datetime.now())
            
            col1, col2 = st.columns(2)
            with col1:
                from_location = st.text_input("From*", placeholder="Starting location")
            with col2:
                to_location = st.text_input("To*", placeholder="Destination")
            
            remarks = st.text_area(
                "Remarks",
                placeholder="Any special requirements or additional information...",
                height=100
            )
            
            st.markdown("<small>*Required fields</small>", unsafe_allow_html=True)
            
            submitted = st.form_submit_button("Submit Travel Request")
            
            if submitted:
                if not employee_email or not employee_phone or not adhara_number or not travel_mode or not from_location or not to_location or not booking_date:
                    st.error("Please fill in all required fields (marked with *)")
                elif not employee_email.strip() or "@" not in employee_email:
                    st.error("Please enter a valid email address")
                elif not employee_phone.strip().isdigit() or len(employee_phone.strip()) < 10:
                    st.error("Please enter a valid 10-digit phone number")
                else:
                    with st.spinner("Submitting your travel request..."):
                        request_id = generate_request_id()
                        current_date = datetime.now().strftime("%d-%m-%Y")
                        current_time = datetime.now().strftime("%H:%M:%S")
                        
                        request_data = {
                            "Request ID": request_id,
                            "Request Type": "Travel",
                            "Employee Name": employee_name,
                            "Employee Code": employee_code,
                            "Designation": designation,
                            "Email": employee_email.strip(),
                            "Phone": employee_phone.strip(),
                            "Adhara Number": adhara_number.strip(),
                            "Hotel Name": "",
                            "Check In Date": "",
                            "Check Out Date": "",
                            "Travel Mode": travel_mode,
                            "From Location": from_location,
                            "To Location": to_location,
                            "Booking Date": booking_date.strftime("%d-%m-%Y"),
                            "Remarks": remarks,
                            "Status": "Pending",
                            "Date Requested": current_date,
                            "Time Requested": current_time
                        }
                        
                        request_df = pd.DataFrame([request_data])
                        success, error = log_travel_hotel_request(conn, request_df)
                        
                        if success:
                            st.session_state.employee_email = employee_email.strip()
                            st.session_state.employee_phone = employee_phone.strip()
                            st.success(f"""
                            Your travel request has been submitted successfully! 
                            **Request ID:** {request_id}
                            """)
                            st.balloons()
                        else:
                            st.error(f"Failed to submit request: {error}")
    
    with tab2:
        st.subheader("Hotel Booking Request")
        with st.form("hotel_form"):
            # Employee contact info
            col1, col2 = st.columns(2)
            with col1:
                employee_email = st.text_input(
                    "Your Email*",
                    value=st.session_state.get('employee_email', ''),
                    placeholder="your.email@company.com",
                    help="Please provide your contact email"
                )
            with col2:
                employee_phone = st.text_input(
                    "Your Phone Number*",
                    value=st.session_state.get('employee_phone', ''),
                    placeholder="9876543210",
                    help="Please provide your contact number"
                )
            
            adhara_number = st.text_input(
                "Aadhaar Number*",
                placeholder="Enter your Aadhaar number",
                help="Required for hotel bookings"
            )
            
            hotel_name = st.text_input("Hotel Name*")
            col1, col2 = st.columns(2)
            with col1:
                check_in_date = st.date_input("Check In Date*", min_value=datetime.now())
            with col2:
                check_out_date = st.date_input("Check Out Date*", min_value=datetime.now())
            
            remarks = st.text_area(
                "Remarks",
                placeholder="Any special requirements or additional information...",
                height=100
            )
            
            st.markdown("<small>*Required fields</small>", unsafe_allow_html=True)
            
            submitted = st.form_submit_button("Submit Hotel Booking Request")
            
            if submitted:
                if not employee_email or not employee_phone or not adhara_number or not hotel_name or not check_in_date or not check_out_date:
                    st.error("Please fill in all required fields (marked with *)")
                elif not employee_email.strip() or "@" not in employee_email:
                    st.error("Please enter a valid email address")
                elif not employee_phone.strip().isdigit() or len(employee_phone.strip()) < 10:
                    st.error("Please enter a valid 10-digit phone number")
                else:
                    with st.spinner("Submitting your hotel booking request..."):
                        request_id = generate_request_id()
                        current_date = datetime.now().strftime("%d-%m-%Y")
                        current_time = datetime.now().strftime("%H:%M:%S")
                        
                        request_data = {
                            "Request ID": request_id,
                            "Request Type": "Hotel",
                            "Employee Name": employee_name,
                            "Employee Code": employee_code,
                            "Designation": designation,
                            "Email": employee_email.strip(),
                            "Phone": employee_phone.strip(),
                            "Adhara Number": adhara_number.strip(),
                            "Hotel Name": hotel_name,
                            "Check In Date": check_in_date.strftime("%d-%m-%Y"),
                            "Check Out Date": check_out_date.strftime("%d-%m-%Y"),
                            "Travel Mode": "",
                            "From Location": "",
                            "To Location": "",
                            "Booking Date": "",
                            "Remarks": remarks,
                            "Status": "Pending",
                            "Date Requested": current_date,
                            "Time Requested": current_time
                        }
                        
                        request_df = pd.DataFrame([request_data])
                        success, error = log_travel_hotel_request(conn, request_df)
                        
                        if success:
                            st.session_state.employee_email = employee_email.strip()
                            st.session_state.employee_phone = employee_phone.strip()
                            st.success(f"""
                            Your hotel booking request has been submitted successfully! 
                            **Request ID:** {request_id}
                            """)
                            st.balloons()
                        else:
                            st.error(f"Failed to submit request: {error}")
    
    with tab3:
        view_my_booking_requests(employee_name)

def view_my_support_requests(employee_name):
    st.subheader("My Support Tickets")
    try:
        tickets_data = conn.read(worksheet="Tickets", usecols=list(range(len(TICKET_SHEET_COLUMNS))), ttl=5)
        tickets_data = tickets_data.dropna(how="all")
        
        if not tickets_data.empty:
            my_tickets = tickets_data[
                tickets_data['Raised By (Employee Name)'] == employee_name
            ].sort_values(by="Date Raised", ascending=False)
            
            if not my_tickets.empty:
                pending_count = len(my_tickets[my_tickets['Status'] == "Open"])
                resolved_count = len(my_tickets[my_tickets['Status'] == "Resolved"])
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Tickets", len(my_tickets))
                col2.metric("Open", pending_count)
                col3.metric("Resolved", resolved_count)
                
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
                
                filtered_tickets = my_tickets.copy()
                if status_filter != "All":
                    filtered_tickets = filtered_tickets[filtered_tickets['Status'] == status_filter]
                if priority_filter != "All":
                    filtered_tickets = filtered_tickets[filtered_tickets['Priority'] == priority_filter]
                if category_filter != "All":
                    filtered_tickets = filtered_tickets[filtered_tickets['Category'] == category_filter]
                
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
                
                if not filtered_tickets.empty:
                    csv = filtered_tickets.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "Download Tickets",
                        csv,
                        "my_support_tickets.csv",
                        "text/csv",
                        key='download-tickets-csv'
                    )
            else:
                st.info("You haven't raised any support tickets yet.")
        else:
            st.info("No support tickets found in the system.")
            
    except Exception as e:
        st.error(f"Error retrieving support tickets: {str(e)}")

def view_my_booking_requests(employee_name):
    st.subheader("My Travel & Hotel Requests")
    try:
        requests_data = conn.read(worksheet="TravelHotelRequests", usecols=list(range(len(TRAVEL_HOTEL_COLUMNS))), ttl=5)
        requests_data = requests_data.dropna(how="all")
        
        if not requests_data.empty:
            my_requests = requests_data[
                requests_data['Employee Name'] == employee_name
            ].sort_values(by="Date Requested", ascending=False)
            
            if not my_requests.empty:
                pending_count = len(my_requests[my_requests['Status'] == "Pending"])
                approved_count = len(my_requests[my_requests['Status'] == "Approved"])
                rejected_count = len(my_requests[my_requests['Status'] == "Rejected"])
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Requests", len(my_requests))
                col2.metric("Pending", pending_count)
                col3.metric("Approved", approved_count)
                
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
                        ["All"] + REQUEST_TYPES,
                        key="request_type_filter"
                    )
                
                filtered_requests = my_requests.copy()
                if status_filter != "All":
                    filtered_requests = filtered_requests[filtered_requests['Status'] == status_filter]
                if type_filter != "All":
                    filtered_requests = filtered_requests[filtered_requests['Request Type'] == type_filter]
                
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
                        st.write(f"**Your Contact Email:** {row['Email']}")
                        st.write(f"**Your Phone Number:** {row['Phone']}")
                        st.write(f"**Adhara Number:** {row['Adhara Number']}")
                        
                        if row['Request Type'] in ["Hotel", "Travel & Hotel"]:
                            st.write("---")
                            st.write("**Hotel Details:**")
                            st.write(f"**Hotel Name:** {row['Hotel Name']}")
                            st.write(f"**Check In Date:** {row['Check In Date']}")
                            st.write(f"**Check Out Date:** {row['Check Out Date']}")
                        
                        if row['Request Type'] in ["Travel", "Travel & Hotel"]:
                            st.write("---")
                            st.write("**Travel Details:**")
                            st.write(f"**Travel Mode:** {row['Travel Mode']}")
                            st.write(f"**From:** {row['From Location']}")
                            st.write(f"**To:** {row['To Location']}")
                            st.write(f"**Booking Date:** {row['Booking Date']}")
                        
                        if row['Remarks']:
                            st.write("---")
                            st.write("**Remarks:**")
                            st.write(row['Remarks'])
                
                if not filtered_requests.empty:
                    csv = filtered_requests.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "Download Requests",
                        csv,
                        "my_travel_requests.csv",
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
    if 'employee_email' not in st.session_state:
        st.session_state.employee_email = None
    if 'employee_phone' not in st.session_state:
        st.session_state.employee_phone = None

    if not st.session_state.authenticated:
        # Create centered layout for logo and heading
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col2:
            # Display centered logo
            try:
                logo = Image.open("logo.png")
                st.image(logo, use_container_width=True)
            except FileNotFoundError:
                st.warning("Logo image not found")
            
            # Centered heading with custom style
            st.markdown("""
            <div style='text-align: center; margin-bottom: 30px;'>
                <h1 style='margin-bottom: 0;'>Employee Portal</h1>
            </div>
            """, unsafe_allow_html=True)

        # Login form
        employee_names = Person['Employee Name'].tolist()
        
        # Create centered form
        form_col1, form_col2, form_col3 = st.columns([1, 2, 1])
        
        with form_col2:
            with st.container():
                employee_name = st.selectbox(
                    "Select Your Name", 
                    employee_names, 
                    key="employee_select"
                )
                passkey = st.text_input(
                    "Password", 
                    type="password", 
                    key="passkey_input"
                )
                
                login_button = st.button(
                    "Log in", 
                    key="login_button",
                    use_container_width=True
                )
                
                if login_button:
                    if authenticate_employee(employee_name, passkey):
                        st.session_state.authenticated = True
                        st.session_state.employee_name = employee_name
                        st.session_state.employee_code = Person[Person['Employee Name'] == employee_name]['Employee Code'].values[0]
                        st.session_state.designation = Person[Person['Employee Name'] == employee_name]['Designation'].values[0]
                        st.rerun()
                    else:
                        st.error("Invalid Employee Code. Please try again.")
    else:
        # Authenticated view
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
            st.rerun()
        
        page = st.sidebar.radio(
            "Navigation",
            ["Travel & Hotel Booking", "Raise Support Ticket"],
            index=0
        )
        
        if page == "Raise Support Ticket":
            raise_new_request_page(
                st.session_state.employee_name,
                st.session_state.employee_code,
                st.session_state.designation
            )
        elif page == "Travel & Hotel Booking":
            travel_hotel_booking_page(
                st.session_state.employee_name,
                st.session_state.employee_code,
                st.session_state.designation
            )

if __name__ == "__main__":
    main()
