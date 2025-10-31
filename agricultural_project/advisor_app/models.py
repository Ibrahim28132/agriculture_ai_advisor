from django.db import models
from django.utils.translation import gettext_lazy as _

class AgriculturalQuery(models.Model):
    query_text = models.TextField(_("Query Text"))
    location = models.CharField(_("Location"), max_length=255)
    crop_type = models.CharField(_("Crop Type"), max_length=100, blank=True)
    language = models.CharField(_("Language"), max_length=10, default='en')
    response = models.TextField(_("AI Response"))
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)

    class Meta:
        verbose_name = _("Agricultural Query")
        verbose_name_plural = _("Agricultural Queries")
        ordering = ['-created_at']

    def __str__(self):
        return f"Query from {self.location} - {self.created_at.date()}"

class WeatherData(models.Model):
    location = models.CharField(_("Location"), max_length=255)
    temperature = models.FloatField(_("Temperature"))
    humidity = models.FloatField(_("Humidity"))
    rainfall = models.FloatField(_("Rainfall"))
    recorded_at = models.DateTimeField(_("Recorded At"), auto_now_add=True)

    class Meta:
        verbose_name = _("Weather Data")
        verbose_name_plural = _("Weather Data")

class CropAdvice(models.Model):
    crop_name = models.CharField(_("Crop Name"), max_length=100)
    season = models.CharField(_("Season"), max_length=50)
    advice_text = models.TextField(_("Advice Text"))
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)

    class Meta:
        verbose_name = _("Crop Advice")
        verbose_name_plural = _("Crop Advice")

class Bookmark(models.Model):
    user_session = models.CharField(_("Session ID"), max_length=255)
    query = models.ForeignKey(AgriculturalQuery, on_delete=models.CASCADE)
    title = models.CharField(_("Custom Title"), max_length=200, blank=True)
    notes = models.TextField(_("Personal Notes"), blank=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)

    class Meta:
        verbose_name = _("Bookmark")
        verbose_name_plural = _("Bookmarks")
        unique_together = ['user_session', 'query']

    def __str__(self):
        return f"Bookmark: {self.title or self.query.query_text[:50]}"

