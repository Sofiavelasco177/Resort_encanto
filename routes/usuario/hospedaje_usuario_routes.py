from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models.baseDatos import db, nuevaHabitacion, Huesped, Reserva
from datetime import datetime

hospedaje_usuario_bp = Blueprint('hospedaje_usuario', __name__)

@hospedaje_usuario_bp.route('/hospedaje_usuario')
def hospedaje_usuario():
    habitaciones = nuevaHabitacion.query.all()
    return render_template('usuario/hospedaje_usuario.html', habitaciones=habitaciones)


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

        # Guardar huésped en BD (ya validamos disponibilidad)
        huesped = Huesped(
            nombre=request.form['nombre'],
            tipoDocumento=request.form['tipoDocumento'],
            numeroDocumento=request.form['numeroDocumento'],
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
        db.session.commit()

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
