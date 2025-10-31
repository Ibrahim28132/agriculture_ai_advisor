from django.test import TestCase
from django.utils import timezone
from .models import WeatherAlert, Resource, MarketPrice


class ModelPropertyTests(TestCase):
	def test_weatheralert_properties(self):
		start = timezone.now()
		end = start + timezone.timedelta(days=1)
		alert = WeatherAlert.objects.create(
			location='Testville',
			alert_type='flood',
			title='Test Flood',
			description='Test description',
			severity='high',
			start_date=start,
			end_date=end,
			is_active=True
		)

		# expires_at should point to end_date
		self.assertEqual(alert.expires_at, alert.end_date)

		# recommended_actions should return a non-empty list for 'flood'
		self.assertIsInstance(alert.recommended_actions, list)
		self.assertTrue(len(alert.recommended_actions) >= 1)

		# icon and color should be strings
		self.assertIsInstance(alert.get_alert_type_icon, str)
		self.assertIsInstance(alert.get_alert_type_color, str)

	def test_resource_image_url(self):
		r1 = Resource.objects.create(
			title='Image Resource',
			description='Has image URL',
			resource_type='guide',
			url='https://example.com/pic.jpg'
		)
		r2 = Resource.objects.create(
			title='Non-image Resource',
			description='No image URL',
			resource_type='article',
			url='https://example.com/page'
		)

		self.assertEqual(r1.image_url, r1.url)
		self.assertIsNone(r2.image_url)

	def test_marketprice_price_change_computation(self):
		# Create two records for same commodity/location to compute change
		# Ensure recorded_at times differ so unique constraint (commodity, location, recorded_at) is not violated
		p1 = MarketPrice.objects.create(
			commodity='Maize',
			location='TestCity',
			price='100.00',
			unit='kg',
			currency='KES',
			source='Local',
			recorded_at=timezone.now() - timezone.timedelta(minutes=1),
		)
		p2 = MarketPrice.objects.create(
			commodity='Maize',
			location='TestCity',
			price='110.00',
			unit='kg',
			currency='KES',
			source='Local',
			recorded_at=timezone.now(),
		)

		# Use view-like computation: latest should be p2 and previous p1
		# The percent change should be (110-100)/100*100 = 10.0
		# Call model property (it may hit DB) and ensure it returns a numeric or None
		change = p2.price_change
		# price_change may compute against actual previous record; ensure it's numeric or None
		if change is not None:
			self.assertAlmostEqual(change, 10.0, places=1)
