from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.usuario import db, Usuario
from datetime import datetime

registro_bp = Blueprint('registro', __name__)

@registro_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contraseña = request.form['contraseña']
        user = Usuario.query.filter_by(usuario=usuario, contrasña=contraseña).first()
        if user:
            flash(f'¡Bienvenido, {user.usuario}!')
            if hasattr(user, 'rol') and user.rol == 'admin':
                return redirect(url_for('dashboard/index.html'))  # Cambia 'dashboard' por tu ruta real
            else:
                return redirect(url_for('home/home'))  # Cambia 'home' por tu ruta real
        else:
            flash('Usuario o contraseña incorrectos')
    return render_template('home/Login.html')

@registro_bp.route('/register', methods=['POST'])
def register():
    usuario = request.form['usuario']
    correo = request.form['correo']
    contraseña = request.form['contraseña']
    direccion = request.form['direccion']
    fechaNacimiento = datetime.strptime(request.form['fechaNacimiento'], "%Y-%m-%d").date()

    # Verificar si el correo ya existe
    if Usuario.query.filter_by(correo=correo).first():
        flash('El correo ya está registrado. Intenta con otro.')
        return redirect(url_for('registro.login'))

    nuevo_usuario = Usuario(
        usuario=usuario,
        correo=correo,
        contraseña=contraseña,  # Corregido
        direccion=direccion,
        fechaNacimiento=fechaNacimiento
    )
    db.session.add(nuevo_usuario)
    db.session.commit()
    flash('¡Registro exitoso! Ahora puedes iniciar sesión.')
    return redirect(url_for('registro.login'))