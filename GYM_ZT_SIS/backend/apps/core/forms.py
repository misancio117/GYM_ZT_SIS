from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.hashers import make_password, check_password
from .models import Usuario


class UsuarioCrearForm(UserCreationForm):
    pregunta_secreta = forms.CharField(
        required=False,
        label='Pregunta de seguridad',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: ¿Nombre de tu mascota?'}),
    )
    respuesta_secreta = forms.CharField(
        required=False,
        label='Respuesta secreta',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tu respuesta (se guardará cifrada)'}),
    )

    class Meta:
        model = Usuario
        fields = ['username', 'first_name', 'last_name', 'email', 'rol', 'password1', 'password2', 'pregunta_secreta', 'respuesta_secreta']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'rol': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        user = super().save(commit=False)
        respuesta = self.cleaned_data.get('respuesta_secreta', '').strip().lower()
        if respuesta:
            user.respuesta_secreta = make_password(respuesta)
        if commit:
            user.save()
        return user


class UsuarioEditarForm(forms.ModelForm):
    pregunta_secreta = forms.CharField(
        required=False,
        label='Pregunta de seguridad',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: ¿Nombre de tu mascota?'}),
    )
    respuesta_secreta = forms.CharField(
        required=False,
        label='Nueva respuesta secreta',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dejar vacío para no cambiar'}),
        help_text='Solo completa si quieres cambiar la respuesta actual.',
    )

    class Meta:
        model = Usuario
        fields = ['username', 'first_name', 'last_name', 'email', 'rol', 'is_active', 'pregunta_secreta', 'respuesta_secreta']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'rol': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        respuesta = self.cleaned_data.get('respuesta_secreta', '').strip().lower()
        if respuesta:
            user.respuesta_secreta = make_password(respuesta)
        if commit:
            user.save()
        return user


class UsuarioCambioPasswordAdminForm(forms.Form):
    new_password1 = forms.CharField(
        label="Nueva Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Nueva contraseña'}),
        help_text="Mínimo 8 caracteres."
    )
    new_password2 = forms.CharField(
        label="Confirmar Nueva Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repita la nueva contraseña'})
    )
    admin_password = forms.CharField(
        label="Tu Contraseña (Admin)",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirme su propia clave para validar'}),
        help_text="Por seguridad, introduce tu propia clave de administrador para confirmar este cambio."
    )

    def __init__(self, *args, **kwargs):
        self.admin_user = kwargs.pop('admin_user', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("new_password1")
        p2 = cleaned_data.get("new_password2")
        admin_pass = cleaned_data.get("admin_password")

        if p1 != p2:
            raise forms.ValidationError("Las nuevas contraseñas no coinciden.")

        if self.admin_user and admin_pass:
            if not self.admin_user.check_password(admin_pass):
                self.add_error('admin_password', "Tu contraseña de administrador es incorrecta.")

        return cleaned_data


class RecuperarPaso1Form(forms.Form):
    username = forms.CharField(
        label='Usuario',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingresa tu nombre de usuario', 'autofocus': True}),
    )

    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            user = Usuario.objects.get(username=username, is_active=True)
        except Usuario.DoesNotExist:
            raise forms.ValidationError('No se encontró un usuario activo con ese nombre.')
        if not user.pregunta_secreta or not user.respuesta_secreta:
            raise forms.ValidationError('Este usuario no tiene una pregunta de seguridad configurada. Contacta al administrador.')
        return username


class RecuperarPaso2Form(forms.Form):
    respuesta = forms.CharField(
        label='Tu respuesta',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Escribe tu respuesta', 'autofocus': True}),
    )
    nueva_password = forms.CharField(
        label='Nueva contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Nueva contraseña'}),
    )
    nueva_password2 = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repite la nueva contraseña'}),
    )

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('nueva_password')
        p2 = cleaned.get('nueva_password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        return cleaned
