from django.contrib import admin
from .models import AgriculturalQuery, WeatherData, CropAdvice

@admin.register(AgriculturalQuery)
class AgriculturalQueryAdmin(admin.ModelAdmin):
    list_display = ['location', 'crop_type', 'language', 'created_at']
    list_filter = ['language', 'created_at']
    search_fields = ['query_text', 'location']

@admin.register(WeatherData)
class WeatherDataAdmin(admin.ModelAdmin):
    list_display = ['location', 'temperature', 'humidity', 'recorded_at']

@admin.register(CropAdvice)
class CropAdviceAdmin(admin.ModelAdmin):
    list_display = ['crop_name', 'season', 'created_at']