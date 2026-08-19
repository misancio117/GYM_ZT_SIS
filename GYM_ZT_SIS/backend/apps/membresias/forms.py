from datetime import timedelta
from django import forms
from .models import Membresia, ClienteMembresia


class MembresiaForm(forms.ModelForm):
    class Meta:
        model = Membresia
        fields = ['nombre', 'precio', 'duracion_dias', 'estado', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'duracion_dias': forms.NumberInput(attrs={'class': 'form-control'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class AsignarMembresiaForm(forms.ModelForm):
    METODO_PAGO_CHOICES = [
        ('efectivo', '💵 Efectivo'),
        ('qr', '📱 QR'),
        ('transferencia', '🏦 Transferencia'),
    ]
    metodo_pago = forms.ChoiceField(
        choices=METODO_PAGO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Método de Pago',
    )

    class Meta:
        model = ClienteMembresia
        fields = ['cliente', 'membresia', 'fecha_inicio', 'peso_registro']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'membresia': forms.Select(attrs={'class': 'form-select'}),
            'fecha_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'peso_registro': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Peso Actual (Kg)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['membresia'].queryset = Membresia.objects.filter(estado=True)

    def clean(self):
        cleaned_data = super().clean()
        cliente = cleaned_data.get('cliente')
        membresia = cleaned_data.get('membresia')
        fecha_inicio = cleaned_data.get('fecha_inicio')

        if not (cliente and membresia and fecha_inicio):
            return cleaned_data

        fecha_fin_nueva = fecha_inicio + timedelta(days=membresia.duracion_dias)

        # Busca cualquier membresía activa o futura del cliente que se solape con el período nuevo.
        # Solapamiento: la existente termina después de que empieza la nueva
        #               Y la existente empieza antes de que termine la nueva.
        solapada = ClienteMembresia.objects.filter(
            cliente=cliente,
            estado='activa',
            fecha_fin__gte=fecha_inicio,
            fecha_inicio__lte=fecha_fin_nueva,
        ).select_related('membresia').first()

        if solapada:
            disponible_desde = solapada.fecha_fin + timedelta(days=1)
            raise forms.ValidationError(
                f'El cliente ya tiene la membresía "{solapada.membresia.nombre}" '
                f'vigente del {solapada.fecha_inicio.strftime("%d/%m/%Y")} '
                f'al {solapada.fecha_fin.strftime("%d/%m/%Y")}. '
                f'La próxima membresía puede iniciar desde el '
                f'{disponible_desde.strftime("%d/%m/%Y")}.'
            )

        return cleaned_data
