from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models.baseDatos import db, nuevaHabitacion, Huesped, Reserva
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

hospedaje_usuario_bp = Blueprint('hospedaje_usuario', __name__)

@hospedaje_usuario_bp.route('/hospedaje_usuario')
def hospedaje_usuario():
    habitaciones = nuevaHabitacion.query.order_by(nuevaHabitacion.plan.asc(), nuevaHabitacion.numero.asc()).all()
    # Agrupar por plan para la vista
    grouped = { 'Oro': [], 'Plata': [], 'Bronce': [], 'Otro': [] }
    for h in habitaciones:
        key = (h.plan or 'Otro')
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(h)
    return render_template('usuario/hospedaje_usuario.html', habitaciones=habitaciones, habitaciones_por_plan=grouped)


@hospedaje_usuario_bp.route('/reservar/<int:habitacion_id>', methods=['GET', 'POST'])
def reservar_habitacion(habitacion_id):
    habitacion = nuevaHabitacion.query.get_or_404(habitacion_id)

    if request.method == 'POST':
        # Requiere usuario logueado
        uid = session.get('user', {}).get('id')
        if not uid:
            flash('Inicia sesión para continuar con la reserva', 'warning')
            return redirect(url_for('registro.login'))

        # Validar fechas y disponibilidad antes de persistir
        try:
            check_in = datetime.strptime(request.form.get('check_in'), '%Y-%m-%d').date()
            check_out = datetime.strptime(request.form.get('check_out'), '%Y-%m-%d').date()
        except Exception:
            flash('Fechas inválidas', 'danger')
            return redirect(url_for('hospedaje_usuario.reservar_habitacion', habitacion_id=habitacion.id))

        if check_out <= check_in:
            flash('La fecha de salida debe ser posterior al check-in', 'danger')
            return redirect(url_for('hospedaje_usuario.reservar_habitacion', habitacion_id=habitacion.id))

        # Bloquear fechas si hay traslape con reservas activas/no canceladas
        if not _habitacion_disponible(habitacion.id, check_in, check_out):
            flash('La habitación no está disponible para las fechas seleccionadas. Por favor elige otras fechas.', 'warning')
            return redirect(url_for('hospedaje_usuario.reservar_habitacion', habitacion_id=habitacion.id))

        # Validar número de documento (columna es Integer actualmente)
        ndoc_raw = (request.form.get('numeroDocumento') or '').strip()
        try:
            ndoc = int(ndoc_raw)
        except Exception:
            flash('El número de documento debe ser numérico.', 'danger')
            return redirect(url_for('hospedaje_usuario.reservar_habitacion', habitacion_id=habitacion.id))

        # Guardar o reutilizar huésped en BD (evitar error de UNIQUE)
        huesped = Huesped.query.filter_by(numeroDocumento=ndoc).first()
        if huesped:
            # Actualizar datos básicos para mantenerlos al día
            huesped.nombre = request.form.get('nombre') or huesped.nombre
            huesped.tipoDocumento = request.form.get('tipoDocumento') or huesped.tipoDocumento
            huesped.telefono = request.form.get('telefono') or huesped.telefono
            huesped.correo = request.form.get('correo') or huesped.correo
            huesped.procedencia = request.form.get('procedencia') or huesped.procedencia
            huesped.nuevaHabitacion_id = habitacion.id
        else:
            huesped = Huesped(
                nombre=request.form['nombre'],
                tipoDocumento=request.form['tipoDocumento'],
                numeroDocumento=ndoc,
                telefono=request.form.get('telefono'),
                correo=request.form.get('correo'),
                procedencia=request.form.get('procedencia'),
                nuevaHabitacion_id=habitacion.id  # Usa la FK correcta
            )
            db.session.add(huesped)

        noches = max(1, (check_out - check_in).days)
        total = float(habitacion.precio or 0) * noches

        reserva = Reserva(
            usuario_id=uid,
            habitacion_id=habitacion.id,
            check_in=check_in,
            check_out=check_out,
            estado='Activa',
            total=total
        )
        db.session.add(reserva)
        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            # Mensaje genérico; en logs quedará el detalle
            flash('No se pudo crear la reserva. Verifica tus datos e inténtalo de nuevo.', 'danger')
            # Registrar error para diagnóstico
            try:
                from flask import current_app
                current_app.logger.exception('Error guardando reserva/huésped: %s', e)
            except Exception:
                pass
            return redirect(url_for('hospedaje_usuario.reservar_habitacion', habitacion_id=habitacion.id))

        # Redirigir a checkout (Wompi)
        return redirect(url_for('pagos_usuario.checkout_reserva', reserva_id=reserva.id))

    return render_template('usuario/reservas.html', habitacion=habitacion)


def _habitacion_disponible(habitacion_id: int, check_in, check_out) -> bool:
    """Retorna True si no existen reservas traslapadas para la habitación en el rango dado.
    La lógica de traslape permite check-in el mismo día del check-out previo.
    """
    # Excluir reservas canceladas
    qs = Reserva.query.filter(
        Reserva.habitacion_id == habitacion_id,
        Reserva.estado != 'Cancelada'
    )
    # overlap si (nuevo_in < existente_out) y (nuevo_out > existente_in)
    qs = qs.filter(Reserva.check_in < check_out, Reserva.check_out > check_in)
    return qs.count() == 0


@hospedaje_usuario_bp.route('/disponibilidad/<int:habitacion_id>')
def disponibilidad_habitacion(habitacion_id):
    """Endpoint simple para consultar disponibilidad por fechas."""
    habitacion = nuevaHabitacion.query.get_or_404(habitacion_id)
    sin = request.args.get('check_in')
    sout = request.args.get('check_out')
    try:
        d_in = datetime.strptime(sin, '%Y-%m-%d').date() if sin else None
        d_out = datetime.strptime(sout, '%Y-%m-%d').date() if sout else None
    except Exception:
        return jsonify({'ok': False, 'error': 'invalid_dates'}), 400

    if not d_in or not d_out or d_out <= d_in:
        return jsonify({'ok': False, 'error': 'invalid_range'}), 400

    available = _habitacion_disponible(habitacion.id, d_in, d_out)
    return jsonify({'ok': True, 'available': available})
