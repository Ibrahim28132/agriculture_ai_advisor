from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db import models
import json
from .forms import AgriculturalQueryForm
from .agricultural_agent import agricultural_advisor, search_agricultural_info_direct
from .models import AgriculturalQuery, Bookmark, Resource, MarketPrice, WeatherAlert
from django.core.cache import cache
from django.views.decorators.http import require_GET
import requests
import os
from datetime import datetime, timedelta
from types import SimpleNamespace

def home(request):
    form = AgriculturalQueryForm()
    # Get featured resources
    featured_resources = Resource.objects.filter(is_featured=True)[:3]
    # Get active weather alerts
    active_alerts = WeatherAlert.objects.filter(is_active=True)[:5]
    return render(request, 'advisor_app/home.html', {
        'form': form,
        'featured_resources': featured_resources,
        'active_alerts': active_alerts
    })

@csrf_exempt
@require_http_methods(["POST"])
def get_agricultural_advice(request):
    try:
        data = json.loads(request.body)
        query = data.get('query', '')
        location = data.get('location', '')
        crop_type = data.get('crop_type', '')
        language = data.get('language', 'en')

        # Location is helpful but not mandatory for follow-up queries; require only a query
        if not query:
            return JsonResponse({
                'error': _('Query is required')
            }, status=400)

        # Get or initialize conversation history from session
        conversation_history = request.session.get('conversation_history', [])

        # Add current user message to history
        user_message = {
            'role': 'user',
            'content': query,
            'timestamp': str(data.get('timestamp', ''))
        }
        conversation_history.append(user_message)

        # Build conversation context for AI
        context_messages = []
        for msg in conversation_history[-10:]:  # Keep last 10 messages for context
            if msg['role'] == 'user':
                context_messages.append(f"User: {msg['content']}")
            elif msg['role'] == 'assistant':
                context_messages.append(f"Assistant: {msg['content']}")

        conversation_context = "\n".join(context_messages)

        # Enhance query with context and conversation history
        enhanced_query = f"""
        Location: {location}
        Crop Type: {crop_type if crop_type else 'Not specified'}

        Conversation History:
        {conversation_context}

        Current Query: {query}

        Please provide comprehensive agricultural advice considering:
        - Current weather conditions
        - Soil suitability
        - Seasonal factors
        - Sustainable practices
        - Potential challenges and solutions
        - Previous conversation context if applicable
        """

        # Get AI response
        response = agricultural_advisor.get_advice(enhanced_query, language)

        # If the advisor returned an empty response, provide a friendly fallback
        if not response or not str(response).strip():
            response = _('I could not generate a response at this time. Please try again later.')

        # Strip markdown from response
        import re
        response = re.sub(r'\*\*(.*?)\*\*', r'\1', response)  # Remove bold
        response = re.sub(r'\*(.*?)\*', r'\1', response)      # Remove italic
        response = re.sub(r'`(.*?)`', r'\1', response)        # Remove inline code
        response = re.sub(r'```.*?```', '', response, flags=re.DOTALL)  # Remove code blocks
        response = re.sub(r'#+\s*', '', response)             # Remove headers
        response = re.sub(r'^\s*[-*+]\s+', '', response, flags=re.MULTILINE)  # Remove list markers
        response = re.sub(r'\n\s*\n', '\n\n', response)       # Clean up extra newlines

        # Add AI response to conversation history
        ai_message = {
            'role': 'assistant',
            'content': response,
            'timestamp': str(data.get('timestamp', ''))
        }
        conversation_history.append(ai_message)

        # Keep only last 20 messages to prevent session bloat
        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]

        # Save conversation history to session
        request.session['conversation_history'] = conversation_history
        request.session.modified = True

        # Save to database (keep existing functionality)
        query_obj = AgriculturalQuery.objects.create(
            query_text=query,
            location=location,
            crop_type=crop_type,
            language=language,
            response=response
        )

        return JsonResponse({
            'response': response,
            'success': True,
            'conversation_id': len(conversation_history),  # For frontend tracking
            'query_id': query_obj.id
        })

    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'success': False
        }, status=500)

def query_history(request):
    queries = AgriculturalQuery.objects.all()[:10]
    return render(request, 'advisor_app/history.html', {'queries': queries})

def about(request):
    return render(request, 'advisor_app/about.html')

@require_http_methods(["GET"])
def get_conversation_history(request):
    """Return the conversation history from session"""
    conversation_history = request.session.get('conversation_history', [])
    return JsonResponse({'history': conversation_history})

@require_http_methods(["POST"])
def clear_conversation(request):
    """Clear the conversation history from session"""
    if 'conversation_history' in request.session:
        del request.session['conversation_history']
        request.session.modified = True
    return JsonResponse({'success': True})

