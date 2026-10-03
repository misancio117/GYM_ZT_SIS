from django.contrib.auth.mixins import LoginRequiredMixin
from apps.core.utils import AdminRequeridoMixin
from django.views.generic import TemplateView
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Sum, Count, F, Q
from datetime import timedelta, date
import json
from apps.ventas.models import Venta, DetalleVenta
from apps.ventas.utils import calcular_ganancia_desglosada
from apps.asistencia.models import Asistencia, ClienteOcasional
from apps.clientes.models import Cliente
from apps.membresias.models import ClienteMembresia
from apps.contabilidad.models import Egreso
from apps.inventario.models import Producto


class ReportesView(AdminRequeridoMixin, LoginRequiredMixin, TemplateView):
    template_name = 'reportes/reportes.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tipo = self.request.GET.get('tipo', 'diario')
        hoy = date.today()

        if tipo == 'diario':
            fecha_str = self.request.GET.get('fecha', str(hoy))
            try:
                from datetime import datetime
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            except Exception:
                fecha = hoy
                fecha_str = str(hoy)

            ventas = Venta.objects.filter(fecha__date=fecha)
            egresos = Egreso.objects.filter(fecha=fecha)
            asistencias = Asistencia.objects.filter(fecha=fecha)
            ocasionales = ClienteOcasional.objects.filter(fecha=fecha)
            titulo = f"Reporte Diario: {fecha.strftime('%d/%m/%Y')}"
            ctx['fecha'] = fecha_str
            ctx['fecha_inicio'] = ''
            ctx['fecha_fin'] = ''
            ctx['mes'] = ''

        elif tipo == 'semanal':
            fecha_inicio_str = self.request.GET.get('fecha_inicio', str(hoy - timedelta(days=hoy.weekday())))
            fecha_fin_str = self.request.GET.get('fecha_fin', str(hoy))
            try:
                from datetime import datetime
                inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
                fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
            except Exception:
                inicio = hoy - timedelta(days=hoy.weekday())
                fin = hoy
                fecha_inicio_str = str(inicio)
                fecha_fin_str = str(fin)

            ventas = Venta.objects.filter(fecha__date__range=[inicio, fin])
            egresos = Egreso.objects.filter(fecha__range=[inicio, fin])
            asistencias = Asistencia.objects.filter(fecha__range=[inicio, fin])
            ocasionales = ClienteOcasional.objects.filter(fecha__range=[inicio, fin])
            titulo = f"Reporte Semanal: {inicio.strftime('%d/%m/%Y')} — {fin.strftime('%d/%m/%Y')}"
            ctx['fecha'] = ''
            ctx['fecha_inicio'] = fecha_inicio_str
            ctx['fecha_fin'] = fecha_fin_str
            ctx['mes'] = ''

        else:  # mensual
            mes_str = self.request.GET.get('mes', hoy.strftime('%Y-%m'))
            try:
                año, m = mes_str.split('-')
                año = int(año)
                m = int(m)
            except Exception:
                año = hoy.year
                m = hoy.month
                mes_str = hoy.strftime('%Y-%m')

            ventas = Venta.objects.filter(fecha__year=año, fecha__month=m)
            egresos = Egreso.objects.filter(fecha__year=año, fecha__month=m)
            asistencias = Asistencia.objects.filter(fecha__year=año, fecha__month=m)
            ocasionales = ClienteOcasional.objects.filter(fecha__year=año, fecha__month=m)
            meses_es = ['enero','febrero','marzo','abril','mayo','junio',
                        'julio','agosto','septiembre','octubre','noviembre','diciembre']
            titulo = f"Reporte Mensual: {meses_es[m-1].capitalize()} {año}"
            ctx['fecha'] = ''
            ctx['fecha_inicio'] = ''
            ctx['fecha_fin'] = ''
            ctx['mes'] = mes_str

        categoria = self.request.GET.get('categoria', 'all')

        # Filtros de area/categoria/disciplina
        if categoria in ['gym', 'gimnasio']:
            ventas = ventas.filter(
                Q(detalles__disciplina__in=['gimnasio', 'gym', '']) |
                Q(detalles__membresia__disciplina='gimnasio')
            ).distinct()
            ocasionales = ocasionales.filter(disciplina__in=['gimnasio', 'gym', ''])
            asistencias = asistencias.filter(disciplina__in=['gimnasio', 'gym', ''])
            egresos = egresos.none()
            titulo += " — Gimnasio"
        elif categoria == 'crossfit':
            ventas = ventas.filter(
                Q(detalles__disciplina='crossfit') |
                Q(detalles__membresia__disciplina='crossfit')
            ).distinct()
            ocasionales = ocasionales.filter(disciplina='crossfit')
            asistencias = asistencias.filter(disciplina='crossfit')
            egresos = egresos.none()
            titulo += " — Crossfit"
        elif categoria == 'kickboxing':
            ventas = ventas.filter(
                Q(detalles__disciplina='kickboxing') |
                Q(detalles__membresia__disciplina='kickboxing')
            ).distinct()
            ocasionales = ocasionales.filter(disciplina='kickboxing')
            asistencias = asistencias.filter(disciplina='kickboxing')
            egresos = egresos.none()
            titulo += " — Kick Boxing"
        elif categoria == 'snacks':
            ventas = ventas.filter(detalles__producto__categoria='snack').distinct()
            egresos = egresos.none()
            asistencias = asistencias.none()
            ocasionales = ocasionales.none()
            titulo += " — Snacks"
        elif categoria == 'suplementos':
            ventas = ventas.filter(detalles__producto__categoria='suplemento').distinct()
            egresos = egresos.none()
            asistencias = asistencias.none()
            ocasionales = ocasionales.none()
            titulo += " — Suplementos"
        elif categoria == 'egresos':
            ventas = ventas.none()
            asistencias = asistencias.none()
            ocasionales = ocasionales.none()
            titulo += " — Egresos"

        total_ingresos = ventas.aggregate(t=Sum('total'))['t'] or 0
        total_egresos = egresos.aggregate(t=Sum('monto'))['t'] or 0
        ganancias = calcular_ganancia_desglosada(ventas)
        ganancia_neta = ganancias['neta']

        # Clientes nuevos
        if tipo == 'diario':
            clientes_nuevos = Cliente.objects.filter(fecha_registro=fecha).count()
        elif tipo == 'semanal':
            clientes_nuevos = Cliente.objects.filter(fecha_registro__range=[inicio, fin]).count()
        else:
            clientes_nuevos = Cliente.objects.filter(fecha_registro__year=año, fecha_registro__month=m).count()

        ctx.update({
            'titulo': titulo,
            'tipo': tipo,
            'categoria': categoria,
            'total_ingresos': total_ingresos,
            'total_egresos': total_egresos,
            'ganancia_neta': ganancia_neta,
            'ganancias_detalle': ganancias,
            'utilidad': ganancia_neta - float(total_egresos),
            'total_asistencias': asistencias.count(),
            'total_ocasionales': ocasionales.count(),
            'ventas': ventas.order_by('-fecha')[:50],
            'egresos': egresos.order_by('-fecha')[:20],
            'clientes_nuevos': clientes_nuevos,
        })
        return ctx


