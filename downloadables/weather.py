#!/usr/bin/env python3
"""
Weather Dashboard TUI Application
A terminal-based weather app with location selection and emoji visualizations.
There is no need to abuse my API, please dont use it in your own projects, create your own free API over at: weatherapi.com
i am using the free plan so there is no need to steal my API key :D
NEEDED PYTHON PACKAGES: requests, rich, textual, and curses-windows if your on windows.
"""
import curses
import time
import json
import sys
import os
from datetime import datetime, timedelta
import requests
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.table import Table
from rich import box
from rich.live import Live
from rich.columns import Columns
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Button, Static
from textual.containers import Container
from textual.reactive import reactive
from textual.screen import ModalScreen, Screen
from textual.binding import Binding
from textual.message import Message

# Weather condition emoji mappings
WEATHER_EMOJIS = {
    "clear": "☀️",
    "sunny": "☀️",
    "partly cloudy": "⛅",
    "cloudy": "☁️",
    "overcast": "☁️",
    "mist": "🌫️",
    "fog": "🌫️",
    "rain": "🌧️",
    "light rain": "🌦️",
    "heavy rain": "⛈️",
    "showers": "🌧️",
    "thunderstorm": "🌩️",
    "snow": "❄️",
    "light snow": "🌨️",
    "heavy snow": "❄️",
    "sleet": "🌨️",
    "hail": "🌨️",
    "windy": "💨",
}

def get_emoji_for_condition(condition_text):
    """Convert weather condition text to appropriate emoji"""
    try:
        condition_text = condition_text.lower()
        for key in WEATHER_EMOJIS:
            if key in condition_text:
                return WEATHER_EMOJIS[key]
        return "🌡️"  # Default emoji if no match
    except (AttributeError, TypeError):
        return "🌡️"  # Default emoji if there's an error

