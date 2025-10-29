from flask import Blueprint, request, redirect, url_for, flash, session, current_app
from models.baseDatos import db, Usuario
from werkzeug.security import generate_password_hash

auth_bp = Blueprint('auth', __name__)

# ---------------- GOOGLE LOGIN ---------------- #

def _build_google_redirect_uri(next_param=None):
   
    try:
        host = request.host or ''
        # Dominios locales típicos
        is_local = ('localhost' in host) or host.startswith('127.0.0.1')
        if not is_local:
            base = 'https://hotelencanto.isladigital.xyz'
            # Usar el alias '/google/authorize' (más común en consolas de Google)
            uri = f"{base}{url_for('auth.google_authorize_alias')}"
        else:
            # Local: respetar host y esquema http y usar la ruta histórica '/google_authorize'
            # para coincidir con las URIs autorizadas en la consola de Google.
            uri = url_for('auth.google_authorize', _external=True, _scheme='http')
        # No anexamos `next` a la redirect_uri para evitar redirect_uri_mismatch en Google.
        # El `next` lo persistimos en sesión.
        return uri
    except Exception:
        # Fallback general
        return url_for('auth.google_authorize', _external=True)


@auth_bp.route('/google-login')
def google_login():
    # Propagar `next` para volver post-login
    next_param = request.args.get('next')
    oauth = current_app.config.get('OAUTH')
    if oauth is None:
        # Modo desarrollo (fake login si está activado)
        if current_app.config.get('ENABLE_DEV_GOOGLE'):
            return redirect(url_for('auth.google_dev_login', next=next_param))
        flash('Google OAuth no está configurado.')
        return redirect(url_for('registro.login', next=next_param))

    try:
        # Guardar `next` en sesión (no en redirect_uri)
        try:
            if next_param:
                session['oauth_next'] = next_param
        except Exception:
            pass
        # Respetar esquema preferido (https en prod) si está configurado
        redirect_uri = _build_google_redirect_uri(None)
        current_app.logger.info(f"Iniciando login con Google. redirect_uri={redirect_uri}")
        return oauth.google.authorize_redirect(redirect_uri)
    except Exception as e:
        current_app.logger.exception(f'Error en Google login: {e}')
        # Si falla, usar modo desarrollo
        if current_app.config.get('ENABLE_DEV_GOOGLE'):
            return redirect(url_for('auth.google_dev_login', next=next_param))
        flash('Error al iniciar sesión con Google. Intenta con usuario y contraseña.')
        return redirect(url_for('registro.login', next=next_param))


@auth_bp.route('/google_authorize')
def google_authorize():
    # Recuperar `next` desde query (si viniera) o desde sesión
    next_param = request.args.get('next') or session.pop('oauth_next', None)
    oauth = current_app.config.get('OAUTH')
    if oauth is None:
        flash('Google OAuth no está configurado.')
        return redirect(url_for('registro.login', next=next_param))

    # Obtener token y datos del usuario desde Google
    try:
        # Forzar endpoints explícitos para entornos donde el discovery falle
        TOKEN_URL = "https://oauth2.googleapis.com/token"
        redirect_uri = _build_google_redirect_uri(None)
        # Si no viene 'code' en la URL, no intentes intercambiar token
        if not request.args.get('code'):
            current_app.logger.warning('Google authorize sin parámetro code; redirigiendo al login de Google')
            return redirect(url_for('auth.google_login', next=next_param))

        # Evitar authorize_access_token (que intenta parsear id_token y requiere jwks_uri).
        # Intercambiamos el código manualmente sin parsear el id_token.
        code = request.args.get('code')
        token = oauth.google.fetch_access_token(
            # token_endpoint=TOKEN_URL,  # opcional: usa el registrado
            code=code,
            grant_type='authorization_code',
            redirect_uri=redirect_uri
        )
        if not token or 'access_token' not in token:
            raise RuntimeError('No se recibió access_token de Google')
        current_app.logger.info('Token de Google recibido correctamente')
        user_info = oauth.google.get('https://openidconnect.googleapis.com/v1/userinfo', token=token).json()
        current_app.logger.info(f"Usuario Google: email={user_info.get('email')}")
    except Exception as e:
        current_app.logger.exception(f'Error al autorizar con Google: {e}')
        if current_app.config.get('ENABLE_DEV_GOOGLE'):
            return redirect(url_for('auth.google_dev_login', next=next_param))
        flash('No se pudo completar el inicio de sesión con Google.')
        return redirect(url_for('registro.login', next=next_param))

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

    # Guardar sesión (incluir avatar si existe en BD o si Google entrega picture)
    session['user'] = {
        'id': usuario.idUsuario,
        'nombre': usuario.usuario,
        'correo': usuario.correo,
        'rol': usuario.rol or 'usuario',
        'avatar': getattr(usuario, 'avatar', None) or user_info.get('picture')
    }

    flash(f'¡Bienvenido, {usuario.usuario}!', 'success')

    # Redirigir a next si está presente y es seguro
    try:
        from urllib.parse import urlparse
        if next_param:
            u = urlparse(next_param)
            if (not u.netloc) and (u.path.startswith('/')):
                return redirect(next_param)
    except Exception:
        pass
    if session['user']['rol'] == 'admin':
        return redirect(url_for('main.home_admin'))
    return redirect(url_for('main.home_usuario'))


# Alias adicional para evitar errores de configuración en Google Console
# Si la consola tiene registrado /google/authorize, aceptamos también esa ruta
@auth_bp.route('/google/authorize')
def google_authorize_alias():
    return google_authorize()


# Endpoint de depuración para verificar configuración de OAuth (no expone secretos)
@auth_bp.route('/oauth/debug')
def oauth_debug():
    try:
        host = request.host or ''
        is_local = ('localhost' in host) or host.startswith('127.0.0.1')
        redirect_uri = _build_google_redirect_uri(None)
        # Evitar exponer secretos; solo mostramos prefijo del client_id si existe en config/env
        import os
        client_id = os.environ.get('GOOGLE_CLIENT_ID') or current_app.config.get('GOOGLE_CLIENT_ID')
        client_id_preview = (client_id[:12] + '…') if client_id else None
        return {
            'host': host,
            'is_local': is_local,
            'computed_redirect_uri': redirect_uri,
            'client_id_preview': client_id_preview,
            'oauth_configured': bool(current_app.config.get('OAUTH'))
        }
    except Exception as e:
        return {'error': str(e)}, 500


# Alias solicitado: /login/google → mismo flujo que /google-login
@auth_bp.route('/login/google')
def login_google():
    return google_login()


@auth_bp.route('/google_dev_login')
def google_dev_login():
    next_param = request.args.get('next')
    """Simulación de login Google para desarrollo"""
    if not current_app.config.get('ENABLE_DEV_GOOGLE'):
        flash('Modo dev Google deshabilitado')
        return redirect(url_for('registro.login', next=next_param))

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
        'rol': getattr(usuario, 'rol', 'usuario'),
        'avatar': getattr(usuario, 'avatar', None)
    }

    flash('Inicio de sesión simulado en modo desarrollo', 'info')
    if next_param:
        try:
            from urllib.parse import urlparse
            u = urlparse(next_param)
            if (not u.netloc) and (u.path.startswith('/')):
                return redirect(next_param)
        except Exception:
            pass
    return redirect(url_for('main.home_usuario'))

@auth_bp.route('/logout')
def logout():
    """Cerrar sesión del usuario actual"""
    try:
        session.pop('user', None)
    except Exception:
        pass
    flash('Sesión cerrada', 'info')
    return redirect(url_for('registro.login'))


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
