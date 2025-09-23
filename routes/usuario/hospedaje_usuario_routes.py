from flask import Blueprint, render_template, request, redirect, url_for
from models.baseDatos import db, habitacionHuesped, Huesped
from datetime import datetime

hospedaje_usuario_bp = Blueprint('hospedaje_usuario', __name__)

@hospedaje_usuario_bp.route('/hospedaje_usuario')
def hospedaje_usuario():
    habitaciones = habitacionHuesped.query.all()
    return render_template('usuario/hospedaje_usuario.html', habitaciones=habitaciones)


@hospedaje_usuario_bp.route('/reservar/<int:habitacion_id>', methods=['GET', 'POST'])
def reservar_habitacion(habitacion_id):
    habitacion = habitacionHuesped.query.get_or_404(habitacion_id)

    if request.method == 'POST':
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

        # Opcional: actualizar fechas de la habitación
        habitacion.check_in = datetime.strptime(request.form['fecha_inicio'], "%Y-%m-%d").date()
        habitacion.check_out = datetime.strptime(request.form['fecha_fin'], "%Y-%m-%d").date()

        db.session.commit()
        return redirect(url_for('main.home_usuario'))  # Ajusta al nombre de tu página

    return render_template('reservar.html', habitacion=habitacion)