def get_weather_data(location):
    """Get weather data for a location using a real weather API"""
    try:
        # Replace this with your actual API key if you have one
        # Free API keys are available from weatherapi.com
        API_KEY = "9a12a34432c04023a8005457252903"  # Example key, may not work
        
        # Make a real API request
        url = f"https://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q={location}&days=5&aqi=no&alerts=no"
        
        # Send the request
        response = requests.get(url, timeout=10)
        
        # Check if request was successful
        if response.status_code == 200:
            data = response.json()
            return data
        elif response.status_code == 400:
            # 400 typically means the location wasn't found
            error_response = response.json()
            error_message = error_response.get('error', {}).get('message', 'Location not found')
            raise ValueError(f"API Error: {error_message}")
        else:
            # Other error codes
            raise ValueError(f"API Error: Status code {response.status_code}")
    
    except requests.exceptions.RequestException as e:
        # Network errors, timeouts, etc.
        raise ValueError(f"Connection error: {str(e)}")
    except ValueError as e:
        # Re-raise any ValueError (including our own)
        raise e
    except Exception as e:
        # Any other unexpected error
        raise ValueError(f"Unexpected error: {str(e)}")
        
    # If we're here, fall back to mock data
    # This is a fallback in case the API is unavailable
    parts = [part.strip() for part in location.split(',')]
    city = parts[0]
    region = parts[1] if len(parts) > 1 else ""
    country = parts[2] if len(parts) > 2 else ""
    
    import random
    random.seed(city.lower())
    
    current_date = datetime.now()
    temp_c = random.randint(0, 35)
    temp_f = int(temp_c * 9/5 + 32)
    
    conditions = ["Sunny", "Partly cloudy", "Cloudy", "Light rain", "Heavy rain"]
    condition = random.choice(conditions)
    
    mock_data = {
        "location": {
            "name": city,
            "region": region,
            "country": country,
            "localtime": current_date.strftime("%Y-%m-%d %H:%M")
        },
        "current": {
            "temp_c": temp_c,
            "temp_f": temp_f,
            "condition": {
                "text": condition,
                "icon": "//cdn.weatherapi.com/weather/64x64/day/116.png"
            },
            "wind_mph": random.randint(0, 30),
            "wind_kph": random.randint(0, 50),
            "wind_dir": random.choice(["N", "NE", "E", "SE", "S", "SW", "W", "NW"]),
            "pressure_mb": random.randint(980, 1030),
            "humidity": random.randint(30, 90),
            "feelslike_c": temp_c + random.randint(-3, 3),
            "feelslike_f": temp_f + random.randint(-5, 5),
            "uv": random.randint(1, 10)
        },
        "current": {
            "temp_c": 22.5,
            "temp_f": 72.5,
            "condition": {
                "text": "Partly cloudy",
                "icon": "//cdn.weatherapi.com/weather/64x64/day/116.png"
            },
            "wind_mph": 5.6,
            "wind_kph": 9.0,
            "wind_dir": "NW",
            "pressure_mb": 1012,
            "humidity": 65,
            "feelslike_c": 24.2,
            "feelslike_f": 75.6,
            "uv": 5
        },
        "forecast": {
            "forecastday": [
                {
                    "date": current_date.strftime("%Y-%m-%d"),
                    "day": {
                        "maxtemp_c": 25.6,
                        "maxtemp_f": 78.1,
                        "mintemp_c": 16.3,
                        "mintemp_f": 61.3,
                        "condition": {
                            "text": "Partly cloudy",
                        },
                        "daily_chance_of_rain": 20
                    },
                    "hour": [
                        {"time": f"{current_date.strftime('%Y-%m-%d')} 00:00", "temp_c": 18.2, "temp_f": 64.8, "condition": {"text": "Clear"}},
                        {"time": f"{current_date.strftime('%Y-%m-%d')} 03:00", "temp_c": 17.0, "temp_f": 62.6, "condition": {"text": "Clear"}},
                        {"time": f"{current_date.strftime('%Y-%m-%d')} 06:00", "temp_c": 16.8, "temp_f": 62.2, "condition": {"text": "Clear"}},
                        {"time": f"{current_date.strftime('%Y-%m-%d')} 09:00", "temp_c": 19.5, "temp_f": 67.1, "condition": {"text": "Sunny"}},
                        {"time": f"{current_date.strftime('%Y-%m-%d')} 12:00", "temp_c": 22.8, "temp_f": 73.0, "condition": {"text": "Sunny"}},
                        {"time": f"{current_date.strftime('%Y-%m-%d')} 15:00", "temp_c": 25.1, "temp_f": 77.2, "condition": {"text": "Partly cloudy"}},
                        {"time": f"{current_date.strftime('%Y-%m-%d')} 18:00", "temp_c": 23.4, "temp_f": 74.1, "condition": {"text": "Partly cloudy"}},
                        {"time": f"{current_date.strftime('%Y-%m-%d')} 21:00", "temp_c": 20.1, "temp_f": 68.2, "condition": {"text": "Clear"}}
                    ]
                },
                {
                    "date": (current_date + timedelta(days=1)).strftime("%Y-%m-%d"),
                    "day": {
                        "maxtemp_c": 27.2,
                        "maxtemp_f": 81.0,
                        "mintemp_c": 17.8,
                        "mintemp_f": 64.0,
                        "condition": {
                            "text": "Sunny",
                        },
                        "daily_chance_of_rain": 0
                    }
                },
                {
                    "date": (current_date + timedelta(days=2)).strftime("%Y-%m-%d"),
                    "day": {
                        "maxtemp_c": 26.5,
                        "maxtemp_f": 79.7,
                        "mintemp_c": 18.1,
                        "mintemp_f": 64.6,
                        "condition": {
                            "text": "Light rain",
                        },
                        "daily_chance_of_rain": 70
                    }
                },
                {
                    "date": (current_date + timedelta(days=3)).strftime("%Y-%m-%d"),
                    "day": {
                        "maxtemp_c": 23.0,
                        "maxtemp_f": 73.4,
                        "mintemp_c": 16.5,
                        "mintemp_f": 61.7,
                        "condition": {
                            "text": "Rain",
                        },
                        "daily_chance_of_rain": 90
                    }
                },
                {
                    "date": (current_date + timedelta(days=4)).strftime("%Y-%m-%d"),
                    "day": {
                        "maxtemp_c": 20.8,
                        "maxtemp_f": 69.4,
                        "mintemp_c": 15.7,
                        "mintemp_f": 60.3,
                        "condition": {
                            "text": "Cloudy",
                        },
                        "daily_chance_of_rain": 40
                    }
                }
            ]
        }
    }
    
    # Simulate API delay
    time.sleep(0.5)
    return mock_data

