import streamlit as st
import pandas as pd
import json
import sqlite3
from datetime import datetime
import folium
from streamlit_folium import folium_static
import matplotlib.pyplot as plt

# Set page configuration
st.set_page_config(
    page_title="District 6 Canvassing App",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Create database connection
@st.cache_resource
def get_connection():
    conn = sqlite3.connect('canvassing_data.db', check_same_thread=False)
    return conn

# Initialize database
def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create volunteers table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS volunteers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create precincts table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS precincts (
        id TEXT PRIMARY KEY,
        name TEXT,
        total_addresses INTEGER,
        owner_occupied INTEGER,
        non_owner_occupied INTEGER
    )
    ''')
    
    conn.commit()

# Load precinct data
@st.cache_data
def load_precinct_data():
    # For demo purposes, return sample data
    return [
        {"id": "123", "name": "Precinct 123", "total_addresses": 1253, "owner_occupied": 950, "non_owner_occupied": 303},
        {"id": "125", "name": "Precinct 125", "total_addresses": 2577, "owner_occupied": 1890, "non_owner_occupied": 687},
        {"id": "130", "name": "Precinct 130", "total_addresses": 1615, "owner_occupied": 1200, "non_owner_occupied": 415},
        {"id": "135", "name": "Precinct 135", "total_addresses": 4198, "owner_occupied": 3100, "non_owner_occupied": 1098},
        {"id": "136", "name": "Precinct 136", "total_addresses": 274, "owner_occupied": 210, "non_owner_occupied": 64},
        {"id": "138", "name": "Precinct 138", "total_addresses": 5337, "owner_occupied": 3900, "non_owner_occupied": 1437},
        {"id": "142", "name": "Precinct 142", "total_addresses": 4560, "owner_occupied": 3300, "non_owner_occupied": 1260},
        {"id": "144", "name": "Precinct 144", "total_addresses": 3334, "owner_occupied": 2500, "non_owner_occupied": 834},
        {"id": "145", "name": "Precinct 145", "total_addresses": 2704, "owner_occupied": 2000, "non_owner_occupied": 704},
        {"id": "154", "name": "Precinct 154", "total_addresses": 4908, "owner_occupied": 3600, "non_owner_occupied": 1308},
        {"id": "155", "name": "Precinct 155", "total_addresses": 4968, "owner_occupied": 3700, "non_owner_occupied": 1268}
    ]

# Load addresses for a specific precinct
@st.cache_data
def load_precinct_addresses(precinct_id):
    # For demo purposes, generate sample data
    sample_addresses = []
    streets = ["MAIN ST", "OAK AVE", "PINE ST", "MAPLE DR", "CEDAR LN", "BEACH BLVD", "CENTRAL AVE"]
    property_types = ["Single Family", "Condominium", "Duplex", "Apartment", "Townhouse"]
    owner_occupied = ["Yes", "No"]
    
    # Base coordinates for St. Petersburg, FL
    base_lat = 27.77
    base_lng = -82.64
    
    # Generate sample addresses
    for i in range(min(20, int(precinct_id) * 2)):  # Limit to 20 addresses for demo
        street = streets[i % len(streets)]
        street_num = 100 + i * 10
        
        # Create slight variations in coordinates
        lat = base_lat + (i % 10) * 0.001
        lng = base_lng + (i % 5) * 0.001
        
        sample_addresses.append({
            "id": i + 1,
            "precinct_id": precinct_id,
            "owner1": f"SMITH, JOHN {i}",
            "owner2": "SMITH, JANE" if i % 3 == 0 else "",
            "address": f"{street_num} {street}",
            "city_zip": "ST PETERSBURG, FL 33701",
            "street_number": street_num,
            "street_name": street,
            "unit": "" if i % 4 != 0 else f"#{i % 10}",
            "zip_code": "33701",
            "property_type": property_types[i % len(property_types)],
            "owner_occupied": owner_occupied[i % len(owner_occupied)],
            "latitude": lat,
            "longitude": lng
        })
    
    return sample_addresses

# Get canvassing statistics
def get_stats():
    # Return sample data for demo
    return {
        'total_interactions': 42,
        'total_addresses_contacted': 28,
        'total_addresses': 100,
        'coverage_percentage': 28.0,
        'response_breakdown': {
            "supportive": 19,
            "leaning": 5,
            "undecided": 8,
            "opposed": 7,
            "not-home": 3
        },
        'precinct_coverage': [
            {"id": "123", "name": "Precinct 123", "total_addresses": 1253, "addresses_contacted": 245},
            {"id": "125", "name": "Precinct 125", "total_addresses": 2577, "addresses_contacted": 512},
            {"id": "130", "name": "Precinct 130", "total_addresses": 1615, "addresses_contacted": 324}
        ]
    }

# Create a map with addresses
def create_map(addresses, center=None):
    # Default center if none provided
    if center is None:
        center = [27.77, -82.64]
    
    # Create map
    m = folium.Map(location=center, zoom_start=14, tiles="OpenStreetMap")
    
    # Add markers for each address
    for address in addresses:
        if address.get('latitude') and address.get('longitude'):
            # Create popup content
            owner = f"{address.get('owner1', 'Unknown')} {address.get('owner2', '')}"
            address_text = f"{address.get('address', '')}, {address.get('city_zip', '')}"
            property_info = f"{address.get('property_type', 'Unknown')} • {'Owner Occupied' if address.get('owner_occupied') == 'Yes' else 'Not Owner Occupied'}"
            
            popup_html = f"""
            <strong>{owner}</strong><br>
            {address_text}<br>
            <small>{property_info}</small>
            """
            
            # Add marker
            folium.Marker(
                location=[address['latitude'], address['longitude']],
                popup=folium.Popup(popup_html, max_width=300),
                icon=folium.Icon(color='blue', icon="home", prefix="fa")
            ).add_to(m)
    
    return m

# Initialize session state
if 'volunteer_name' not in st.session_state:
    st.session_state.volunteer_name = "Jane Doe"
if 'selected_precinct' not in st.session_state:
    st.session_state.selected_precinct = None
if 'addresses' not in st.session_state:
    st.session_state.addresses = []
if 'visited_addresses' not in st.session_state:
    st.session_state.visited_addresses = set()
if 'current_tab' not in st.session_state:
    st.session_state.current_tab = "Home"

# Initialize database
init_db()

# Sidebar for navigation
st.sidebar.title("District 6 Canvassing")
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/2/2c/Map_icon.svg/1200px-Map_icon.svg.png", width=100)

# Navigation
tab = st.sidebar.radio("Navigation", ["Home", "Stats", "Settings"])
st.session_state.current_tab = tab

# Volunteer info in sidebar
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Volunteer:** {st.session_state.volunteer_name}")
if st.sidebar.button("Sync Data"):
    st.sidebar.success("Data synchronized successfully!")

# Main content area
if st.session_state.current_tab == "Home":
    st.title("Door Knocking Campaign")
    
    # Precinct selector
    precincts = load_precinct_data()
    precinct_options = ["Select a precinct"] + [f"Precinct {p['id']} ({p['total_addresses']} addresses)" for p in precincts]
    selected_option = st.selectbox("Select Precinct:", precinct_options)
    
    if selected_option != "Select a precinct":
        # Extract precinct ID from selection
        precinct_id = selected_option.split()[1]
        
        # Load addresses if precinct changed
        if st.session_state.selected_precinct != precinct_id:
            st.session_state.selected_precinct = precinct_id
            st.session_state.addresses = load_precinct_addresses(precinct_id)
            st.session_state.visited_addresses = set()
            st.rerun()  # Changed from experimental_rerun to rerun
        
        # Display map
        if st.session_state.addresses:
            # Find center of addresses
            lats = [a['latitude'] for a in st.session_state.addresses if 'latitude' in a]
            lngs = [a['longitude'] for a in st.session_state.addresses if 'longitude' in a]
            if lats and lngs:
                center = [sum(lats)/len(lats), sum(lngs)/len(lngs)]
                m = create_map(st.session_state.addresses, center)
                st.subheader("Precinct Map")
                folium_static(m, width=800, height=500)
            
            # Progress tracking
            total_addresses = len(st.session_state.addresses)
            visited_count = len(st.session_state.visited_addresses)
            remaining_count = total_addresses - visited_count
            percentage = (visited_count / total_addresses * 100) if total_addresses > 0 else 0
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Progress", f"{visited_count}/{total_addresses} ({percentage:.1f}%)")
            with col2:
                st.metric("Remaining", remaining_count)
            
            st.progress(percentage / 100)
            
            # Address list
            st.subheader("Addresses to Visit")
            
            for i, address in enumerate(st.session_state.addresses):
                address_id = address.get('id', i)
                visited = address_id in st.session_state.visited_addresses
                
                # Create a card-like container for each address
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        owner = f"{address.get('owner1', 'Unknown')} {address.get('owner2', '')}"
                        address_text = f"{address.get('address', '')}, {address.get('city_zip', '')}"
                        property_info = f"{address.get('property_type', 'Unknown')} • {'Owner Occupied' if address.get('owner_occupied') == 'Yes' else 'Not Owner Occupied'}"
                        
                        st.markdown(f"**{owner}**")
                        st.text(address_text)
                        st.text(property_info)
                    
                    with col2:
                        if not visited:
                            if st.button("Contact", key=f"contact_{address_id}"):
                                st.session_state.visited_addresses.add(address_id)
                                st.success("Interaction recorded successfully!")
                                st.rerun()  # Changed from experimental_rerun to rerun
                            
                            if st.button("Not Home", key=f"nothome_{address_id}"):
                                st.session_state.visited_addresses.add(address_id)
                                st.success("Marked as Not Home")
                                st.rerun()  # Changed from experimental_rerun to rerun
                            
                            if st.button("Skip", key=f"skip_{address_id}"):
                                st.session_state.visited_addresses.add(address_id)
                                st.success("Marked as Skipped")
                                st.rerun()  # Changed from experimental_rerun to rerun
                        else:
                            st.success("Visited")
                    
                    st.markdown("---")
    else:
        st.info("Please select a precinct to begin canvassing")

elif st.session_state.current_tab == "Stats":
    st.title("Canvassing Statistics")
    
    # Get statistics
    stats = get_stats()
    
    # Display overall stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Doors Knocked", stats['total_interactions'])
    with col2:
        st.metric("Contacts Made", stats['total_addresses_contacted'])
    with col3:
        st.metric("Contact Rate", f"{stats['coverage_percentage']}%")
    
    # Response breakdown
    st.subheader("Response Breakdown")
    
    # Prepare data for chart
    response_labels = list(stats['response_breakdown'].keys())
    response_values = list(stats['response_breakdown'].values())
    
    if response_labels and response_values:
        # Create a pie chart
        fig, ax = plt.subplots(figsize=(10, 6))
        colors = ['#4CAF50', '#FF9800', '#2196F3', '#F44336', '#9E9E9E']
        ax.pie(response_values, labels=response_labels, autopct='%1.1f%%', startangle=90, colors=colors)
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        st.pyplot(fig)
    else:
        st.info("No response data available yet")
    
    # Precinct coverage
    st.subheader("Precinct Coverage")
    
    if stats['precinct_coverage']:
        # Create a DataFrame for the table
        coverage_df = pd.DataFrame(stats['precinct_coverage'])
        coverage_df['Coverage'] = coverage_df.apply(
            lambda row: f"{(row['addresses_contacted'] / row['total_addresses'] * 100):.1f}%" 
            if row['total_addresses'] > 0 else "0.0%", 
            axis=1
        )
        
        # Display as a table
        st.dataframe(
            coverage_df[['id', 'name', 'addresses_contacted', 'total_addresses', 'Coverage']].rename(
                columns={'id': 'Precinct ID', 'name': 'Precinct Name', 'addresses_contacted': 'Doors Knocked', 'total_addresses': 'Total Addresses'}
            ),
            hide_index=True
        )
    else:
        st.info("No precinct coverage data available yet")

elif st.session_state.current_tab == "Settings":
    st.title("Settings")
    
    # Volunteer information
    st.subheader("Volunteer Information")
    
    with st.form("volunteer_form"):
        name = st.text_input("Your Name", value=st.session_state.volunteer_name)
        email = st.text_input("Email")
        phone = st.text_input("Phone Number")
        
        if st.form_submit_button("Save Settings"):
            st.session_state.volunteer_name = name
            st.success("Settings saved successfully!")
    
    # Help and support
    st.subheader("Help & Support")
    st.markdown("""
    If you encounter any issues or have questions:
    - Contact your campaign coordinator
    - Email support at support@district6campaign.org
    - Call the campaign office at (727) 555-6789
    """)
    
    # About
    st.subheader("About")
    st.markdown("""
    **District 6 Canvassing App** v1.0
    
    This app helps campaign volunteers efficiently canvas District 6 by providing optimized routes, 
    tracking progress, and recording voter interactions.
    
    Thank you for volunteering! Your efforts make a huge difference in connecting with voters and 
    building support for our campaign.
    """)

# Footer
st.markdown("---")
st.markdown("© 2025 District 6 Campaign | Powered by Streamlit")
