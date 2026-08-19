"""
Genera el Manual de Usuario de GYM ZT SIS en PDF usando ReportLab.
Uso: py docs/generar_manual.py
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate
from reportlab.pdfgen import canvas
import os

OUTPUT = os.path.join(os.path.dirname(__file__), "Manual_GYM_ZT_SIS.pdf")

# ── Colores ──────────────────────────────────────────────────────────────────
AZUL       = colors.HexColor("#1a1f36")
ACENTO     = colors.HexColor("#6c63ff")
ACENTO2    = colors.HexColor("#4f46e5")
GRIS_CLARO = colors.HexColor("#f0f4ff")
GRIS_MED   = colors.HexColor("#c5cfe8")
VERDE      = colors.HexColor("#198754")
ROJO       = colors.HexColor("#dc3545")
BLANCO     = colors.white
NEGRO      = colors.HexColor("#1a1a2e")

W, H = A4


# ── Header / Footer ──────────────────────────────────────────────────────────
def header_footer(canv, doc):
    canv.saveState()
    # Header
    canv.setFillColor(AZUL)
    canv.rect(0, H - 1.2*cm, W, 1.2*cm, fill=1, stroke=0)
    canv.setFillColor(BLANCO)
    canv.setFont("Helvetica-Bold", 9)
    canv.drawString(1.5*cm, H - 0.85*cm, "GYM ZT SIS — Manual de Usuario")
    canv.setFont("Helvetica", 8)
    canv.drawRightString(W - 1.5*cm, H - 0.85*cm, "MISACORP")
    # Footer
    canv.setFillColor(AZUL)
    canv.rect(0, 0, W, 0.9*cm, fill=1, stroke=0)
    canv.setFillColor(GRIS_MED)
    canv.setFont("Helvetica", 7.5)
    canv.drawString(1.5*cm, 0.3*cm, "© MISACORP — Todos los derechos reservados")
    canv.drawRightString(W - 1.5*cm, 0.3*cm, f"Página {doc.page}")
    canv.restoreState()


# ── Estilos ───────────────────────────────────────────────────────────────────
def estilos():
    s = getSampleStyleSheet()

    titulo_portada = ParagraphStyle("titulo_portada",
        fontSize=34, textColor=BLANCO, alignment=TA_CENTER,
        fontName="Helvetica-Bold", spaceAfter=6)

    subtitulo_portada = ParagraphStyle("subtitulo_portada",
        fontSize=13, textColor=GRIS_MED, alignment=TA_CENTER,
        fontName="Helvetica", spaceAfter=4)

    titulo_seccion = ParagraphStyle("titulo_seccion",
        fontSize=16, textColor=ACENTO, fontName="Helvetica-Bold",
        spaceBefore=18, spaceAfter=6, leftIndent=0)

    titulo_subseccion = ParagraphStyle("titulo_subseccion",
        fontSize=12, textColor=AZUL, fontName="Helvetica-Bold",
        spaceBefore=10, spaceAfter=4)

    cuerpo = ParagraphStyle("cuerpo",
        fontSize=10, textColor=NEGRO, fontName="Helvetica",
        leading=16, spaceAfter=6, alignment=TA_JUSTIFY)

    bullet = ParagraphStyle("bullet",
        fontSize=10, textColor=NEGRO, fontName="Helvetica",
        leading=15, spaceAfter=3, leftIndent=16, bulletIndent=6)

    nota = ParagraphStyle("nota",
        fontSize=9, textColor=colors.HexColor("#5c6080"),
        fontName="Helvetica-Oblique", leading=13,
        leftIndent=12, spaceAfter=6)

    paso = ParagraphStyle("paso",
        fontSize=10, textColor=NEGRO, fontName="Helvetica-Bold",
        leading=15, spaceAfter=2, leftIndent=0)

    return {
        "titulo_portada": titulo_portada,
        "subtitulo_portada": subtitulo_portada,
        "titulo_seccion": titulo_seccion,
        "titulo_subseccion": titulo_subseccion,
        "cuerpo": cuerpo,
        "bullet": bullet,
        "nota": nota,
        "paso": paso,
    }


def titulo_con_linea(texto, st):
    return [
        Paragraph(texto, st["titulo_seccion"]),
        HRFlowable(width="100%", thickness=1.5, color=ACENTO, spaceAfter=8),
    ]


def paso_item(num, texto, st):
    return Paragraph(f"<b>Paso {num}.</b> {texto}", st["cuerpo"])


def bala(texto, st):
    return Paragraph(f"• {texto}", st["bullet"])


def tabla_info(datos, col_widths=None):
    if col_widths is None:
        col_widths = [5.5*cm, 11*cm]
    t = Table(datos, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), GRIS_CLARO),
        ("BACKGROUND", (1, 0), (1, -1), BLANCO),
        ("TEXTCOLOR", (0, 0), (0, -1), AZUL),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("GRID", (0, 0), (-1, -1), 0.4, GRIS_MED),
        ("ROWBACKGROUND", (0, 0), (-1, -1), [GRIS_CLARO, BLANCO]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


# ── PORTADA ───────────────────────────────────────────────────────────────────
def portada(story, st):
    story.append(Spacer(1, 3.5*cm))

    # Bloque de color con título
    data = [[Paragraph("⚡ GYM ZT SIS", st["titulo_portada"])]]
    t = Table(data, colWidths=[16*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), AZUL),
        ("ROUNDEDCORNERS", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 28),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 28),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.6*cm))
    story.append(Paragraph("Sistema de Gestión de Gimnasio", st["subtitulo_portada"]))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph("Manual de Usuario", ParagraphStyle("mp",
        fontSize=18, textColor=ACENTO, alignment=TA_CENTER,
        fontName="Helvetica-Bold", spaceAfter=4)))
    story.append(Spacer(1, 2.5*cm))

    info = [
        ["Versión", "1.0"],
        ["Desarrollado por", "MISACORP"],
        ["Destinado a", "Dueño / Administrador del Gimnasio"],
    ]
    story.append(tabla_info(info, [4*cm, 10*cm]))
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph(
        "Este manual le guiará paso a paso en el uso del sistema GYM ZT SIS. "
        "No se necesita conocimiento técnico previo.",
        ParagraphStyle("intro_p", fontSize=10, textColor=colors.HexColor("#5c6080"),
                       alignment=TA_CENTER, fontName="Helvetica-Oblique", leading=16)))
    story.append(PageBreak())


# ── ÍNDICE ────────────────────────────────────────────────────────────────────
def indice(story, st):
    story += titulo_con_linea("Contenido", st)

    secciones = [
        ("1.", "Primeros pasos — Iniciar el sistema"),
        ("2.", "Inicio de sesión"),
        ("3.", "Recuperar contraseña olvidada"),
        ("4.", "Panel principal (Dashboard)"),
        ("5.", "Clientes"),
        ("6.", "Membresías"),
        ("7.", "Asistencia"),
        ("8.", "Punto de Venta"),
        ("9.", "Caja"),
        ("10.", "Egresos / Gastos"),
        ("11.", "Inventario (Solo administrador)"),
        ("12.", "Contabilidad (Solo administrador)"),
        ("13.", "Reportes (Solo administrador)"),
        ("14.", "Gestión de Usuarios (Solo administrador)"),
        ("15.", "Preguntas frecuentes"),
    ]

    data = [[Paragraph(f"<b>{n}</b>", ParagraphStyle("idx_n",
                fontSize=10, textColor=ACENTO, fontName="Helvetica-Bold")),
             Paragraph(t, ParagraphStyle("idx_t",
                fontSize=10, textColor=NEGRO, fontName="Helvetica"))]
            for n, t in secciones]

    t = Table(data, colWidths=[1.4*cm, 14.6*cm])
    t.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, GRIS_MED),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(t)
    story.append(PageBreak())


# ── SECCIONES ─────────────────────────────────────────────────────────────────
def seccion_inicio(story, st):
    story += titulo_con_linea("1. Primeros pasos — Iniciar el sistema", st)
    story.append(Paragraph(
        "GYM ZT SIS es una aplicación de escritorio. Para usarla simplemente "
        "haga doble clic en el ícono <b>GYM ZT SIS</b> de su escritorio o "
        "búsquela en el menú Inicio de Windows.", st["cuerpo"]))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("¿Qué pasa al abrir la aplicación?", st["titulo_subseccion"]))
    story.append(bala("Aparece una pantalla de carga mientras el sistema se prepara.", st))
    story.append(bala("En unos segundos se abre la pantalla de inicio de sesión.", st))
    story.append(bala("Si es la primera vez, el sistema crea automáticamente la base de datos.", st))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        "⚠ <b>Importante:</b> El sistema requiere que el servicio de base de datos "
        "(PostgreSQL) esté funcionando en la computadora. Este se instala junto "
        "con la aplicación y normalmente inicia solo con Windows.",
        st["nota"]))


def seccion_login(story, st):
    story += titulo_con_linea("2. Inicio de sesión", st)
    story.append(Paragraph(
        "Al abrir la aplicación verá la pantalla de inicio de sesión. "
        "Ingrese sus credenciales para entrar al sistema.", st["cuerpo"]))

    story.append(Paragraph("Campos requeridos:", st["titulo_subseccion"]))
    data = [
        ["Usuario", "Nombre de usuario asignado (ej: misacorp)"],
        ["Contraseña", "Su contraseña personal"],
    ]
    story.append(tabla_info(data))
    story.append(Spacer(1, 0.4*cm))
    story.append(paso_item(1, "Escriba su nombre de usuario.", st))
    story.append(paso_item(2, "Escriba su contraseña (puede usar el ojo 👁 para verla).", st))
    story.append(paso_item(3, "Haga clic en <b>Iniciar Sesión</b>.", st))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        "Si el usuario o la contraseña son incorrectos, el sistema le avisará "
        "con un mensaje en rojo. Verifique que no tenga el bloqueo de mayúsculas activado.",
        st["nota"]))


def seccion_recuperar(story, st):
    story += titulo_con_linea("3. Recuperar contraseña olvidada", st)
    story.append(Paragraph(
        "Si olvidó su contraseña puede recuperarla respondiendo su pregunta "
        "de seguridad, sin necesidad de llamar a soporte técnico.", st["cuerpo"]))
    story.append(Spacer(1, 0.2*cm))
    story.append(paso_item(1, "En la pantalla de login haga clic en <b>¿Olvidaste tu contraseña?</b>", st))
    story.append(paso_item(2, "Escriba su nombre de usuario y haga clic en <b>Continuar</b>.", st))
    story.append(paso_item(3, "Responda la pregunta de seguridad que configuró.", st))
    story.append(paso_item(4, "Escriba su nueva contraseña y confírmela.", st))
    story.append(paso_item(5, "Haga clic en <b>Cambiar contraseña</b>. Ya puede ingresar con la nueva clave.", st))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        "💡 <b>Consejo:</b> Configure su pregunta de seguridad desde el panel de "
        "administración de usuarios antes de que surja la necesidad.",
        st["nota"]))


def seccion_dashboard(story, st):
    story += titulo_con_linea("4. Panel principal (Dashboard)", st)
    story.append(Paragraph(
        "Al ingresar al sistema verá el panel principal con un resumen de "
        "todo lo que ocurre en su gimnasio en tiempo real.", st["cuerpo"]))

    story.append(Paragraph("¿Qué muestra el Dashboard?", st["titulo_subseccion"]))
    data = [
        ["Asistencias hoy", "Cuántas personas ingresaron al gimnasio hoy"],
        ["Ventas del día", "Total de ventas realizadas en el día actual"],
        ["Ingresos del día", "Dinero total que entró hoy (membresías + ventas)"],
        ["Miembros activos", "Cantidad de clientes con membresía vigente"],
        ["Membresías por vencer", "Clientes cuya membresía vence en los próximos días"],
        ["Alertas", "Notificaciones de stock bajo, membresías vencidas, etc."],
    ]
    story.append(tabla_info(data))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        "Use el menú lateral izquierdo para navegar entre las diferentes secciones del sistema.",
        st["cuerpo"]))


def seccion_clientes(story, st):
    story += titulo_con_linea("5. Clientes", st)
    story.append(Paragraph(
        "En esta sección registra y administra toda la información de los "
        "clientes del gimnasio.", st["cuerpo"]))

    story.append(Paragraph("Registrar un nuevo cliente", st["titulo_subseccion"]))
    story.append(paso_item(1, "Vaya a <b>Clientes</b> en el menú lateral.", st))
    story.append(paso_item(2, "Haga clic en el botón <b>Nuevo Cliente</b>.", st))
    story.append(paso_item(3, "Complete los datos del formulario:", st))

    data = [
        ["Nombre *", "Nombre completo del cliente (obligatorio)"],
        ["Teléfono", "Número de contacto"],
        ["Ubicación", "Barrio o zona donde vive"],
        ["Peso inicial", "Peso en kilogramos al momento de registro"],
        ["Foto", "Fotografía del cliente (opcional)"],
        ["Notas", "Observaciones adicionales"],
    ]
    story.append(tabla_info(data))
    story.append(paso_item(4, "Haga clic en <b>Guardar</b>.", st))

    story.append(Paragraph("Buscar y filtrar clientes", st["titulo_subseccion"]))
    story.append(bala("Use la barra de búsqueda para encontrar un cliente por nombre.", st))
    story.append(bala("Puede filtrar entre clientes activos e inactivos.", st))

    story.append(Paragraph("Editar o desactivar un cliente", st["titulo_subseccion"]))
    story.append(bala("Haga clic en el botón <b>Editar</b> junto al cliente.", st))
    story.append(bala("Para desactivarlo, desmarque la opción <b>Activo</b> y guarde.", st))
    story.append(Paragraph(
        "Un cliente inactivo no aparece en el punto de venta ni puede registrar asistencia.",
        st["nota"]))


def seccion_membresias(story, st):
    story += titulo_con_linea("6. Membresías", st)
    story.append(Paragraph(
        "Las membresías son los planes que ofrecen a sus clientes (mensual, "
        "trimestral, etc.). Primero se crean los planes y luego se asignan a cada cliente.",
        st["cuerpo"]))

    story.append(Paragraph("Crear un plan de membresía", st["titulo_subseccion"]))
    story.append(paso_item(1, "Vaya a <b>Membresías</b> en el menú lateral.", st))
    story.append(paso_item(2, "Haga clic en <b>Nuevo Plan</b>.", st))
    data = [
        ["Nombre *", "Ej: Mensual, Trimestral, Anual"],
        ["Precio *", "Costo en bolivianos (Bs.)"],
        ["Duración *", "Cantidad de días que dura el plan"],
        ["Descripción", "Detalles adicionales del plan (opcional)"],
    ]
    story.append(tabla_info(data))
    story.append(paso_item(3, "Haga clic en <b>Guardar</b>.", st))

    story.append(Paragraph("Asignar membresía a un cliente", st["titulo_subseccion"]))
    story.append(paso_item(1, "Busque y abra el perfil del cliente.", st))
    story.append(paso_item(2, "Haga clic en <b>Asignar Membresía</b>.", st))
    story.append(paso_item(3, "Seleccione el plan, la fecha de inicio y el método de pago.", st))
    story.append(paso_item(4, "Haga clic en <b>Guardar</b>. La fecha de vencimiento se calcula sola.", st))
    story.append(Paragraph(
        "💡 Al asignar una membresía se genera automáticamente una venta en el sistema.",
        st["nota"]))


def seccion_asistencia(story, st):
    story += titulo_con_linea("7. Asistencia", st)
    story.append(Paragraph(
        "Registre el ingreso diario de clientes al gimnasio. El sistema "
        "lleva un historial completo de asistencias.", st["cuerpo"]))

    story.append(Paragraph("Registrar asistencia de un miembro", st["titulo_subseccion"]))
    story.append(paso_item(1, "Vaya a <b>Asistencia</b> en el menú lateral.", st))
    story.append(paso_item(2, "Escriba el nombre del cliente en el buscador.", st))
    story.append(paso_item(3, "Seleccione el cliente de la lista.", st))
    story.append(paso_item(4, "Haga clic en <b>Registrar</b>.", st))
    story.append(Paragraph(
        "Si el cliente ya registró asistencia hoy, el sistema le avisará y no duplicará el registro.",
        st["nota"]))

    story.append(Paragraph("Registrar entrada ocasional", st["titulo_subseccion"]))
    story.append(Paragraph(
        "Para personas que pagan por día sin ser miembros:", st["cuerpo"]))
    story.append(paso_item(1, "En el panel de asistencia, complete el formulario <b>Entrada Ocasional</b>.", st))
    story.append(paso_item(2, "Ingrese el nombre (opcional), el monto pagado y el método de pago.", st))
    story.append(paso_item(3, "Haga clic en <b>Registrar Ocasional</b>.", st))

    story.append(Paragraph("Lista de asistencias de hoy", st["titulo_subseccion"]))
    story.append(bala("Los miembros aparecen con un badge azul.", st))
    story.append(bala("Los ocasionales aparecen en verde con el monto pagado.", st))
    story.append(bala("El encabezado muestra el total: <b>X miembros + Y ocasionales</b>.", st))


def seccion_pos(story, st):
    story += titulo_con_linea("8. Punto de Venta", st)
    story.append(Paragraph(
        "Use esta sección para registrar ventas de productos (snacks, "
        "suplementos) a sus clientes.", st["cuerpo"]))

    story.append(Paragraph("Realizar una venta", st["titulo_subseccion"]))
    story.append(paso_item(1, "Vaya a <b>Punto de Venta</b> en el menú lateral.", st))
    story.append(paso_item(2, "Busque y seleccione los productos haciendo clic sobre ellos.", st))
    story.append(paso_item(3, "Ajuste las cantidades con los botones + y − en el carrito.", st))
    story.append(paso_item(4, "Si la venta es para un cliente registrado, búsquelo en el campo <b>Buscar cliente</b>.", st))
    story.append(paso_item(5, "Seleccione el <b>método de pago</b> (Efectivo, Transferencia o QR).", st))
    story.append(paso_item(6, "Haga clic en <b>COBRAR</b>. Aparecerá una notificación verde confirmando la venta.", st))

    story.append(Paragraph("Filtrar productos", st["titulo_subseccion"]))
    story.append(bala("Use los botones <b>Snacks</b> y <b>Suplementos</b> para filtrar por categoría.", st))
    story.append(bala("Use la barra de búsqueda para encontrar un producto por nombre.", st))

    story.append(Paragraph(
        "⚠ <b>Importante:</b> Debe haber una caja abierta para poder realizar ventas. "
        "Si el botón COBRAR está desactivado, abra la caja primero.",
        st["nota"]))


def seccion_caja(story, st):
    story += titulo_con_linea("9. Caja", st)
    story.append(Paragraph(
        "La caja registra todos los movimientos de dinero del día: "
        "ingresos por ventas y membresías, y egresos por gastos.",
        st["cuerpo"]))

    story.append(Paragraph("Abrir la caja", st["titulo_subseccion"]))
    story.append(paso_item(1, "Vaya a <b>Caja</b> en el menú lateral.", st))
    story.append(paso_item(2, "Haga clic en <b>Abrir Caja</b>.", st))
    story.append(paso_item(3, "Ingrese el monto inicial (efectivo con el que comienza el día).", st))
    story.append(paso_item(4, "Haga clic en <b>Confirmar</b>.", st))

    story.append(Paragraph("Cerrar la caja", st["titulo_subseccion"]))
    story.append(paso_item(1, "Al finalizar el día, haga clic en <b>Cerrar Caja</b>.", st))
    story.append(paso_item(2, "El sistema mostrará el resumen: ingresos, egresos y saldo final.", st))
    story.append(paso_item(3, "Confirme el cierre.", st))
    story.append(Paragraph(
        "Una vez cerrada la caja no se pueden registrar más ventas ni egresos del día. "
        "Abra una nueva caja al día siguiente.",
        st["nota"]))


def seccion_egresos(story, st):
    story += titulo_con_linea("10. Egresos / Gastos", st)
    story.append(Paragraph(
        "Registre todos los gastos del gimnasio para llevar un control "
        "completo de sus finanzas.", st["cuerpo"]))

    story.append(Paragraph("Registrar un egreso", st["titulo_subseccion"]))
    story.append(paso_item(1, "Vaya a <b>Egresos</b> en el menú lateral.", st))
    story.append(paso_item(2, "Haga clic en <b>Nuevo Egreso</b>.", st))

    data = [
        ["Tipo *", "Categoría del gasto"],
        ["Monto *", "Importe en bolivianos (Bs.)"],
        ["Fecha *", "Fecha del gasto (viene con el día actual)"],
        ["Descripción", "Detalle adicional del gasto"],
    ]
    story.append(tabla_info(data))
    story.append(paso_item(3, "Haga clic en <b>Registrar Egreso</b>.", st))

    story.append(Paragraph("Tipos de egreso disponibles:", st["titulo_subseccion"]))
    tipos = ["Compra de Producto", "Sueldos", "Alquiler",
             "Servicios (Luz/Agua/Internet)", "Mantenimiento", "Otros"]
    for t in tipos:
        story.append(bala(t, st))


def seccion_inventario(story, st):
    story += titulo_con_linea("11. Inventario (Solo administrador)", st)
    story.append(Paragraph(
        "Controle el stock de snacks y suplementos que vende en su gimnasio. "
        "Esta sección solo es accesible para administradores.",
        st["cuerpo"]))

    story.append(Paragraph("Agregar un nuevo producto", st["titulo_subseccion"]))
    story.append(paso_item(1, "Vaya a <b>Inventario Snacks</b> o <b>Inventario Suplementos</b>.", st))
    story.append(paso_item(2, "Haga clic en <b>Nuevo Producto</b>.", st))
    data = [
        ["Nombre *", "Nombre del producto"],
        ["Categoría *", "Snack o Suplemento"],
        ["Precio de compra *", "Cuánto le costó a usted (Bs.)"],
        ["Precio de venta *", "Cuánto lo vende al cliente (Bs.)"],
        ["Stock inicial *", "Cantidad disponible"],
        ["Imagen", "Foto del producto (opcional)"],
    ]
    story.append(tabla_info(data))
    story.append(paso_item(3, "Haga clic en <b>Guardar</b>.", st))

    story.append(Paragraph("Agregar stock a un producto existente", st["titulo_subseccion"]))
    story.append(paso_item(1, "En la lista de inventario, haga clic en <b>+ Stock</b> junto al producto.", st))
    story.append(paso_item(2, "Ingrese la cantidad que desea agregar.", st))
    story.append(paso_item(3, "Haga clic en <b>Agregar</b>. El stock se suma al existente.", st))
    story.append(Paragraph(
        "💡 Cuando el stock de un producto baje de 5 unidades, el sistema generará "
        "una alerta automática en el panel principal.",
        st["nota"]))


def seccion_contabilidad(story, st):
    story += titulo_con_linea("12. Contabilidad (Solo administrador)", st)
    story.append(Paragraph(
        "Vea un resumen financiero completo de su gimnasio: ingresos, "
        "egresos, ganancias por período.", st["cuerpo"]))

    story.append(Paragraph("¿Qué muestra?", st["titulo_subseccion"]))
    data = [
        ["Ingresos totales", "Todo el dinero que entró (ventas + membresías)"],
        ["Egresos totales", "Todos los gastos registrados"],
        ["Ganancia neta", "Ingresos menos egresos"],
        ["Historial de egresos", "Lista detallada de todos los gastos"],
    ]
    story.append(tabla_info(data))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        "Puede filtrar la información por rango de fechas para ver períodos específicos.",
        st["cuerpo"]))


def seccion_reportes(story, st):
    story += titulo_con_linea("13. Reportes (Solo administrador)", st)
    story.append(Paragraph(
        "Genere reportes visuales sobre el rendimiento de su gimnasio.",
        st["cuerpo"]))

    story.append(Paragraph("Reportes disponibles:", st["titulo_subseccion"]))
    data = [
        ["Ventas por período", "Gráfico de ventas diarias, semanales o mensuales"],
        ["Productos más vendidos", "Ranking de productos con mayor rotación"],
        ["Asistencia", "Historial y tendencias de concurrencia al gimnasio"],
        ["Membresías", "Estado general de membresías activas y vencidas"],
    ]
    story.append(tabla_info(data))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        "Use los reportes para tomar decisiones sobre qué productos comprar, "
        "qué horarios tienen más demanda y cómo va el negocio en general.",
        st["cuerpo"]))


def seccion_usuarios(story, st):
    story += titulo_con_linea("14. Gestión de Usuarios (Solo administrador)", st)
    story.append(Paragraph(
        "Cree y administre las cuentas de acceso al sistema para usted y "
        "sus empleados.", st["cuerpo"]))

    story.append(Paragraph("Roles disponibles:", st["titulo_subseccion"]))
    data = [
        ["Administrador", "Acceso completo a todas las funciones del sistema"],
        ["Empleado", "Acceso a: Asistencia, Ventas, Caja, Clientes, Membresías y Egresos"],
    ]
    story.append(tabla_info(data))

    story.append(Paragraph("Crear un nuevo usuario", st["titulo_subseccion"]))
    story.append(paso_item(1, "Vaya a <b>Usuarios</b> en el menú lateral (sección Administración).", st))
    story.append(paso_item(2, "Haga clic en <b>Nuevo Usuario</b>.", st))
    story.append(paso_item(3, "Complete nombre, usuario, contraseña y rol.", st))
    story.append(paso_item(4, "Configure una <b>pregunta de seguridad</b> y su respuesta para que el usuario pueda recuperar su contraseña.", st))
    story.append(paso_item(5, "Haga clic en <b>Guardar</b>.", st))

    story.append(Paragraph("Cambiar la contraseña de un usuario", st["titulo_subseccion"]))
    story.append(paso_item(1, "En la lista de usuarios, haga clic en el ícono de candado 🔒.", st))
    story.append(paso_item(2, "Ingrese la nueva contraseña y confirme con su propia contraseña de administrador.", st))


def seccion_faq(story, st):
    story += titulo_con_linea("15. Preguntas frecuentes", st)

    faqs = [
        ("¿Qué hago si la app no abre?",
         "Verifique que el servicio PostgreSQL esté en ejecución. Puede hacerlo desde "
         "Servicios de Windows (busque 'postgresql'). Si el servicio está detenido, inícielo."),
        ("¿Se pierden los datos si desinstalo la app?",
         "No. Los datos están en la base de datos PostgreSQL que permanece en su computadora "
         "aunque desinstale la aplicación."),
        ("¿Puedo usar el sistema en varias computadoras?",
         "En esta versión el sistema está diseñado para una sola computadora. "
         "Todos los datos se almacenan localmente."),
        ("¿Cómo hago respaldo de mis datos?",
         "Desde pgAdmin puede exportar (hacer backup) de la base de datos 'gym_zt_sis_desktop'. "
         "Se recomienda hacerlo periódicamente."),
        ("Un empleado no puede ver ciertas secciones, ¿es normal?",
         "Sí. Los empleados solo ven: Asistencia, Ventas, Caja, Clientes, Membresías y Egresos. "
         "Inventario, Contabilidad y Reportes son exclusivos del administrador."),
        ("¿Cómo actualizo el sistema?",
         "El administrador del sistema (MISACORP) le entregará un nuevo instalador. "
         "Solo ejecútelo encima de la versión anterior. Sus datos no se verán afectados."),
    ]

    for pregunta, respuesta in faqs:
        bloque = [
            Paragraph(f"❓ {pregunta}", ParagraphStyle("faq_p",
                fontSize=10.5, textColor=AZUL, fontName="Helvetica-Bold",
                spaceBefore=10, spaceAfter=3)),
            Paragraph(respuesta, st["cuerpo"]),
            HRFlowable(width="100%", thickness=0.4, color=GRIS_MED, spaceAfter=4),
        ]
        story += bloque

    story.append(Spacer(1, 1*cm))

    # Cierre
    data = [[Paragraph(
        "Para soporte técnico o consultas comuníquese con <b>MISACORP</b>.",
        ParagraphStyle("cierre", fontSize=10, textColor=BLANCO,
                       fontName="Helvetica", alignment=TA_CENTER, leading=16))]]
    t = Table(data, colWidths=[16*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), AZUL),
        ("TOPPADDING", (0, 0), (-1, -1), 16),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
    ]))
    story.append(t)


# ── MAIN ─────────────────────────────────────────────────────────────────────
def generar():
    doc = SimpleDocTemplate(
        OUTPUT,
        pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=1.8*cm, bottomMargin=1.6*cm,
        title="Manual de Usuario — GYM ZT SIS",
        author="MISACORP",
    )

    st = estilos()
    story = []

    portada(story, st)
    indice(story, st)
    seccion_inicio(story, st);    story.append(Spacer(1, 0.4*cm))
    seccion_login(story, st);     story.append(Spacer(1, 0.4*cm))
    seccion_recuperar(story, st); story.append(PageBreak())
    seccion_dashboard(story, st); story.append(Spacer(1, 0.4*cm))
    seccion_clientes(story, st);  story.append(PageBreak())
    seccion_membresias(story, st);story.append(Spacer(1, 0.4*cm))
    seccion_asistencia(story, st);story.append(PageBreak())
    seccion_pos(story, st);       story.append(Spacer(1, 0.4*cm))
    seccion_caja(story, st);      story.append(PageBreak())
    seccion_egresos(story, st);   story.append(Spacer(1, 0.4*cm))
    seccion_inventario(story, st);story.append(PageBreak())
    seccion_contabilidad(story, st); story.append(Spacer(1, 0.4*cm))
    seccion_reportes(story, st);  story.append(Spacer(1, 0.4*cm))
    seccion_usuarios(story, st);  story.append(PageBreak())
    seccion_faq(story, st)

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"Manual generado: {OUTPUT}")


if __name__ == "__main__":
    generar()
