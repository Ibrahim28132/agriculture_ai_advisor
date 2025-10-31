from django.urls import path
from . import views

app_name = 'advisor_app'

urlpatterns = [
    path('', views.home, name='home'),
    path('get-advice/', views.get_agricultural_advice, name='get_advice'),
    path('conversation-history/', views.get_conversation_history, name='get_conversation_history'),
    path('clear-conversation/', views.clear_conversation, name='clear_conversation'),
    path('bookmark-query/', views.bookmark_query, name='bookmark_query'),
    path('history/', views.query_history, name='history'),
    path('about/', views.about, name='about'),
    path('resources/', views.resources, name='resources'),
    path('market-prices/', views.market_prices, name='market_prices'),
    path('weather-alerts/', views.weather_alerts, name='weather_alerts'),
    path('external-search/', views.external_search, name='external_search'),
    path('bookmarks/', views.bookmarks, name='bookmarks'),
]