class Resource(models.Model):
    RESOURCE_TYPES = [
        ('guide', _('Farming Guide')),
        ('video', _('Video Tutorial')),
        ('article', _('Article')),
        ('tool', _('Tool/Resource')),
        ('research', _('Research Paper')),
    ]

    title = models.CharField(_("Title"), max_length=200)
    description = models.TextField(_("Description"))
    resource_type = models.CharField(_("Type"), max_length=20, choices=RESOURCE_TYPES)
    url = models.URLField(_("URL"), blank=True)
    content = models.TextField(_("Content"), blank=True)
    tags = models.CharField(_("Tags"), max_length=500, blank=True, help_text=_("Comma-separated tags"))
    language = models.CharField(_("Language"), max_length=10, default='en')
    is_featured = models.BooleanField(_("Featured"), default=False)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)

    class Meta:
        verbose_name = _("Resource")
        verbose_name_plural = _("Resources")
        ordering = ['-is_featured', '-created_at']

    def __str__(self):
        return self.title

    @property
    def image_url(self):
        """Return an image URL if the resource URL points to an image, otherwise None.

        Templates check `resource.image_url` so this provides a safe accessor.
        """
        if not self.url:
            return None
        url_lower = self.url.lower()
        if any(url_lower.endswith(ext) for ext in ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg')):
            return self.url
        return None

class MarketPrice(models.Model):
    commodity = models.CharField(_("Commodity"), max_length=100)
    location = models.CharField(_("Location"), max_length=255)
    price = models.DecimalField(_("Price"), max_digits=10, decimal_places=2)
    unit = models.CharField(_("Unit"), max_length=20, default='kg')
    currency = models.CharField(_("Currency"), max_length=10, default='USD')
    source = models.CharField(_("Source"), max_length=100)
    recorded_at = models.DateTimeField(_("Recorded At"), auto_now_add=True)

    class Meta:
        verbose_name = _("Market Price")
        verbose_name_plural = _("Market Prices")
        ordering = ['-recorded_at']
        unique_together = ['commodity', 'location', 'recorded_at']

    def __str__(self):
        return f"{self.commodity} - {self.location}: {self.price} {self.currency}/{self.unit}"

    @property
    def price_change(self):
        """Compute a simple percentage change relative to the previous recorded price for same commodity/location.

        Returns a float rounded to 2 decimals or None if previous price not available.
        Keep DB access minimal: only one query per instance when accessed.
        """
        try:
            prev = MarketPrice.objects.filter(
                commodity=self.commodity,
                location=self.location,
                recorded_at__lt=self.recorded_at
            ).order_by('-recorded_at').first()
            if not prev:
                return None
            try:
                change = (float(self.price) - float(prev.price)) / float(prev.price) * 100.0
                return round(change, 2)
            except Exception:
                return None
        except Exception:
            return None

class WeatherAlert(models.Model):
    ALERT_TYPES = [
        ('frost', _('Frost Warning')),
        ('heat', _('Heat Wave')),
        ('drought', _('Drought')),
        ('flood', _('Flood Risk')),
        ('storm', _('Storm Warning')),
        ('pest', _('Pest Alert')),
    ]

    location = models.CharField(_("Location"), max_length=255)
    alert_type = models.CharField(_("Alert Type"), max_length=20, choices=ALERT_TYPES)
    title = models.CharField(_("Title"), max_length=200)
    description = models.TextField(_("Description"))
    severity = models.CharField(_("Severity"), max_length=20, choices=[
        ('low', _('Low')),
        ('medium', _('Medium')),
        ('high', _('High')),
        ('critical', _('Critical')),
    ])
    start_date = models.DateTimeField(_("Start Date"))
    end_date = models.DateTimeField(_("End Date"), null=True, blank=True)
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)

    class Meta:
        verbose_name = _("Weather Alert")
        verbose_name_plural = _("Weather Alerts")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.alert_type} - {self.location}: {self.title}"

    @property
    def expires_at(self):
        """Compatibility property used by templates (alias for end_date)."""
        return self.end_date

    @property
    def recommended_actions(self):
        """Return a small list of recommended actions based on alert type.

        Templates iterate over this if present. Keep it lightweight and safe.
        """
        actions_map = {
            'flood': [
                'Move livestock and equipment to higher ground',
                'Avoid low-lying and flood-prone areas',
                'Secure stored grain and inputs from water damage',
            ],
            'drought': [
                'Implement water conservation measures',
                'Prioritize drought-resistant crop varieties',
                'Stagger planting and use mulches to retain moisture',
            ],
            'frost': [
                'Cover sensitive crops at night',
                'Use wind machines or water irrigation carefully to reduce frost',
            ],
            'heat': [
                'Increase irrigation frequency',
                'Provide shade for young plants and livestock',
            ],
            'storm': [
                'Secure light structures and protect seedlings',
                'Harvest mature crops if safe to do so',
            ],
            'pest': [
                'Monitor fields regularly and use integrated pest management',
            ],
        }
        return actions_map.get(self.alert_type, [])

    @property
    def get_alert_type_icon(self):
        """Return a FontAwesome icon class suffix for the alert type used in templates.

        The template uses `fas {{ alert.get_alert_type_icon }}` so return e.g. 'fa-water'.
        """
        icon_map = {
            'flood': 'fa-water',
            'storm': 'fa-cloud-showers-heavy',
            'drought': 'fa-sun',
            'frost': 'fa-snowflake',
            'heat': 'fa-thermometer-full',
            'pest': 'fa-bug',
        }
        return icon_map.get(self.alert_type, 'fa-info-circle')

    @property
    def get_alert_type_color(self):
        """Return a Bootstrap color name (used in template class names) for the alert type."""
        color_map = {
            'flood': 'info',
            'storm': 'primary',
            'drought': 'warning',
            'frost': 'secondary',
            'heat': 'danger',
            'pest': 'danger',
        }
        return color_map.get(self.alert_type, 'secondary')
