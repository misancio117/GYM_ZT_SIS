# Manual de uso — GYM ZT SIS

Guía para el **usuario final** del sistema: cómo moverse por la interfaz, qué significa cada pantalla, **de dónde salen los números** y qué acciones puede realizar en cada módulo.

> Moneda y formato: el sistema muestra montos en **bolivianos (Bs.)** salvo configuración distinta de su organización.

---

## Tabla de contenidos

1. [Acceso y roles](#1-acceso-y-roles)
2. [Cómo está organizada la pantalla](#2-cómo-está-organizada-la-pantalla)
3. [Dashboard](#3-dashboard)
4. [Asistencia](#4-asistencia)
5. [Punto de venta (POS)](#5-punto-de-venta-pos)
6. [Caja](#6-caja)
7. [Clientes](#7-clientes)
8. [Membresías](#8-membresías)
9. [Inventario](#9-inventario)
10. [Contabilidad](#10-contabilidad)
11. [Egresos](#11-egresos)
12. [Reportes](#12-reportes)
13. [Alertas](#13-alertas)
14. [Administración (solo administradores)](#14-administración-solo-administradores)
15. [Resumen: de dónde vienen los principales indicadores](#15-resumen-de-dónde-vienen-los-principales-indicadores)

---

## 1. Acceso y roles

### Inicio de sesión

1. Abra la aplicación **GYM ZT SIS** (escritorio) o la URL que le indique su soporte (normalmente `http://127.0.0.1:8000/login/`).
2. Introduzca **usuario** y **contraseña** que le haya dado el administrador.
3. Tras entrar, el sistema lo lleva al **Dashboard**.

### Roles

| Rol | Descripción |
|-----|-------------|
| **Administrador** | Acceso a todo el menú, incluidos **Usuarios** y **Auditoría**. |
| **Empleado** | Acceso a operaciones diarias (asistencia, ventas, caja, clientes, membresías, inventario, contabilidad, reportes, alertas). **No** ve el apartado de gestión de usuarios del sistema ni el listado de auditoría en el menú lateral. |

---

## 2. Cómo está organizada la pantalla

### Menú lateral (barra izquierda)

Secciones y enlaces (de arriba abajo):

| Sección | Enlaces |
|---------|---------|
| *(inicio)* | **Dashboard** |
| **OPERACIONES** | Asistencia, Punto de Venta, Caja |
| **GESTIÓN** | Clientes, Membresías, Inventario |
| **FINANZAS** | Contabilidad, Egresos, Reportes |
| **ADMINISTRACIÓN** *(solo admin)* | Usuarios, Auditoría |

Puede **contraer o expandir** el menú con el botón de tres rayas (☰) en la barra superior.

### Barra superior

- **Título** de la página actual.
- **Accesos rápidos:** registrar entrada (asistencia) y nueva venta (POS).
- **Campana de alertas:** muestra un contador si hay alertas activas; al desplegar ve un resumen y un enlace a **Ver todas**.
- **Menú de usuario:** muestra su nombre y rol; **Cerrar sesión** cierra la sesión de forma segura.

### Mensajes en verde / amarillo / rojo

Tras guardar formularios, el sistema puede mostrar mensajes de éxito o error en la parte superior del contenido; suelen cerrarse solos pasados unos segundos.

---

## 3. Dashboard

Es la **página de inicio** después del login. Resume el **día de hoy** y el **mes en curso** en parte de los bloques.

### Tarjetas de indicadores (KPI) — fila 1

| Indicador | Qué es | Origen de los datos |
|-----------|--------|---------------------|
| **Ingresos hoy** | Suma de **totales** de todas las **ventas** registradas **hoy** (cualquier tipo: producto, membresía, ocasional, mixto). | Tabla de **ventas** (`Venta`), campo `total`, filtrado por la **fecha** de la venta = hoy. |
| **Egresos hoy** | Suma de **montos** de los **egresos** registrados con **fecha** = hoy. | Módulo **Contabilidad** → registros de **Egreso** (`monto`, `fecha`). |
| **Ganancia neta** *(hoy)* | **Margen de productos** (ventas tipo producto o mixto: suma del campo `ganancia`) **más** **ingresos directos del gimnasio** (ventas tipo membresía u ocasional: se usa el `total` de esas ventas). | Calculado solo con las ventas de **hoy**. No resta aquí los egresos de contabilidad (eso lo verá en Contabilidad / Reportes como “utilidad”). |

### Tarjetas — fila 2

| Indicador | Origen |
|-----------|--------|
| **Asistencias hoy** | Cantidad de registros de **asistencia** de clientes con membresía (o flujo normal de entrada) con **fecha** = hoy. |
| **Ocasionales** | Cantidad de **entradas ocasionales** registradas **hoy** (clientes sin plan, típicamente vinculadas a una venta de tipo ocasional). |
| **Membresías activas** | Cantidad de **asignaciones** de plan a cliente con estado **activa** y vigencia según fechas del sistema. |

Además se muestra el total de **clientes activos** en el sistema (ficha cliente con estado activo).

### Gráfico “Ingresos últimos 7 días”

- Para cada uno de los últimos 7 días calendario suma el **total** de ventas de ese día.
- **Fuente:** mismas **ventas** que “Ingresos hoy”, pero día a día.

### Gráfico “Métodos de pago hoy (Bs.)”

- Reparte los **ingresos de hoy** según cómo se cobró cada venta: **Efectivo**, **Transferencia**, **QR**.
- Usa el **monto en bolivianos** de cada venta, no solo el número de tickets.

### Tabla “Ventas recientes”

- Lista las **últimas ventas del día** con número de ticket, descripción del primer ítem, total, método y hora.
- Enlace **Ver todo** lleva al listado completo de ventas.

### Tabla “Top productos del mes”

- Los **5 productos más vendidos en cantidad** en el **mes calendario actual** (año/mes de la fecha del servidor).
- Solo considera líneas de venta que llevan **producto de inventario** (no planes sueltos como “nombre de producto” si no vienen de catálogo).

### Caja abierta / cerrada

- Si existe una **caja abierta**, muestra **monto inicial** y **saldo calculado** (inicial + movimientos de ingreso en caja − movimientos de egreso en caja).
- Si no hay caja abierta, avisa y ofrece ir a **Caja** para abrir una.

> **Nota:** La caja registra **movimientos operativos** de efectivo en caja; los **totales financieros** del negocio siguen viniendo de **ventas** y **egresos** de contabilidad.

---

## 4. Asistencia

### Registro de entrada (pantalla principal de Asistencia)

- Busque y seleccione un **cliente activo** y registre su entrada.
- El cliente debe tener **membresía activa**; si no, el sistema mostrará un mensaje de error.
- Solo se permite **una asistencia por cliente y por día**; si ya ingresó hoy, verá una advertencia.
- En la misma pantalla suele verse el **listado del día** y totales de hoy.
- Las **asistencias** alimentan el contador del **Dashboard** y los **reportes**.

### Lista de asistencias

- Historial con **paginación**; puede filtrar por **fecha** y por **cliente** (según los filtros de la pantalla).

### Entrada ocasional

- Registro rápido de **visitante sin plan**: nombre, monto y método de pago.
- El sistema crea una **venta** de tipo ocasional, un registro de **cliente ocasional** y, si hay **caja abierta**, un **movimiento de ingreso** en caja vinculado a esa venta.

---

## 5. Punto de venta (POS)

Es donde se **cobran** ventas: productos del inventario, **membresías** y **entradas ocasionales**, incluso **mixtas** en un mismo ticket.

### Tipos de venta (internos del sistema)

| Tipo | Significado |
|------|-------------|
| **Producto** | Venta centrada en artículos del inventario. |
| **Membresía** | Venta de un plan al cliente (activa o renueva la membresía según proceso). |
| **Entrada ocasional** | Pase diario o entrada sin plan. |
| **Mixto** | Combinación en un mismo ticket (por ejemplo productos + algo más). |

### Métodos de pago

- **Efectivo**, **Transferencia**, **QR** (según lo elegido en cada venta).

### Listado y detalle de ventas

- Desde el menú o enlaces del dashboard puede abrir el **listado de ventas** y el **detalle** de una venta concreta.
- Todo lo cobrado por POS es lo que alimenta **ingresos**, **gráficos** y **contabilidad** (como ingresos).
- La **venta** se guarda siempre; el **ingreso en caja** automático solo ocurre si en ese momento hay **caja abierta** (si no, igual verá la venta en listados y reportes, pero no habrá movimiento de caja asociado).

---

## 6. Caja

Gestiona una **sesión de caja** (turno) y sus **movimientos**.

### Abrir caja

- Indica el **monto inicial** (fondo de caja).
- Solo puede haber **una caja abierta** a la vez; si ya hay una, el sistema lo avisará.

### Cerrar caja

- Registra el **cierre**, guarda el **saldo final** calculado y deja la caja en estado cerrada.

### Movimientos (cómo se registran)

En la pantalla de Caja usted **ve** la lista de movimientos; en la versión actual del sistema se generan así:

| Origen | Efecto en caja |
|--------|----------------|
| **Venta en el POS** | Si hay caja abierta, se agrega un **ingreso** por el total de la venta (referencia al número de venta). |
| **Entrada ocasional** (desde Asistencia) | Si hay caja abierta, **ingreso** por el monto cobrado. |
| **Nuevo egreso** (Contabilidad → Egresos) | Si hay caja abierta, **egreso** por el monto del egreso. **Importante:** para registrar un egreso contable el sistema exige que exista **caja abierta**. |

No es el mismo concepto que solo “anotar gasto”: el **Egreso** en contabilidad queda en la base de datos de egresos **y** refleja salida de caja cuando aplica lo anterior.

### Historial

- Consulta de **cajas cerradas** anteriores.

---

## 7. Clientes

| Acción | Descripción |
|--------|-------------|
| **Listado** | Busque y vea fichas de clientes. |
| **Nuevo** | Alta de cliente (datos personales, CI, contacto, foto si aplica, estado, notas). |
| **Detalle / Editar** | Ver o modificar la ficha. |

Los **clientes nuevos** que aparecen en **reportes** son los dados de alta en el período según la **fecha de registro** de la ficha.

---

## 8. Membresías

### Planes (catálogo)

- **Listado, crear y editar** planes: nombre, precio, duración en días, descripción, si el plan está activo para venta.

### Asignaciones

- **Listado** de membresías asignadas a clientes (fechas inicio/fin, estado: activa, expirada, cancelada).
- **Asignar** (o renovar vía venta según flujo): vincula un cliente con un plan; las fechas de fin suelen calcularse según la duración del plan.

Las **membresías activas** del Dashboard cuentan asignaciones en estado **activa**.

---

## 9. Inventario

| Acción | Descripción |
|--------|-------------|
| **Productos** | Listado del catálogo: nombre, precios, stock, stock mínimo, imagen opcional. |
| **Nuevo / Editar** | Mantenimiento del producto (incluye precio de compra y venta para cálculo de **ganancia** en ventas). |
| **Agregar stock** | Incrementar existencias sin pasar por una venta. |

El stock bajo puede generar **alertas** (véase sección Alertas).

---

## 10. Contabilidad

Pantalla de **resumen financiero por mes** (no es contabilidad de doble partida completa; es un **panel de ingresos y egresos** del negocio).

### Selector de mes

- Arriba puede elegir **año-mes** y pulsar **Filtrar**.
- Todos los totales de la pantalla se recalculan para ese **mes calendario**.

### Indicadores principales

| Indicador | Origen / cálculo |
|-----------|------------------|
| **Ingresos gimnasio** | Suma de `total` de **ventas** del mes con tipo **membresía** u **ocasional**. |
| **Ingresos productos** | Suma de `total` de **ventas** del mes con tipo **producto** o **mixto**. |
| **Total egresos** | Suma de **egresos** registrados en contabilidad en ese mes (`Egreso.monto`). |
| **Ganancia bruta (sin egresos)** | Igual que “ganancia neta” del reporte: margen de productos/mixto (`ganancia`) + ingresos de membresía/ocasional (`total`). |
| **Utilidad neta** | **Ganancia bruta** − **total egresos** del mes. Si es negativa, se muestra en rojo. |

### Enlaces rápidos

- **Ver egresos** → listado filtrable de egresos.
- **Ver ventas** → listado de ventas.

---

## 11. Egresos

Registro de **salidas de dinero** del negocio (gastos), distintas de los movimientos de “Caja” pero complementarias para ver **utilidad**.

### Listado

- Tabla de egresos con **fecha**, **tipo**, **descripción**, **monto**.
- **Filtros:** rango de fechas y tipo de egreso.
- Muestra un **total** de los egresos que cumplen el filtro (útil para sumar un período).

### Nuevo egreso

- Botón **Nuevo egreso**: tipo, monto, fecha, descripción.

### Tipos de egreso disponibles

- Compra de producto  
- Sueldos  
- Alquiler  
- Servicios (luz/agua/internet)  
- Mantenimiento  
- Otros  

---

## 12. Reportes

Consolida información por **día**, **rango de fechas (semana)** o **mes**.

### Tipos de reporte

1. **Diario** — elija un **día** concreto.  
2. **Semanal** — **desde** / **hasta** (cualquier rango; no tiene por qué ser semana ISO).  
3. **Mensual** — selector **año-mes**.

Pulse **Filtrar** para actualizar la vista.

### Indicadores del reporte

| Indicador | Origen |
|-----------|--------|
| **Ingresos totales** | Suma de `total` de **ventas** en el período. |
| **Egresos totales** | Suma de **egresos** de contabilidad en el período. |
| **Ganancia neta** | Misma lógica que en Dashboard/Contabilidad: margen productos/mixto + ingresos membresía/ocasional. |
| **Utilidad neta** | Ganancia neta − egresos totales. |
| **Asistencias** | Conteo de **asistencias** en el período. |
| **Clientes nuevos** | Clientes cuya **fecha de registro** cae en el período. |

*(El sistema calcula también ocasionales en el backend para el período; la tabla principal muestra ventas y egresos.)*

### Tablas

- **Ventas del período:** número, fecha/hora, tipo, total, método de pago.  
- **Egresos del período:** fecha, tipo, descripción, monto.

### Descargar PDF

- Botón **Descargar PDF** genera un documento con **ReportLab** usando los mismos filtros seleccionados (diario/semanal/mensual).

---

## 13. Alertas

- Listado de **alertas activas** (por ejemplo **stock bajo** en productos, **membresía vencida** o por vencer según reglas del sistema).
- El **Dashboard** al cargar puede **regenerar** alertas automáticamente.
- Puede existir una acción para **marcar como leída** o **regenerar** alertas según los botones de su pantalla.
- La **campana** del menú superior enlaza a esta sección.

---

## 14. Administración (solo administradores)

### Usuarios

- **Listado** de usuarios del sistema (login, nombre, rol administrador/empleado).
- **Crear** y **Editar** usuarios y contraseñas según formularios del sistema.

### Auditoría

- Registro de acciones relevantes (por ejemplo **inicio y cierre de sesión**, y otras operaciones que el sistema audite).
- Sirve para trazabilidad y revisión de uso.

---

## 15. Resumen: de dónde vienen los principales indicadores

| Necesita ver… | Debe registrar antes en… |
|---------------|---------------------------|
| Ingresos del día / mes | **Punto de venta** (ventas) |
| Egresos y utilidad neta | **Egresos** (contabilidad) + ventas |
| Asistencias | **Asistencia** |
| Membresías activas | **Membresías** (planes + asignaciones) + ventas que activen planes |
| Stock y alertas de inventario | **Inventario** (productos y stock) |
| Saldo de caja del turno | **Caja** (apertura, movimientos, cierre) |
| Clientes nuevos en reportes | **Clientes** (altas con fecha de registro) |

---

## Documentación relacionada

- Instalación en un PC nuevo (técnico): [MANUAL_INSTALACION_EQUIPO_NUEVO.md](MANUAL_INSTALACION_EQUIPO_NUEVO.md)  
- Instalación, backup y fallos habituales: [GUIA_USUARIO_FINAL.md](GUIA_USUARIO_FINAL.md)

---

## Soporte

*(Complete con datos de contacto de MISACORP o su distribuidor.)*

---

*Manual alineado con la versión de código del proyecto GYM ZT SIS (Django + PostgreSQL). Si tras una actualización cambian pantallas o campos, consulte la nota de versión o a su proveedor.*
