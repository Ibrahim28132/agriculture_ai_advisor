from django.core.management.base import BaseCommand
from advisor_app.models import WeatherData
import requests
import os
from datetime import datetime

class Command(BaseCommand):
    help = 'Update weather data for agricultural locations'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--locations',
            nargs='+',
            default=['Punjab,India', 'California,USA', 'Nairobi,Kenya'],
            help='List of locations to update weather data for'
        )
    
    def handle(self, *args, **options):
        locations = options['locations']
        api_key = os.getenv('OPENWEATHER_API_KEY')
        
        if not api_key:
            self.stdout.write(
                self.style.ERROR('OpenWeather API key not configured')
            )
            return
        
        for location in locations:
            try:
                url = "http://api.openweathermap.org/data/2.5/weather"
                params = {
                    'q': location,
                    'appid': api_key,
                    'units': 'metric'
                }
                
                response = requests.get(url, params=params, timeout=10)
                data = response.json()
                
                if response.status_code == 200:
                    WeatherData.objects.create(
                        location=location,
                        temperature=data['main']['temp'],
                        humidity=data['main']['humidity'],
                        rainfall=data.get('rain', {}).get('1h', 0),
                    )
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Successfully updated weather data for {location}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Failed to get weather data for {location}: {data.get("message", "Unknown error")}'
                        )
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Error updating weather data for {location}: {str(e)}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS('Weather data update completed')
        )