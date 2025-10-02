from flask import Blueprint, render_template, request, redirect, url_for, flash, session
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

        # Guardar huésped en BD
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

        # Crear Reserva formal
        try:
            check_in = datetime.strptime(request.form.get('check_in'), '%Y-%m-%d').date()
            check_out = datetime.strptime(request.form.get('check_out'), '%Y-%m-%d').date()
        except Exception:
            flash('Fechas inválidas', 'danger')
            return redirect(url_for('hospedaje_usuario.reservar_habitacion', habitacion_id=habitacion.id))

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
