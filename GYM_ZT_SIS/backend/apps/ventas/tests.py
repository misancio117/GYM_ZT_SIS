import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from apps.inventario.models import Producto
from apps.caja.models import Caja, MovimientoCaja
from apps.ventas.models import Venta, DetalleVenta

Usuario = get_user_model()
URL = '/api/procesar/'


def _payload(producto_id, cantidad=2, precio=10.0, costo=6.0):
    subtotal = precio * cantidad
    costo_subtotal = costo * cantidad
    return {
        'metodo_pago': 'efectivo',
        'items': [{
            'tipo': 'producto',
            'descripcion': 'Producto test',
            'cantidad': cantidad,
            'precio_unitario': precio,
            'costo_unitario': costo,
            'subtotal': subtotal,
            'costo_subtotal': costo_subtotal,
            'producto_id': producto_id,
        }],
    }


class ProcesarVentaTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.usuario = Usuario.objects.create_user(
            username='cajero', password='pass1234', rol='empleado'
        )
        self.caja = Caja.objects.create(usuario=self.usuario, estado='abierta', monto_inicial=100)
        self.producto = Producto.objects.create(
            nombre='Proteína test', precio_venta=10, precio_compra=6, stock=10
        )
        self.client.login(username='cajero', password='pass1234')

    def _post(self, payload):
        return self.client.post(
            URL,
            data=json.dumps(payload),
            content_type='application/json',
        )

    def test_venta_crea_registro(self):
        """Procesar una venta crea Venta y DetalleVenta en la BD."""
        resp = self._post(_payload(self.producto.pk))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'], data.get('error'))
        self.assertEqual(Venta.objects.count(), 1)
        self.assertEqual(DetalleVenta.objects.count(), 1)

    def test_venta_descuenta_stock(self):
        """El stock del producto disminuye exactamente en la cantidad vendida."""
        self._post(_payload(self.producto.pk, cantidad=3))
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock, 7)

    def test_venta_registra_movimiento_caja(self):
        """Se crea un MovimientoCaja de tipo ingreso asociado a la caja abierta."""
        self._post(_payload(self.producto.pk))
        movimiento = MovimientoCaja.objects.filter(caja=self.caja, tipo='ingreso').first()
        self.assertIsNotNone(movimiento)
        self.assertEqual(float(movimiento.monto), 20.0)  # 2 unidades x Bs.10

    def test_rollback_si_producto_inexistente(self):
        """Si un producto_id no existe, no se guarda ninguna Venta ni se toca el stock."""
        payload = _payload(producto_id=99999)
        resp = self._post(payload)
        data = resp.json()
        self.assertFalse(data['success'])
        self.assertEqual(Venta.objects.count(), 0)
        self.assertEqual(MovimientoCaja.objects.filter(tipo='ingreso').count(), 0)

    def test_sin_caja_abierta_rechaza_venta(self):
        """Sin caja abierta el endpoint devuelve error y no crea registros."""
        self.caja.estado = 'cerrada'
        self.caja.save()
        resp = self._post(_payload(self.producto.pk))
        data = resp.json()
        self.assertFalse(data['success'])
        self.assertEqual(Venta.objects.count(), 0)
