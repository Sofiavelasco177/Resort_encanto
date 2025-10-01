from flask import Blueprint, request, redirect, url_for, flash, session, current_app
from models.baseDatos import db, Usuario
from werkzeug.security import generate_password_hash

auth_bp = Blueprint('auth', __name__)

# ---------------- GOOGLE LOGIN ---------------- #

@auth_bp.route('/google-login')
def google_login():
    oauth = current_app.config.get('OAUTH')
    if oauth is None:
        # Modo desarrollo (fake login si está activado)
        if current_app.config.get('ENABLE_DEV_GOOGLE'):
            return redirect(url_for('auth.google_dev_login'))
        flash('Google OAuth no está configurado.')
        return redirect(url_for('registro.login'))

    try:
        redirect_uri = url_for('auth.google_authorize', _external=True)
        current_app.logger.info(f"Iniciando login con Google. redirect_uri={redirect_uri}")
        return oauth.google.authorize_redirect(redirect_uri)
    except Exception as e:
        current_app.logger.exception(f'Error en Google login: {e}')
        # Si falla, usar modo desarrollo
        if current_app.config.get('ENABLE_DEV_GOOGLE'):
            return redirect(url_for('auth.google_dev_login'))
        flash('Error al iniciar sesión con Google. Intenta con usuario y contraseña.')
        return redirect(url_for('registro.login'))


@auth_bp.route('/google_authorize')
def google_authorize():
    oauth = current_app.config.get('OAUTH')
    if oauth is None:
        flash('Google OAuth no está configurado.')
        return redirect(url_for('registro.login'))

    # Obtener token y datos del usuario desde Google
    try:
        token = oauth.google.authorize_access_token()
        current_app.logger.info('Token de Google recibido correctamente')
        user_info = oauth.google.get('https://www.googleapis.com/oauth2/v3/userinfo').json()
        current_app.logger.info(f"Usuario Google: email={user_info.get('email')}")
    except Exception as e:
        current_app.logger.exception(f'Error al autorizar con Google: {e}')
        if current_app.config.get('ENABLE_DEV_GOOGLE'):
            return redirect(url_for('auth.google_dev_login'))
        flash('No se pudo completar el inicio de sesión con Google.')
        return redirect(url_for('registro.login'))

    # Buscar usuario en BD por correo
    usuario = Usuario.query.filter_by(correo=user_info['email']).first()

    if not usuario:
        usuario = Usuario(
            usuario=user_info.get('name', 'Usuario Google'),
            correo=user_info['email'],
            contrasena=generate_password_hash('google_placeholder', method='pbkdf2:sha256'),  # 🔹 HASH válido
            direccion=None,
            fechaNacimiento=None,
            rol='usuario'
        )
        db.session.add(usuario)
        db.session.commit()

    # Guardar sesión
    session['user'] = {
        'id': usuario.idUsuario,
        'nombre': usuario.usuario,
        'correo': usuario.correo,
        'rol': usuario.rol or 'usuario'
    }

    flash(f'¡Bienvenido, {usuario.usuario}!', 'success')

    if session['user']['rol'] == 'admin':
        return redirect(url_for('main.home_admin'))
    return redirect(url_for('main.home_usuario'))


@auth_bp.route('/google_dev_login')
def google_dev_login():
    """Simulación de login Google para desarrollo"""
    if not current_app.config.get('ENABLE_DEV_GOOGLE'):
        flash('Modo dev Google deshabilitado')
        return redirect(url_for('registro.login'))

    user_info = {
        'email': 'dev.user@example.com',
        'name': 'Usuario Dev'
    }

    usuario = Usuario.query.filter_by(correo=user_info['email']).first()
    if not usuario:
        usuario = Usuario(
            usuario=user_info.get('name', 'Usuario Dev'),
            correo=user_info['email'],
            contrasena=generate_password_hash('google_dev_placeholder', method='pbkdf2:sha256'),  # 🔹 HASH válido
            direccion=None,
            fechaNacimiento=None,
            rol='usuario'
        )
        db.session.add(usuario)
        db.session.commit()

    session['user'] = {
        'id': usuario.idUsuario,
        'nombre': usuario.usuario,
        'correo': usuario.correo,
        'rol': getattr(usuario, 'rol', 'usuario')
    }

    flash('Inicio de sesión simulado en modo desarrollo', 'info')
    return redirect(url_for('main.home_usuario'))


# ---------------- RECUPERAR CONTRASEÑA ---------------- #

@auth_bp.route('/password_recover', methods=['POST'])
def password_recover():
    correo = request.form.get('correo')
    if not correo:
        flash('Por favor ingresa un correo electrónico')
        return redirect(url_for('registro.login'))

    usuario = Usuario.query.filter_by(correo=correo).first()
    if usuario:
        flash('Si existe una cuenta con ese correo, se han enviado instrucciones a tu correo (simulado).')
    else:
        flash('No se encontró una cuenta asociada a ese correo')
    return redirect(url_for('registro.login'))