@require_http_methods(["POST"])
def bookmark_query(request):
    """Bookmark a query for later reference"""
    try:
        data = json.loads(request.body)
        query_id = data.get('query_id')
        title = data.get('title', '')
        notes = data.get('notes', '')
        session_id = request.session.session_key or 'anonymous'

        query = AgriculturalQuery.objects.get(id=query_id)
        bookmark, created = Bookmark.objects.get_or_create(
            user_session=session_id,
            query=query,
            defaults={'title': title, 'notes': notes}
        )

        if not created:
            bookmark.title = title
            bookmark.notes = notes
            bookmark.save()

        return JsonResponse({'success': True, 'created': created})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def resources(request):
    """Display educational resources"""
    resource_type = request.GET.get('type', '')
    search_query = request.GET.get('q', '')
    resources = Resource.objects.all()
    external_results = None

    if resource_type:
        resources = resources.filter(resource_type=resource_type)
    if search_query:
        # Prefer Tavily search results when user is searching
        try:
            query_text = f"{resource_type} {search_query}".strip()
            # Use direct callable to avoid calling a StructuredTool wrapper
            raw = search_agricultural_info_direct(query_text)
            try:
                external_results = json.loads(raw)
            except Exception:
                external_results = [{'title': 'Search result', 'content': raw, 'url': ''}]
        except Exception as e:
            external_results = [{'title': 'Search error', 'content': str(e), 'url': ''}]

    paginator = Paginator(resources, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'advisor_app/resources.html', {
        'page_obj': page_obj,
        'resource_type': resource_type,
        'search_query': search_query,
        'external_results': external_results,
    })

def market_prices(request):
    """Display current market prices"""
    location = request.GET.get('location', '')
    commodity = request.GET.get('commodity', '')

    prices = MarketPrice.objects.all()
    external_prices = None

    if location:
        prices = prices.filter(location__icontains=location)
    if commodity:
        prices = prices.filter(commodity__icontains=commodity)

    # If user provided commodity/location, try Tavily search for quick external results
    if commodity or location:
        try:
            query_text = f"market prices {commodity} {location}".strip()
            raw = search_agricultural_info_direct(query_text)
            try:
                external_prices = json.loads(raw)
            except Exception:
                external_prices = [{'title': 'Search result', 'content': raw, 'url': ''}]
        except Exception as e:
            external_prices = [{'title': 'Search error', 'content': str(e), 'url': ''}]

    # Get latest prices for each commodity/location combination
    # We'll precompute a simple percent change relative to the previous record
    latest_prices = {}
    # Iterate ordered so the first seen per key is the latest, next is previous
    for price in prices.order_by('commodity', 'location', '-recorded_at'):
        key = f"{price.commodity}_{price.location}"
        if key not in latest_prices:
            # store latest price object
            latest_prices[key] = price
            # default placeholder for price_change; may be overwritten when we see a previous value
            setattr(price, 'price_change', None)
        else:
            # we already have latest; compute change between latest and this previous
            latest = latest_prices[key]
            try:
                prev_price = float(price.price)
                latest_price = float(latest.price)
                if prev_price != 0:
                    change = (latest_price - prev_price) / prev_price * 100.0
                    setattr(latest, 'price_change', round(change, 2))
                else:
                    setattr(latest, 'price_change', None)
            except Exception:
                setattr(latest, 'price_change', None)

    return render(request, 'advisor_app/market_prices.html', {
        'prices': list(latest_prices.values()),
        'location': location,
        'commodity': commodity,
        'external_prices': external_prices,
    })