# Define the modal dialog for location input first
class LocationInputModal(ModalScreen):
    """Modal screen for location input"""
    
    def __init__(self, dashboard):
        super().__init__()
        self.dashboard = dashboard
    
    def compose(self) -> ComposeResult:
        yield Container(
            Static("Enter location (formats accepted):"),
            Static("- City name (e.g., London)"),
            Static("- City, Country (e.g., Paris, France)"),
            Static("- US/CA Zip code (e.g., 10001)"),
            Static("- UK Postcode (e.g., SW1)"),
            Static("- Latitude, Longitude (e.g., 40.7128,-74.0060)"),
            Input(placeholder="Enter location", id="location_input"),
            Button("Get Weather", id="submit"),
            id="dialog-container"
        )
    
    def on_mount(self):
        # Focus the input field
        self.query_one("#location_input").focus()
    
    def on_button_pressed(self, event):
        if event.button.id == "submit":
            location = self.query_one("#location_input").value
            if location:
                self.dismiss()
                self.dashboard.update_location(location)
    
    def on_input_submitted(self, event):
        location = event.value
        if location:
            self.dismiss()
            self.dashboard.update_location(location)

class LocationInput(Static):
    """Input widget for location search"""
    
    def on_mount(self):
        try:
            self.update_location()
        except Exception as e:
            self.update(Panel("Location Search", title="Error"))
    
    def update_location(self):
        """Update the location display"""
        try:
            location_text = self.app.current_location if hasattr(self.app, 'current_location') else "Unknown"
            self.update(Panel(f"📍 Current location: [b]{location_text}[/b]\nPress 's' to change location", title="Location"))
        except Exception as e:
            self.update(Panel("Error showing location", title="Location"))
    
    def on_show(self):
        """Update when the widget is shown"""
        self.update_location()
        
    def on_weather_dashboard_location_changed(self, event):
        """React to location changes in the dashboard"""
        self.update_location()

class CurrentWeather(Static):
    """Widget to display current weather conditions"""
    weather_data = reactive(None)
    use_celsius = reactive(True)
    
    def watch_weather_data(self, weather_data):
        """React to changes in weather data"""
        self.update(self._make_panel())
        
    def watch_use_celsius(self, use_celsius):
        """React to temperature unit changes"""
        self.update(self._make_panel())
    
    def _make_panel(self):
        """Create a panel with current weather information"""
        if not self.weather_data:
            return Panel("Loading weather data...")
        
        try:
            current = self.weather_data["current"]
            location = self.weather_data["location"]
            
            # Debug print to see what's in the location data
            print(f"Current weather location data: {location}")
            
            condition_text = current["condition"]["text"]
            emoji = get_emoji_for_condition(condition_text)
            
            # Choose temperature unit
            temp = f"{current['temp_c']}°C" if self.use_celsius else f"{current['temp_f']}°F"
            feels_like = f"{current['feelslike_c']}°C" if self.use_celsius else f"{current['feelslike_f']}°F"
            
            # Format location string based on available data
            location_str = location['name']
            
            if location.get('region') and location['region'].strip():
                location_str += f", {location['region']}"
                
            if location.get('country') and location['country'].strip():
                location_str += f", {location['country']}"
            
            current_info = Text.from_markup(f"""
[bold]{location_str}[/bold]
🕒 Local time: {location['localtime']}

{emoji} [bold]{condition_text}[/bold]

🌡️ Temperature: {temp}
🧥 Feels like: {feels_like}
💧 Humidity: {current['humidity']}%
💨 Wind: {current['wind_kph']} km/h {current['wind_dir']}
🧭 Pressure: {current['pressure_mb']} mb
☀️ UV Index: {current['uv']}
            """)
            
            unit_text = "°C" if self.use_celsius else "°F"
            return Panel(current_info, title=f"Current Weather ({unit_text})", border_style="blue")
        except (KeyError, IndexError) as e:
            # Graceful error handling
            return Panel(f"Unable to display current weather: {str(e)}", title="Current Weather", border_style="blue")

