from django import forms
from django.utils.translation import gettext_lazy as _

class AgriculturalQueryForm(forms.Form):
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('es', 'Spanish'),
        ('fr', 'French'),
        ('hi', 'Hindi'),
    ]
    
    CROP_CHOICES = [
        ('', 'Any Crop'),
        ('vegetables', 'Vegetables'),
        ('fruits', 'Fruits'),
        ('grains', 'Grains'),
        ('legumes', 'Legumes'),
        ('rice', 'Rice'),
        ('wheat', 'Wheat'),
        ('tomato', 'Tomato'),
    ]
    
    query = forms.CharField(
        label=_("Your Agricultural Question"),
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': _('e.g., What crops should I plant this season in my area?'),
            'class': 'form-control'
        }),
        max_length=1000
    )
    
    location = forms.CharField(
        label=_("Your Location"),
        widget=forms.TextInput(attrs={
            'placeholder': _('e.g., Punjab, India'),
            'class': 'form-control'
        }),
        max_length=255
    )
    
    crop_type = forms.ChoiceField(
        label=_("Crop Type (Optional)"),
        choices=CROP_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    language = forms.ChoiceField(
        label=_("Response Language"),
        choices=LANGUAGE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )