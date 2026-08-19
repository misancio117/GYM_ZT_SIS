from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.clientes.models import Cliente
from apps.membresias.models import Membresia, ClienteMembresia
from apps.membresias.forms import AsignarMembresiaForm

Usuario = get_user_model()


def _hoy():
    return date.today()


class AsignarMembresiaValidacionTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(username='test', password='pass')
        self.cliente = Cliente.objects.create(nombre='Juan Pérez')
        self.plan_mensual = Membresia.objects.create(
            nombre='Mensual', precio=100, duracion_dias=30, estado=True
        )
        self.plan_quincenal = Membresia.objects.create(
            nombre='Quincenal', precio=60, duracion_dias=15, estado=True
        )

    def _form(self, fecha_inicio, membresia=None):
        return AsignarMembresiaForm(data={
            'cliente': self.cliente.pk,
            'membresia': (membresia or self.plan_mensual).pk,
            'fecha_inicio': fecha_inicio.isoformat(),
            'peso_registro': '',
        })

    def _crear_membresia_activa(self, fecha_inicio, plan=None):
        plan = plan or self.plan_mensual
        return ClienteMembresia.objects.create(
            cliente=self.cliente,
            membresia=plan,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_inicio + timedelta(days=plan.duracion_dias),
            estado='activa',
            usuario=self.usuario,
        )

    def test_primera_membresia_es_valida(self):
        """Sin membresías previas el formulario es válido."""
        form = self._form(fecha_inicio=_hoy())
        self.assertTrue(form.is_valid(), form.errors)

    def test_rechaza_misma_fecha_inicio(self):
        """No se puede asignar una membresía con la misma fecha de inicio que una activa."""
        self._crear_membresia_activa(_hoy())
        form = self._form(fecha_inicio=_hoy())
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)

    def test_rechaza_fecha_dentro_del_periodo_activo(self):
        """No se puede asignar una membresía que empiece dentro del período vigente."""
        self._crear_membresia_activa(_hoy())
        fecha_solapada = _hoy() + timedelta(days=15)  # mitad del mes activo
        form = self._form(fecha_inicio=fecha_solapada)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)

    def test_permite_membresia_futura_al_dia_siguiente_del_vencimiento(self):
        """Una membresía que empieza el día después del vencimiento es válida."""
        mem_activa = self._crear_membresia_activa(_hoy())
        fecha_siguiente = mem_activa.fecha_fin + timedelta(days=1)
        form = self._form(fecha_inicio=fecha_siguiente)
        self.assertTrue(form.is_valid(), form.errors)

    def test_rechaza_solapamiento_con_membresia_futura_ya_agendada(self):
        """No se puede solapar con una membresía futura ya asignada."""
        inicio_futura = _hoy() + timedelta(days=35)
        self._crear_membresia_activa(inicio_futura)
        # Intentar una que empieza antes pero termina dentro de la futura
        form = self._form(fecha_inicio=_hoy() + timedelta(days=30))
        self.assertFalse(form.is_valid())

    def test_membresia_expirada_no_bloquea_nueva(self):
        """Una membresía expirada no debe impedir asignar una nueva."""
        mem = self._crear_membresia_activa(_hoy() - timedelta(days=60))
        mem.estado = 'expirada'
        mem.save()
        form = self._form(fecha_inicio=_hoy())
        self.assertTrue(form.is_valid(), form.errors)

    def test_mensaje_error_indica_fecha_disponible(self):
        """El error debe incluir la fecha desde la que se puede asignar."""
        mem = self._crear_membresia_activa(_hoy())
        form = self._form(fecha_inicio=_hoy())
        form.is_valid()
        error_texto = str(form.errors['__all__'])
        fecha_esperada = (mem.fecha_fin + timedelta(days=1)).strftime('%d/%m/%Y')
        self.assertIn(fecha_esperada, error_texto)