class ForecastWidget(Static):
    """Widget to display forecast information"""
    weather_data = reactive(None)
    use_celsius = reactive(True)
    
    def watch_weather_data(self, weather_data):
        """React to changes in weather data"""
        self.update(self._make_panel())
        
    def watch_use_celsius(self, use_celsius):
        """React to temperature unit changes"""
        self.update(self._make_panel())
    
    def _make_panel(self):
        """Create a panel with forecast information"""
        if not self.weather_data:
            return Panel("Loading forecast data...")
        
        try:
            forecast_days = self.weather_data["forecast"]["forecastday"]
            
            table = Table(box=box.SIMPLE)
            table.add_column("Date")
            table.add_column("Condition")
            table.add_column("High")
            table.add_column("Low")
            table.add_column("Rain")
            
            for day in forecast_days:
                try:
                    date = datetime.strptime(day["date"], "%Y-%m-%d").strftime("%a, %b %d")
                    condition = day["day"]["condition"]["text"]
                    emoji = get_emoji_for_condition(condition)
                    
                    # Choose temperature unit
                    high = f"{day['day']['maxtemp_c']}°C" if self.use_celsius else f"{day['day']['maxtemp_f']}°F"
                    low = f"{day['day']['mintemp_c']}°C" if self.use_celsius else f"{day['day']['mintemp_f']}°F"
                    
                    rain_chance = f"{day['day']['daily_chance_of_rain']}%"
                    
                    table.add_row(
                        date,
                        f"{emoji} {condition}",
                        high,
                        low,
                        rain_chance
                    )
                except (KeyError, ValueError) as e:
                    # Skip problematic days
                    continue
            
            unit_text = "°C" if self.use_celsius else "°F"
            return Panel(table, title=f"5-Day Forecast ({unit_text})", border_style="green")
        except (KeyError, IndexError) as e:
            # Graceful error handling
            return Panel(f"Unable to display forecast: {str(e)}", title="5-Day Forecast", border_style="green")

