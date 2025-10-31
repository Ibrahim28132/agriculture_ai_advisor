from django.core.management.base import BaseCommand
from advisor_app.models import Resource, MarketPrice, WeatherAlert, AgriculturalQuery, Bookmark
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Populate sample data for resources, market prices, and weather alerts'

    def handle(self, *args, **options):
        self.stdout.write('Populating sample data...')

        # Create sample resources
        resources_data = [
            {
                'title': 'Sustainable Farming Practices Guide',
                'description': 'Comprehensive guide to sustainable agriculture techniques including crop rotation, organic farming, and water conservation.',
                'resource_type': 'guide',
                'url': 'https://example.com/sustainable-farming',
                'tags': 'sustainable, organic, water conservation',
                'is_featured': True,
            },
            {
                'title': 'Pest Management in Maize Farming',
                'description': 'Learn about common pests affecting maize crops and effective management strategies.',
                'resource_type': 'article',
                'url': 'https://example.com/maize-pests',
                'tags': 'maize, pests, management',
                'is_featured': True,
            },
            {
                'title': 'Soil Health and Fertility',
                'description': 'Understanding soil types, testing methods, and improving soil fertility for better crop yields.',
                'resource_type': 'guide',
                'url': 'https://example.com/soil-health',
                'tags': 'soil, fertility, testing',
                'is_featured': False,
            },
            {
                'title': 'Climate-Smart Agriculture',
                'description': 'Adapting farming practices to climate change with resilient crop varieties and weather forecasting.',
                'resource_type': 'research',
                'url': 'https://example.com/climate-smart',
                'tags': 'climate, adaptation, resilience',
                'is_featured': True,
            },
            {
                'title': 'Irrigation Techniques for Small Farms',
                'description': 'Various irrigation methods suitable for small-scale farmers including drip irrigation and rainwater harvesting.',
                'resource_type': 'video',
                'url': 'https://example.com/irrigation-video',
                'tags': 'irrigation, water, small farms',
                'is_featured': False,
            },
        ]

        for resource_data in resources_data:
            Resource.objects.get_or_create(
                title=resource_data['title'],
                defaults=resource_data
            )

        # Create sample market prices
        commodities = ['Maize', 'Rice', 'Wheat', 'Beans', 'Potatoes', 'Tomatoes']
        locations = ['Nairobi', 'Kisumu', 'Eldoret', 'Nakuru', 'Mombasa']
        sources = ['Ministry of Agriculture', 'Local Market', 'Farmers Union']

        for _ in range(50):
            MarketPrice.objects.get_or_create(
                commodity=random.choice(commodities),
                location=random.choice(locations),
                recorded_at=datetime.now() - timedelta(days=random.randint(0, 30)),
                defaults={
                    'price': round(random.uniform(50, 500), 2),
                    'unit': 'kg',
                    'currency': 'KES',
                    'source': random.choice(sources),
                }
            )

        # Create sample weather alerts
        alerts_data = [
            {
                'location': 'Kisumu',
                'alert_type': 'flood',
                'title': 'Flood Warning for Western Kenya',
                'description': 'Heavy rainfall expected in the next 48 hours. Rivers may overflow causing flooding in low-lying areas.',
                'severity': 'high',
                'start_date': datetime.now(),
                'end_date': datetime.now() + timedelta(days=2),
                'is_active': True,
            },
            {
                'location': 'Nakuru',
                'alert_type': 'frost',
                'title': 'Frost Warning',
                'description': 'Temperatures expected to drop below freezing. Protect sensitive crops from frost damage.',
                'severity': 'medium',
                'start_date': datetime.now(),
                'end_date': datetime.now() + timedelta(days=1),
                'is_active': True,
            },
            {
                'location': 'Mombasa',
                'alert_type': 'drought',
                'title': 'Drought Conditions Alert',
                'description': 'Extended dry period affecting crop growth. Implement water conservation measures.',
                'severity': 'high',
                'start_date': datetime.now() - timedelta(days=7),
                'end_date': datetime.now() + timedelta(days=14),
                'is_active': True,
            },
            {
                'location': 'Eldoret',
                'alert_type': 'heat',
                'title': 'Heat Wave Warning',
                'description': 'Extreme temperatures expected. Ensure adequate water supply for livestock and crops.',
                'severity': 'medium',
                'start_date': datetime.now(),
                'end_date': datetime.now() + timedelta(days=3),
                'is_active': True,
            },
        ]

        for alert_data in alerts_data:
            WeatherAlert.objects.get_or_create(
                title=alert_data['title'],
                location=alert_data['location'],
                defaults=alert_data
            )

        # Create a sample agricultural query and bookmark for anonymous session so bookmarks page shows sample content
        sample_query, _ = AgriculturalQuery.objects.get_or_create(
            query_text='How to prevent armyworms on maize?',
            defaults={
                'location': 'Kisumu',
                'crop_type': 'maize',
                'language': 'en',
                'response': 'Use integrated pest management: monitor fields regularly, use pheromone traps, encourage natural predators, and apply registered pesticides only when thresholds are exceeded.'
            }
        )

        Bookmark.objects.get_or_create(
            user_session='anonymous',
            query=sample_query,
            defaults={
                'title': 'Prevent armyworms on maize',
                'notes': 'Sample bookmark created by populate_sample_data'
            }
        )

        self.stdout.write(self.style.SUCCESS('Sample data populated successfully!'))
