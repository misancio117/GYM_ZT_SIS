from django import forms
from .models import Caja


class AperturaCajaForm(forms.Form):
    monto_inicial = forms.DecimalField(
        max_digits=12, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'})
    )