class HourlyForecastWidget(Static):
    """Widget to display hourly forecast information for the current day"""
    weather_data = reactive(None)
    use_celsius = reactive(True)
    
    def watch_weather_data(self, weather_data):
        """React to changes in weather data"""
        self.update(self._make_panel())
        
    def watch_use_celsius(self, use_celsius):
        """React to temperature unit changes"""
        self.update(self._make_panel())
    
    def _make_panel(self):
        """Create a panel with hourly forecast information"""
        if not self.weather_data:
            return Panel("Loading hourly forecast data...")
        
        try:
            hours = self.weather_data["forecast"]["forecastday"][0]["hour"]
            
            # Only show future hours or a selection of hours throughout the day
            current_hour = datetime.now().hour
            
            # Select hours to display
            try:
                selected_hours = hours[current_hour::3]  # Every 3 hours from current hour
                if len(selected_hours) < 3:
                    selected_hours = hours[::3][:8]  # Just take 8 entries, every 3 hours
            except IndexError:
                # Fallback if there's an issue with the selection
                selected_hours = hours[::3][:3]  # Take first few entries
            
            table = Table(box=box.SIMPLE)
            table.add_column("Time")
            table.add_column("Temp")
            table.add_column("Condition")
            
            for hour in selected_hours:
                try:
                    # Try to parse time in format "YYYY-MM-DD HH:MM"
                    if " " in hour["time"]:
                        time_str = hour["time"].split(" ")[1]
                    else:
                        # Fallback if the time format is unexpected
                        time_str = hour["time"]
                    
                    # Choose temperature unit
                    temp = f"{hour['temp_c']}°C" if self.use_celsius else f"{hour['temp_f']}°F"
                    
                    condition = hour["condition"]["text"]
                    emoji = get_emoji_for_condition(condition)
                    
                    table.add_row(
                        time_str,
                        temp,
                        f"{emoji} {condition}"
                    )
                except (KeyError, IndexError) as e:
                    # Skip problematic entries
                    continue
            
            unit_text = "°C" if self.use_celsius else "°F"
            return Panel(table, title=f"Hourly Forecast ({unit_text})", border_style="yellow")
            
        except (KeyError, IndexError) as e:
            # Graceful error handling
            return Panel(f"Unable to display hourly forecast: {str(e)}", title="Hourly Forecast", border_style="yellow")

class WeatherDashboard(App):
    """Main Weather Dashboard Application"""
    
    BINDINGS = [
        ("s", "location_search", "Search Location"),
        ("r", "refresh", "Refresh"),
        ("u", "toggle_units", "Toggle °C/°F"),
        ("q", "quit", "Quit")
    ]
    
    def __init__(self, *args, **kwargs):
        self.weather_data = None
        self.current_location = "London, UK"  # Default location
        self.use_celsius = True  # Default to Celsius
        super().__init__(*args, **kwargs)
        self.title = "Weather Dashboard"
        self.sub_title = "Press 's' to search, 'r' to refresh, 'u' to toggle units, 'q' to quit"
    
    async def on_mount(self) -> None:
        """Set up the application layout"""
        try:
            # Create widgets
            self.location_input = LocationInput()
            self.current_weather = CurrentWeather()
            self.forecast = ForecastWidget()
            self.hourly = HourlyForecastWidget()
            
            # Create main container with all weather widgets
            main_container = Container(
                self.location_input,
                self.current_weather,
                self.forecast,
                self.hourly
            )
            
            # Mount the widgets to the app
            await self.mount(Header())
            await self.mount(main_container)
            await self.mount(Footer())
            
            # Load initial weather data
            self.load_location(self.current_location)
        except Exception as e:
            # Fallback if there's an issue during initialization
            error_widget = Static(f"Error initializing application: {str(e)}")
            await self.mount(error_widget)
    
    def load_location(self, location):
        """Process a new location entered by the user"""
        if not location:
            return
            
        print(f"Loading weather for: {location}")
        
        # Update the location display first
        old_location = self.current_location
        self.current_location = location
        
        # Update app title
        self.title = f"Weather Dashboard - {location}"
        
        # Now load the weather data
        try:
            # Get the weather data
            self.weather_data = get_weather_data(location)
            
            # Update widgets with new data
            if hasattr(self, 'current_weather'):
                self.current_weather.weather_data = self.weather_data
            if hasattr(self, 'forecast'):
                self.forecast.weather_data = self.weather_data
            if hasattr(self, 'hourly'):
                self.hourly.weather_data = self.weather_data
            
            # Show success notification
            self.notify(f"Weather updated for {location}")
            
            # Force update of location display
            if hasattr(self, 'location_input'):
                self.location_input.update_location()
                
        except Exception as e:
            # Log the error but don't crash
            print(f"Error loading weather data: {str(e)}")
            self.notify(f"Error: Could not load weather for {location}", severity="error")
    
    def load_weather_data(self, location):
        """Load weather data for a given location"""
        try:
            # Update the title immediately
            self.title = f"Weather Dashboard - {location}"
            
            # Show a notification that we're loading
            self.notify(f"Loading weather data for {location}")
            
            # Get weather data
            weather_data = get_weather_data(location)
            
            # Update the stored data
            self.weather_data = weather_data
            
            # Update the widgets with new data
            if hasattr(self, 'current_weather'):
                self.current_weather.weather_data = weather_data
            
            if hasattr(self, 'forecast'):  
                self.forecast.weather_data = weather_data
                
            if hasattr(self, 'hourly'):
                self.hourly.weather_data = weather_data
            
            # Force redraw
            self.refresh()
            
            # Show success notification
            self.notify(f"Weather updated for {location}")
            
        except Exception as e:
            # Log the error but don't crash
            print(f"Error loading weather data: {str(e)}")
            self.notify(f"Error: {str(e)}", severity="error")
    
    class LocationChanged(Message):
        """Event sent when location changes"""
        def __init__(self, old, new):
            super().__init__()
            self.old = old
            self.new = new
    
    def update_location(self, location):
        """Update the location and refresh weather data"""
        # Show loading notification
        self.notify(f"Searching for location: {location}...")
        
        try:
            # Try to get weather data (this will validate the location via API)
            weather_data = get_weather_data(location)
            
            # Extract the properly formatted location from the API response
            formatted_location = f"{weather_data['location']['name']}, {weather_data['location']['country']}"
            
            # Update current location with properly formatted version
            self.current_location = formatted_location
            
            # Update title
            self.title = f"Weather Dashboard - {formatted_location}"
            
            # Save weather data
            self.weather_data = weather_data
            
            # Update all widgets
            self.current_weather.weather_data = weather_data
            self.forecast.weather_data = weather_data
            self.hourly.weather_data = weather_data
            
            # Update location display
            self.location_input.update_location()
            
            # Show confirmation
            self.notify(f"Weather updated for {formatted_location}")
            
        except Exception as e:
            # Show error if location is invalid
            error_message = str(e)
            self.notify(f"Error: {error_message}", severity="error")
            
            # Log the error
            print(f"Weather API error: {error_message}")
    
    def action_location_search(self) -> None:
        """Action handler for location search"""
        location_modal = LocationInputModal(self)
        self.push_screen(location_modal)
    
    def action_toggle_units(self) -> None:
        """Toggle between Celsius and Fahrenheit"""
        # Toggle the unit
        self.use_celsius = not self.use_celsius
        
        # Update temperature unit preference in all widgets
        if hasattr(self, 'current_weather'):
            self.current_weather.use_celsius = self.use_celsius
        if hasattr(self, 'forecast'):
            self.forecast.use_celsius = self.use_celsius
        if hasattr(self, 'hourly'):
            self.hourly.use_celsius = self.use_celsius
        
        # Show notification
        unit_text = "Celsius (°C)" if self.use_celsius else "Fahrenheit (°F)"
        self.notify(f"Switched to {unit_text}")
    
    def action_refresh(self):
        """Action to refresh weather data"""
        self.notify("Refreshing weather data...")
        self.load_weather_data(self.current_location)
    
    def action_quit(self):
        """Action to quit the application"""
        self.exit()
    
    async def on_key(self, event):
        """Directly handle key presses as a backup to the BINDINGS system"""
        key = event.key
        if key == "s":
            # Directly call the action method 
            self.action_location_search()
        elif key == "r":
            self.load_weather_data(self.current_location)
        elif key == "q":
            self.exit()
        # Note: We're not handling 'u' here to avoid double-triggering

def main():
    """Run the weather dashboard application"""
    parser = argparse.ArgumentParser(description="Weather Dashboard TUI Application")
    parser.add_argument(
        "-l", "--location", 
        type=str, 
        default="London, UK", 
        help="Default location to show weather for"
    )
    args = parser.parse_args()
    
    app = WeatherDashboard()
    app.current_location = args.location
    app.run()

if __name__ == "__main__":
    main()
