import requests
import streamlit as st
from datetime import datetime, timedelta

def get_weather(city="Tokyo"):
    API_KEY = "cb456f3fc138f080dcbc8649c80377cb"
    
    try:
        # Get current weather
        current_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        current_response = requests.get(current_url)
        
        if current_response.status_code != 200:
            st.error(f"Error getting current weather: {current_response.status_code}")
            return None
            
        current_data = current_response.json()
        
        # Get 5-day forecast
        forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric"
        forecast_response = requests.get(forecast_url)
        
        if forecast_response.status_code != 200:
            st.error(f"Error getting forecast: {forecast_response.status_code}")
            return None
            
        forecast_data = forecast_response.json()
        
        # Format current weather
        current = {
            "condition": current_data['weather'][0]['main'],
            "temperature": round(current_data['main']['temp'])
        }
        
        # Process forecast data
        forecast = []
        date_temps = {}
        
        for item in forecast_data['list']:
            date = item['dt_txt'].split()[0]
            if date not in date_temps:
                date_temps[date] = {
                    'temps': [],
                    'conditions': []
                }
            date_temps[date]['temps'].append(item['main']['temp'])
            date_temps[date]['conditions'].append(item['weather'][0]['main'])
        
        # Calculate daily averages
        for date, data in date_temps.items():
            avg_temp = sum(data['temps']) / len(data['temps'])
            # Get most common condition for the day
            condition = max(set(data['conditions']), key=data['conditions'].count)
            forecast.append({
                "weather": condition,
                "temperature": round(avg_temp)
            })
        
        return {
            "current": current,
            "forecast": forecast[:7]  # Limit to 7 days
        }
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None