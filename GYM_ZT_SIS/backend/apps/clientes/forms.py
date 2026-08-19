from django import forms
from .models import Cliente


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'ubicacion', 'peso_inicial', 'telefono', 'foto', 'estado', 'notas']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre completo'}),
            'ubicacion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dirección / Zona'}),
            'peso_inicial': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono'}),
            'foto': forms.FileInput(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        nombre = cleaned_data.get('nombre')
        telefono = cleaned_data.get('telefono')

        if nombre and telefono:
            exists = Cliente.objects.filter(nombre__iexact=nombre, telefono=telefono)
            if self.instance.pk:
                exists = exists.exclude(pk=self.instance.pk)
            
            if exists.exists():
                raise forms.ValidationError(
                    f"Ya existe un cliente registrado con el nombre '{nombre}' y teléfono '{telefono}'."
                )

        return cleaned_data