def reporte_pdf(request):
    """Generate PDF report using ReportLab."""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from io import BytesIO
    except ImportError:
        return HttpResponse(
            '<h2 style="font-family:sans-serif;color:red;">ReportLab no está instalado.</h2>'
            '<p style="font-family:sans-serif;">Ejecuta: <code>pip install reportlab</code></p>',
            status=500
        )

    buffer = BytesIO()
    tipo = request.GET.get('tipo', 'diario')
    hoy = date.today()

    if tipo == 'diario':
        fecha_str = request.GET.get('fecha', str(hoy))
        try:
            from datetime import datetime
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except Exception:
            fecha = hoy
        ventas = Venta.objects.filter(fecha__date=fecha)
        egresos = Egreso.objects.filter(fecha=fecha)
        titulo_reporte = f"Reporte Diario: {fecha.strftime('%d/%m/%Y')}"

    elif tipo == 'semanal':
        fecha_inicio_str = request.GET.get('fecha_inicio', str(hoy - timedelta(days=hoy.weekday())))
        fecha_fin_str = request.GET.get('fecha_fin', str(hoy))
        try:
            from datetime import datetime
            inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
            fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
        except Exception:
            inicio = hoy - timedelta(days=hoy.weekday())
            fin = hoy
        ventas = Venta.objects.filter(fecha__date__range=[inicio, fin])
        egresos = Egreso.objects.filter(fecha__range=[inicio, fin])
        titulo_reporte = f"Reporte Semanal: {inicio.strftime('%d/%m/%Y')} — {fin.strftime('%d/%m/%Y')}"

    else:  # mensual
        mes_str = request.GET.get('mes', hoy.strftime('%Y-%m'))
        try:
            año, m = mes_str.split('-')
            año = int(año)
            m = int(m)
        except Exception:
            año = hoy.year
            m = hoy.month
        ventas = Venta.objects.filter(fecha__year=año, fecha__month=m)
        egresos = Egreso.objects.filter(fecha__year=año, fecha__month=m)
        titulo_reporte = f"Reporte Mensual: {m}/{año}"

    categoria = request.GET.get('categoria', 'all')
    if categoria in ['gym', 'gimnasio']:
        ventas = ventas.filter(
            Q(detalles__disciplina__in=['gimnasio', 'gym', '']) |
            Q(detalles__membresia__disciplina='gimnasio')
        ).distinct()
        egresos = egresos.none()
        titulo_reporte += " (Gimnasio)"
    elif categoria == 'crossfit':
        ventas = ventas.filter(
            Q(detalles__disciplina='crossfit') |
            Q(detalles__membresia__disciplina='crossfit')
        ).distinct()
        egresos = egresos.none()
        titulo_reporte += " (Crossfit)"
    elif categoria == 'kickboxing':
        ventas = ventas.filter(
            Q(detalles__disciplina='kickboxing') |
            Q(detalles__membresia__disciplina='kickboxing')
        ).distinct()
        egresos = egresos.none()
        titulo_reporte += " (Kick Boxing)"
    elif categoria == 'snacks':
        ventas = ventas.filter(detalles__producto__categoria='snack').distinct()
        egresos = egresos.none()
        titulo_reporte += " (Snacks)"
    elif categoria == 'suplementos':
        ventas = ventas.filter(detalles__producto__categoria='suplemento').distinct()
        egresos = egresos.none()
        titulo_reporte += " (Suplementos)"
    elif categoria == 'egresos':
        ventas = ventas.none()
        titulo_reporte += " (Egresos)"

    ventas = ventas.prefetch_related('detalles')

    total_ingresos = ventas.aggregate(t=Sum('total'))['t'] or 0
    total_egresos = egresos.aggregate(t=Sum('monto'))['t'] or 0
    ganancias = calcular_ganancia_desglosada(ventas)
    ganancia_neta = ganancias['neta']
    utilidad = ganancia_neta - float(total_egresos)

    # ---- Build PDF ----
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Header background
    p.setFillColor(colors.HexColor('#1a1a2e'))
    p.rect(0, height - 90, width, 90, fill=1, stroke=0)

    # Title
    p.setFillColor(colors.HexColor('#6c63ff'))
    p.setFont("Helvetica-Bold", 20)
    p.drawString(40, height - 40, "GYM ZT SIS")
    p.setFillColor(colors.white)
    p.setFont("Helvetica", 12)
    p.drawString(40, height - 62, titulo_reporte)
    p.setFillColor(colors.HexColor('#aaaacc'))
    p.setFont("Helvetica", 9)
    p.drawString(40, height - 78, f"Generado: {hoy.strftime('%d/%m/%Y')}")

    # Summary boxes
    y_sum = height - 130
    # Ingresos
    p.setFillColor(colors.HexColor('#f0fdf4'))
    p.roundRect(40, y_sum - 50, 140, 60, 8, fill=1, stroke=0)
    p.setFillColor(colors.HexColor('#16a34a'))
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y_sum - 20, f"Bs. {total_ingresos:,.2f}")
    p.setFillColor(colors.HexColor('#555'))
    p.setFont("Helvetica", 10)
    p.drawString(50, y_sum - 40, "Total Ingresos")

    # Egresos
    p.setFillColor(colors.HexColor('#fef2f2'))
    p.roundRect(195, y_sum - 50, 140, 60, 8, fill=1, stroke=0)
    p.setFillColor(colors.HexColor('#dc2626'))
    p.setFont("Helvetica-Bold", 14)
    p.drawString(205, y_sum - 20, f"Bs. {total_egresos:,.2f}")
    p.setFillColor(colors.HexColor('#555'))
    p.setFont("Helvetica", 10)
    p.drawString(205, y_sum - 40, "Total Egresos")

    # Ganancia
    p.setFillColor(colors.HexColor('#f0f0ff'))
    p.roundRect(350, y_sum - 50, 140, 60, 8, fill=1, stroke=0)
    p.setFillColor(colors.HexColor('#6c63ff'))
    p.setFont("Helvetica-Bold", 14)
    p.drawString(360, y_sum - 20, f"Bs. {ganancia_neta:,.2f}")
    p.setFillColor(colors.HexColor('#555'))
    p.setFont("Helvetica", 10)
    p.drawString(360, y_sum - 40, "Ganancia Neta")

    # Utilidad
    p.setFillColor(colors.HexColor('#fffbeb'))
    p.roundRect(505, y_sum - 50, 50, 60, 8, fill=1, stroke=0)
    p.setFillColor(colors.HexColor('#d97706'))
    p.setFont("Helvetica-Bold", 10)
    p.drawString(510, y_sum - 20, f"{utilidad:,.0f}")
    p.setFillColor(colors.HexColor('#555'))
    p.setFont("Helvetica", 8)
    p.drawString(510, y_sum - 40, "Utilidad")

    # --- Ventas Table ---
    if categoria != 'egresos':
        y = y_sum - 80
        p.setFillColor(colors.HexColor('#6c63ff'))
        p.setFont("Helvetica-Bold", 12)
        p.drawString(40, y, "DETALLE DE VENTAS")
        y -= 5
        p.setStrokeColor(colors.HexColor('#6c63ff'))
        p.setLineWidth(1.5)
        p.line(40, y, 555, y)
        y -= 18

        p.setFillColor(colors.HexColor('#eeeeee'))
        p.rect(40, y - 4, 515, 18, fill=1, stroke=0)
        p.setFillColor(colors.black)
        p.setFont("Helvetica-Bold", 9)
        p.drawString(45, y + 2, "#")
        p.drawString(70, y + 2, "Fecha / Hora")
        p.drawString(170, y + 2, "Detalle")
        p.drawString(320, y + 2, "Metodo")
        p.drawString(400, y + 2, "Usuario")
        p.drawString(490, y + 2, "Total (Bs.)")
        y -= 18

        p.setFont("Helvetica", 9)
        row_fill = False
        for v in ventas[:40]:
            if y < 80:
                p.showPage()
                y = height - 60

            if row_fill:
                p.setFillColor(colors.HexColor('#f9f9f9'))
                p.rect(40, y - 4, 515, 16, fill=1, stroke=0)
            row_fill = not row_fill

            p.setFillColor(colors.black)
            p.drawString(45, y + 2, str(v.pk))
            p.drawString(70, y + 2, v.fecha.strftime('%d/%m/%Y %H:%M'))
            
            detalle_desc = str(v.detalles.first().descripcion)[:22] if v.detalles.exists() else 'Venta'
            p.drawString(170, y + 2, detalle_desc)
            
            p.drawString(320, y + 2, v.get_metodo_pago_display()[:12])
            usuario_nombre = str(v.usuario.username)[:12] if v.usuario else "-"
            p.drawString(400, y + 2, usuario_nombre)
            p.setFillColor(colors.HexColor('#16a34a'))
            p.drawString(490, y + 2, f"{v.total:,.2f}")
            p.setFillColor(colors.black)
            y -= 16
    else:
        y = y_sum - 80

    # --- Egresos Table ---
    if categoria in ['all', 'egresos']:
        y -= 20
        if y < 150:
            p.showPage()
            y = height - 60

        p.setFillColor(colors.HexColor('#dc2626'))
        p.setFont("Helvetica-Bold", 12)
        p.drawString(40, y, "DETALLE DE EGRESOS")
        y -= 5
        p.setStrokeColor(colors.HexColor('#dc2626'))
        p.setLineWidth(1.5)
        p.line(40, y, 555, y)
        y -= 18

        p.setFillColor(colors.HexColor('#eeeeee'))
        p.rect(40, y - 4, 515, 18, fill=1, stroke=0)
        p.setFillColor(colors.black)
        p.setFont("Helvetica-Bold", 9)
        p.drawString(45, y + 2, "Fecha")
        p.drawString(150, y + 2, "Usuario")
        p.drawString(280, y + 2, "Descripcion")
        p.drawString(490, y + 2, "Monto (Bs.)")
        y -= 18

        p.setFont("Helvetica", 9)
        row_fill = False
        for e in egresos[:20]:
            if y < 80:
                p.showPage()
                y = height - 60
            if row_fill:
                p.setFillColor(colors.HexColor('#fff5f5'))
                p.rect(40, y - 4, 515, 16, fill=1, stroke=0)
            row_fill = not row_fill

            p.setFillColor(colors.black)
            p.drawString(45, y + 2, e.fecha.strftime('%d/%m/%Y'))
            usuario_nombre = str(e.usuario.username)[:15] if e.usuario else "-"
            p.drawString(150, y + 2, usuario_nombre)
            p.drawString(280, y + 2, str(e.descripcion)[:30])
            p.setFillColor(colors.HexColor('#dc2626'))
            p.drawString(490, y + 2, f"{e.monto:,.2f}")
            p.setFillColor(colors.black)
            y -= 16

    # Footer
    p.setFont("Helvetica", 8)
    p.setFillColor(colors.HexColor('#999999'))
    p.drawString(40, 30, f"GYM ZT SIS — Reporte generado automaticamente el {hoy.strftime('%d/%m/%Y')}")

    p.showPage()
    p.save()
    buffer.seek(0)
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_{tipo}_{hoy}.pdf"'
    return response
