
import streamlit as st
from openai import OpenAI
import json
import os
from dotenv import load_dotenv
from weather_api import get_weather
from datetime import datetime
import urllib.parse
import requests
import google.generativeai as genai

# Load environment variables
load_dotenv()

genai.configure(api_key="AIzaSyArFsF8XTEyuPDbQhtvGjZfygziLN6RF7o")

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 1024,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

# File paths
USER_FILE = "user.json"
FEEDBACK_FILE = "feedback.json"

def load_users():
    try:
        with open(USER_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        with open(USER_FILE, "w") as f:
            json.dump({}, f)
        return {}

def save_user(username, password):
    users = load_users()
    users[username] = password
    with open(USER_FILE, "w") as f:
        json.dump(users, f)

def load_feedback():
    try:
        with open(FEEDBACK_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_feedback(username, destination, rating, comment):
    feedback = load_feedback()
    
    if username not in feedback:
        feedback[username] = []
    
    feedback[username].append({
        "destination": destination,
        "rating": rating,
        "comment": comment,
        "date": str(datetime.now())
    })

    with open(FEEDBACK_FILE, "w") as f:
        json.dump(feedback, f)

def fetch_countries():
    """Fetch countries using REST Countries API"""
    try:
        url = "https://restcountries.com/v3.1/all?fields=name,cca2"
        response = requests.get(url)
        
        if response.status_code == 200:
            countries_data = response.json()
            countries_dict = {}
            for country in countries_data:
                country_name = country["name"]["common"]
                country_code = country["cca2"]
                countries_dict[country_name] = {"code": country_code}
            countries_dict = dict(sorted(countries_dict.items()))
            return countries_dict
        else:
            return _get_fallback_countries()
    except Exception as e:
        print(f"Error fetching countries: {str(e)}")
        return _get_fallback_countries()

def _get_fallback_countries():
    """Return a hardcoded list of major countries as fallback"""
    return {
        "India": {"code": "IN"},
        "United States": {"code": "US"},
        "United Kingdom": {"code": "GB"},
        "Japan": {"code": "JP"},
        "Australia": {"code": "AU"},
        "Canada": {"code": "CA"},
        "Germany": {"code": "DE"},
        "France": {"code": "FR"},
        "Italy": {"code": "IT"},
        "Brazil": {"code": "BR"},
        "China": {"code": "CN"},
        "Russia": {"code": "RU"},
        "South Africa": {"code": "ZA"},
        "Mexico": {"code": "MX"},
        "Singapore": {"code": "SG"},
        "Thailand": {"code": "TH"}
    }

# New functions to get states and cities using Gemini (Google Generative AI)
def get_states_from_gemini(country):
    prompt = f"List all states or provinces in {country}. Return the result as a comma-separated list."
    try:
        response = model.generate_content(prompt)
        if response.text:
            states = [state.strip() for state in response.text.split(',')]
            return states
        else:
            return ["State not available"]
    except Exception as e:
        print(f"Error fetching states from Gemini: {e}")
        return ["State not available"]

def get_cities_from_gemini(state):
    prompt = f"List all cities in {state}. Return the result as a comma-separated list. List as many as you can and only return a list of comma separated cities without any extra text. Use whatever definition of a 'city' you find correct or refer to your own knowledge. Don't worry about being incorrect, just name all cities according to google maps."
    try:
        response = model.generate_content(prompt)
        if response.text:
            cities = [city.strip() for city in response.text.split(',')]
            return cities
        else:
            return ["City not available"]
    except Exception as e:
        print(f"Error fetching cities from Gemini: {e}")
        return ["City not available"]

def display_weather(city):
    """Display current weather for the selected city"""
    try:
        weather_data = get_weather(city)
        if weather_data and 'current' in weather_data and weather_data['current']:
            with st.expander("🌤️ Current Weather", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Temperature", f"{weather_data['current']['temperature']}°C")
                    if 'humidity' in weather_data['current'] and weather_data['current']['humidity']:
                        st.metric("Humidity", f"{weather_data['current']['humidity']}%")
                with col2:
                    st.write(f"**Condition:** {weather_data['current']['condition']}")
                    if 'wind_speed' in weather_data['current'] and weather_data['current']['wind_speed']:
                        st.write(f"**Wind:** {weather_data['current']['wind_speed']} km/h")
                if 'forecast' in weather_data and weather_data['forecast']:
                    st.write("### 3-Day Forecast")
                    forecast_cols = st.columns(min(3, len(weather_data['forecast'])))
                    for i, forecast in enumerate(weather_data['forecast'][:3]):
                        with forecast_cols[i]:
                            st.write(f"**Day {i+1}**")
                            st.write(f"Weather: {forecast['weather']}")
                            st.write(f"Temp: {forecast['temperature']}°C")
    except Exception as e:
        print(f"Error displaying weather: {str(e)}")

def login_page():
    st.title("Login")
    st.markdown("""
    <style>
        .stButton button {
            background-color: #4CAF50;
            color: white;
            width: 100%;
        }
    </style>
    """, unsafe_allow_html=True)
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        users = load_users()
        if username in users and users[username] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("Logged in successfully!")
            st.rerun()
        else:
            st.error("Invalid credentials")

def signup_page():
    st.title("Sign Up")
    st.markdown("""
    <style>
        .stButton button {
            background-color: #008CBA;
            color: white;
            width: 100%;
        }
    </style>
    """, unsafe_allow_html=True)
    
    new_user = st.text_input("New Username")
    new_pass = st.text_input("New Password", type="password")
    confirm_pass = st.text_input("Confirm Password", type="password")
    
    if st.button("Create Account"):
        if not new_user or not new_pass:
            st.error("Please fill in all fields")
        else:
            users = load_users()
            if new_user in users:
                st.error("Username already exists")
            elif new_pass != confirm_pass:
                st.error("Passwords don't match")
            else:
                save_user(new_user, new_pass)
                st.success("Account created! Please login")
##########
def generate_itinerary(destination, duration, budget, interests, use_weather=True, weather_city=None):
    try:
        weather_info = ""
        if use_weather:
            try:
                # Use the specific city name for weather API, or fallback to destination
                city_for_weather = weather_city if weather_city else destination.split('+')[0]
                weather = get_weather(city_for_weather)
                if weather and 'current' in weather and weather['current'] and 'forecast' in weather and weather['forecast']:
                    weather_info = f"""
**Weather Report for {destination}:**

Current Weather: {weather['current']['condition']}, {weather['current']['temperature']}°C

**Forecast for the next {min(duration, len(weather['forecast']))} days:**

{chr(10).join([f"Day {i+1}: {forecast['weather']}, {forecast['temperature']}°C" for i, forecast in enumerate(weather['forecast'][:duration])])}

"""
            except Exception as e:
                print(f"Error getting weather for itinerary: {str(e)}")

        prompt = f"""
        {weather_info}
        Create a {duration}-day itinerary for {destination} with a budget of ₹{budget} INR.
        Interests: {interests}.
        
        Format each day as:
        # **Day X:**
        • Stay: [Hotel name] (near [famous landmarks/areas], ₹[price]/night)
        
        • Morning: [Activity/Place description and details]
          ◦ Transportation: [How to get there - subway/bus/walk/taxi] from hotel (with cost in ₹)
          ◦ Location: [Place name] - [Map](https://www.google.com/maps/search/?api=1&query=PLACE_NAME_HERE+{destination})
        
        • Afternoon: [Activity/Place description and details]
          ◦ Transportation: [How to get there] from morning location (with cost in ₹)
          ◦ Location: [Place name] - [Map](https://www.google.com/maps/search/?api=1&query=PLACE_NAME_HERE+{destination})
        
        • Evening: [Activity/Place description and details]
          ◦ Transportation: [How to get there] from afternoon location (with cost in ₹)
          ◦ Location: [Place name] - [Map](https://www.google.com/maps/search/?api=1&query=PLACE_NAME_HERE+{destination})
        
        • Night: [Activity/Place description and details] (if any)
          ◦ Transportation: [How to get there] and back to hotel (with cost in ₹)
          ◦ Location: [Place name] - [Map](https://www.google.com/maps/search/?api=1&query=PLACE_NAME_HERE+{destination})
        
        Daily Cost Summary:
        - Hotel: ₹[price]/night
        - Transportation: ₹[total transport cost]
        - Activities/Entrance fees: ₹[total activities cost]
        - Total for Day X: ₹[daily total]

        After all days are listed, include:

        Total Trip Cost Summary:
        - Total Hotel Costs: ₹[sum of all hotel costs]
        - Total Transportation: ₹[sum of all transport costs]
        - Total Activities: ₹[sum of all activity costs]
        - Grand Total: ₹[total trip cost]

        EXTREMELY IMPORTANT: For each location mentioned, the word "Map" should be a clickable markdown hyperlink. The exact proper markdown syntax must be used, which is: [Map](URL). 

        For example:
        ◦ Location: Taj Mahal - [Map](https://www.google.com/maps/search/?api=1&query=Taj+Mahal+Agra+India)

        In this example, only the word "Map" is visible and clickable, and clicking it takes the user to the URL.

        When creating map links, replace spaces with plus signs (+) in both the place name and destination parts of the URL.

        Note: All prices should be in Indian Rupees (₹). Only the 'Day X:' headers should be bold and large (#). All other text should be in normal size and font.
        
        Note: Include estimated transportation costs and times.
        
        Note: Each activity/place must have a map link formatted exactly as shown in the example.
        """
        client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
        )
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating itinerary: {str(e)}")
        return None
def feedback_page():
    if not st.session_state.get('logged_in', False):
        st.error("Please login first")
        return

    st.title("Share Your Travel Feedback 📝")
    st.subheader(f"Welcome {st.session_state.username}!")

    feedback_data = load_feedback()
    user_feedback = feedback_data.get(st.session_state.username, [])
    
    st.markdown("### Submit New Feedback")
    destination = st.text_input("🌍 Destination")
    rating = st.slider("Rate your experience (1-10) ⭐", 1, 10, 5)
    feedback_text = st.text_area("Drop your review & help others travel smarter")
    
    if st.button("Submit Feedback"):
        if destination and feedback_text:
            save_feedback(st.session_state.username, destination, rating, feedback_text)
            st.success("Thank you for your feedback! 🙏")
            st.rerun()
        else:
            st.error("Please fill in all fields")

    if user_feedback:
        st.markdown("### Your Previous Feedback")
        for idx, feedback in enumerate(reversed(user_feedback)):
            with st.expander(f"{feedback['destination']} - {feedback['date'][:10]}"):
                st.write(f"Rating: {'⭐' * int(feedback['rating'])} ({feedback['rating']}/10)")
                st.write(f"Comment: {feedback['comment']}")

def travel_planner():

    # 🔁 NEW: State tracking
    if "generated" not in st.session_state:
        st.session_state.generated = False
    if "last_itinerary" not in st.session_state:
        st.session_state.last_itinerary = ""
    if "last_inputs" not in st.session_state:
        st.session_state.last_inputs = {}

    #"""Main travel planner function with fixed variable scope"""
    if not st.session_state.get('logged_in', False):
        st.error("Please login first")
        return

    st.title(f"Travel Itinerary Planner")
    st.subheader(f"Welcome {st.session_state.username}! 🌎")
    
    st.markdown("""
    <style>
        .stButton button {
            background-color: #4CAF50;
            color: white;
        }
        .stSelectbox {
            color: #4CAF50;
        }
    </style>
    """, unsafe_allow_html=True)
    
    if 'countries' not in st.session_state:
        st.session_state.countries = fetch_countries()
    if 'selected_country' not in st.session_state:
        st.session_state.selected_country = None
    if 'selected_state' not in st.session_state:
        st.session_state.selected_state = None
    if 'selected_city' not in st.session_state:
        st.session_state.selected_city = None
    
    if 'states_cache' not in st.session_state:
        st.session_state.states_cache = {}
    if 'cities_cache' not in st.session_state:
        st.session_state.cities_cache = {}
    
    col1, col2, col3 = st.columns(3)
    
    # Country selection remains unchanged
    with col1:
        country_list = list(st.session_state.countries.keys())
        country_index = 0

        if st.session_state.selected_country is None:
            st.session_state.selected_country = "India"
        
        if st.session_state.selected_country is not None:
            try:
                country_index = country_list.index(st.session_state.selected_country)
            except ValueError:
                country_index = 0
        
        selected_country = st.selectbox(
            "🌏 Select Country",
            options=country_list,
            index=country_index
        )
        
        if st.session_state.selected_country != selected_country:
            st.session_state.selected_country = selected_country
            st.session_state.selected_state = None
            st.session_state.selected_city = None
            st.rerun()
    
    # State selection now uses Gemini to get states for the selected country
    with col2:
        with st.spinner("Loading states..."):
            if st.session_state.selected_country in st.session_state.states_cache:
                states = st.session_state.states_cache[st.session_state.selected_country]
            else:
                states = get_states_from_gemini(st.session_state.selected_country)
                st.session_state.states_cache[st.session_state.selected_country] = states
            if st.session_state.selected_state is None and "Karnataka" in states:
                st.session_state.selected_state = "Karnataka"


        state_index = 0
        if st.session_state.selected_state is not None:
            try:
                state_index = states.index(st.session_state.selected_state)
            except ValueError:
                state_index = 0
        
        selected_state = st.selectbox(
            "🏙️ Select State/Region",
            options=states,
            index=state_index
        )
        
        if st.session_state.selected_state != selected_state:
            st.session_state.selected_state = selected_state
            st.session_state.selected_city = None
            st.rerun()
    
    # City selection now uses Gemini to get cities for the selected state
    with col3:
        city_placeholder = st.empty()

        if st.session_state.selected_state and st.session_state.selected_state != "State not available":
            with st.spinner("Loading cities..."):
                cache_key = f"{st.session_state.selected_country}_{st.session_state.selected_state}"
                if cache_key in st.session_state.cities_cache:
                    cities = st.session_state.cities_cache[cache_key]
                else:
                    cities = get_cities_from_gemini(st.session_state.selected_state)
                    st.session_state.cities_cache[cache_key] = cities
                if st.session_state.selected_city is None and "Bangalore" in cities:
                    st.session_state.selected_city = "Bangalore"
            city_index = 0
            if st.session_state.selected_city is not None:
                try:
                    city_index = cities.index(st.session_state.selected_city)
                except ValueError:
                    city_index = 0
            selected_city = city_placeholder.selectbox(
                "🏙️ Select City",
                options=cities,
                index=city_index
            )
            
            st.session_state.selected_city = selected_city
        else:
            city_placeholder.selectbox(
                "🏙️ Select City",
                options=["Please select a state first"],
                disabled=True
            )
            st.session_state.selected_city = None
    
    if st.session_state.selected_city and st.session_state.selected_city not in ["City not available", "Please select a state first"]:
        display_weather(st.session_state.selected_city)
    
    col1, col2 = st.columns(2)
    
    with col1:
        duration = st.number_input("📅 Duration (Days)", min_value=1, max_value=10, value=3)
    
    with col2:
        budget = st.number_input("💰 Budget (₹)", min_value=8000, max_value=400000, value=65000)
    
    interests = st.text_area("🎯  Help us to plan the perfect trip — what do you love? (comma-separated)", placeholder="e.g., Historical, Adventure, Nature")

    
    
    if st.button("Generate Itinerary ✈️"):
        if not st.session_state.selected_city or st.session_state.selected_city == "Please select a state first" or not interests:
            st.error("Please fill in all required fields")
        else:
            with st.spinner("🔄 Planning your dream trip..."):
                maps_destination = f"{st.session_state.selected_city}+{st.session_state.selected_state}+{st.session_state.selected_country}"
                weather_city = st.session_state.selected_city
                itinerary = generate_itinerary(maps_destination, duration, budget, interests, True, weather_city)
                if itinerary:
                    st.session_state.generated = True  # ✅ NEW
                    st.session_state.last_itinerary = itinerary
                    st.session_state.last_inputs = {
                        "destination": maps_destination,
                        "duration": duration,
                        "budget": budget,
                        "weather_city": weather_city
                    }
                    st.snow()
                    st.subheader("🗺️ Your Personalized Itinerary")
                    st.markdown(st.session_state.last_itinerary)
        
    # 🔁 NEW: Feedback Regeneration Section
    if st.session_state.generated:
        st.markdown("---")
        st.subheader("🔁 Refine Your Itinerary")
        new_interests = st.text_area("✏️ Change interests & regenerate", placeholder="e.g., Beaches, Nightlife")
        if st.button("Regenerate Itinerary 🔄"):
            if new_interests.strip() == "":
                st.warning("Please enter updated interests.")
            else:
                with st.spinner("Regenerating itinerary..."):
                    inputs = st.session_state.last_inputs
                    new_itinerary = generate_itinerary(
                        inputs["destination"], inputs["duration"], inputs["budget"], new_interests, True, inputs["weather_city"]
                    )
                    if new_itinerary:
                        st.session_state.last_itinerary = new_itinerary
                        st.markdown("### ✅ Updated Itinerary")
                        st.markdown(new_itinerary)




def main():
    st.set_page_config(
        page_title="Travel Planner",
        page_icon="✈️",
        layout="wide"
    )

    


    st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(
            rgba(0, 0, 0, 0.3), 
            rgba(0, 0, 0, 0.3)
        ),
        url("https://images.unsplash.com/photo-1507525428034-b723cf961d3e");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }
    </style>
    """,
    unsafe_allow_html=True
)



    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    st.sidebar.markdown("""
    <style>
        .sidebar .sidebar-content {
            background-color: #f0f2f6;
        }
    </style>
    """, unsafe_allow_html=True)

    st.sidebar.title("Navigation ✈️")
    page = st.sidebar.radio("", ["Login", "Sign Up", "Travel Planner", "Feedback"])

    if st.session_state.get('logged_in', False):
        if st.sidebar.button("Logout 👋"):
            st.session_state.clear()
            st.rerun()

    if page == "Login":
        login_page()
    elif page == "Sign Up":
        signup_page()
    elif page == "Travel Planner":
        if not st.session_state.get('logged_in', False):
            st.error("⚠️ Please login first")
            st.sidebar.radio("", ["Login"])
        else:
            travel_planner()
    elif page == "Feedback":
        feedback_page()

    st.sidebar.markdown("---")
    st.sidebar.markdown("Made with ❤️ by our Team")

if __name__ == "__main__":
    main()