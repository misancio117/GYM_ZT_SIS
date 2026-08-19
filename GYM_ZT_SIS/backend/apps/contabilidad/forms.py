from django import forms
from django.utils import timezone
from .models import Egreso


class EgresoForm(forms.ModelForm):
    class Meta:
        model = Egreso
        fields = ['tipo', 'monto', 'fecha', 'descripcion']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Descripción del egreso (opcional)...'
            }),
        }
        labels = {
            'tipo': 'Tipo de Egreso',
            'monto': 'Monto (Bs.)',
            'fecha': 'Fecha',
            'descripcion': 'Descripción',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['fecha'].initial = timezone.now().date()