@require_GET
def external_search(request):
    """AJAX endpoint: perform a Tavily search for a query and return JSON results.

    Uses caching to avoid repeated external calls for the same query.
    """
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'error': 'Missing query parameter q'}, status=400)

    cache_key = f"tavily:{q}"
    cached = cache.get(cache_key)
    if cached is not None:
        return JsonResponse({'results': cached, 'cached': True})

    try:
        raw = search_agricultural_info_direct(q)
        try:
            results = json.loads(raw)
        except Exception:
            results = [{'title': 'Search result', 'content': raw, 'url': ''}]

        # Cache for 10 minutes
        cache.set(cache_key, results, 60 * 10)
        return JsonResponse({'results': results, 'cached': False})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def weather_alerts(request):
    """Display weather alerts"""
    location = request.GET.get('location', '')
    alert_type = request.GET.get('type', '')

    # If no location provided, fall back to DB alerts
    if not location:
        alerts = WeatherAlert.objects.filter(is_active=True)
        if alert_type:
            alerts = alerts.filter(alert_type=alert_type)
        return render(request, 'advisor_app/weather_alerts.html', {
            'alerts': alerts,
            'location': location,
            'alert_type': alert_type
        })

    # When location is provided, fetch forecast from OpenWeather and generate lightweight alerts
    api_key = None
    try:
        api_key = os.getenv('OPENWEATHER_API_KEY')
    except Exception:
        api_key = None

    if not api_key:
        # Fall back to DB alerts if API key not configured
        alerts = WeatherAlert.objects.filter(is_active=True)
        return render(request, 'advisor_app/weather_alerts.html', {
            'alerts': alerts,
            'location': location,
            'alert_type': alert_type
        })

    # Try cache first
    cache_key = f"openweather:{location}".lower()
    cached_alerts = cache.get(cache_key)
    if cached_alerts is not None:
        # cached_alerts is list of dicts; convert to SimpleNamespace objects with expected properties
        alerts_objs = []
        for a in cached_alerts:
            alerts_objs.append(SimpleNamespace(**a))
        return render(request, 'advisor_app/weather_alerts.html', {
            'alerts': alerts_objs,
            'location': location,
            'alert_type': alert_type
        })

    # Call 5 day / 3 hour forecast
    url = 'http://api.openweathermap.org/data/2.5/forecast'
    params = {'q': location, 'appid': api_key, 'units': 'metric'}
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
    except Exception as e:
        # On error, fall back to DB
        alerts = WeatherAlert.objects.filter(is_active=True)
        return render(request, 'advisor_app/weather_alerts.html', {
            'alerts': alerts,
            'location': location,
            'alert_type': alert_type
        })

    # Analyze forecast for potential alerts using simple heuristics
    forecasts = data.get('list', [])
    detected = []
    now = datetime.utcnow()

    total_rain = 0.0
    max_temp = -9999.0
    min_temp = 9999.0
    for item in forecasts:
        main = item.get('main', {})
        temp = main.get('temp')
        if temp is not None:
            max_temp = max(max_temp, temp)
            min_temp = min(min_temp, temp)
        rain = 0.0
        if 'rain' in item:
            rain = item.get('rain', {}).get('3h', 0.0)
        total_rain += rain

    # Heuristics
    if total_rain >= 30.0:
        detected.append({'alert_type': 'flood', 'severity': 'high', 'title': f'Flood Risk in {location}', 'description': f'Forecasted heavy rainfall totaling {total_rain:.1f} mm over the forecast period.'})
    if max_temp >= 35.0:
        detected.append({'alert_type': 'heat', 'severity': 'medium', 'title': f'Heat Alert in {location}', 'description': f'High temperatures expected up to {max_temp:.1f}°C.'})
    if min_temp <= 0.0:
        detected.append({'alert_type': 'frost', 'severity': 'medium', 'title': f'Frost Warning in {location}', 'description': f'Low temperatures down to {min_temp:.1f}°C expected.'})

    # Build Alert objects for template
    alerts_objs = []
    for idx, d in enumerate(detected):
        start = now
        end = now + timedelta(days=2)
        a = {
            'location': location,
            'alert_type': d['alert_type'],
            'title': d['title'],
            'description': d['description'],
            'severity': d.get('severity', 'medium'),
            'start_date': start,
            'end_date': end,
            'is_active': True,
            'created_at': now,
        }

        # convert to object with expected properties and helper methods used in template
        obj = SimpleNamespace(**a)

        def get_icon(at):
            return {
                'flood': 'fa-water',
                'storm': 'fa-cloud-showers-heavy',
                'drought': 'fa-sun',
                'frost': 'fa-snowflake',
                'heat': 'fa-thermometer-full',
                'pest': 'fa-bug',
            }.get(at, 'fa-info-circle')

        def get_color(at):
            return {
                'flood': 'info',
                'storm': 'primary',
                'drought': 'warning',
                'frost': 'secondary',
                'heat': 'danger',
                'pest': 'danger',
            }.get(at, 'secondary')

        def recommended_actions_fn(at):
            return {
                'flood': ['Move livestock to higher ground', 'Secure stored inputs from water damage', 'Avoid low-lying fields'],
                'drought': ['Implement water conservation', 'Use drought-tolerant varieties'],
                'frost': ['Cover sensitive crops at night', 'Delay irrigation during cold nights'],
                'heat': ['Increase irrigation', 'Provide shade for seedlings and livestock'],
            }.get(at, [])

        # Attach helper attributes
        obj.get_alert_type_icon = get_icon(obj.alert_type)
        obj.get_alert_type_color = get_color(obj.alert_type)
        obj.recommended_actions = recommended_actions_fn(obj.alert_type)
        obj.expires_at = obj.end_date

        alerts_objs.append(obj)

    # Cache alerts for this location for 10 minutes
    try:
        cache.set(cache_key, [o.__dict__ for o in alerts_objs], 60 * 10)
    except Exception:
        pass

    return render(request, 'advisor_app/weather_alerts.html', {
        'alerts': alerts_objs,
        'location': location,
        'alert_type': alert_type
    })

def bookmarks(request):
    """Display user bookmarks"""
    session_id = request.session.session_key or 'anonymous'
    user_bookmarks = Bookmark.objects.filter(user_session=session_id).select_related('query')

    return render(request, 'advisor_app/bookmarks.html', {
        'bookmarks': user_bookmarks
    })
