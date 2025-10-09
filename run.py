from flask import Flask, render_template, send_from_directory
import logging
import os
from datetime import datetime
from config import Config
from werkzeug.middleware.proxy_fix import ProxyFix

# Configurar logging temprano
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from sqlalchemy import inspect, text
from models.baseDatos import Usuario
from routes.main import main_bp
from routes.registro import registro_bp
from routes.auth import auth_bp
from authlib.integrations.flask_client import OAuth
from utils.extensions import db, bcrypt, serializer
from routes.usuario.perfil_usuario_routes import perfil_usuario_bp
from routes.usuario.pagos_usuario import pagos_usuario_bp
from flask import Blueprint

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv()

# Preferir minúsculas por compatibilidad Linux; fallback a 'Static' si es lo que existe
default_static = 'static' if os.path.isdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')) else 'Static'
app = Flask(__name__, template_folder='templates', static_folder=default_static, static_url_path='/static')
# Respetar cabeceras del proxy (X-Forwarded-Proto, Host, etc.) para generar URLs https correctas
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

# Soportar nombres de carpetas con mayúsculas (por compatibilidad)
base_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(base_dir, 'templates')
templates_dir_cap = os.path.join(base_dir, 'Templates')
static_dir = os.path.join(base_dir, 'static')
static_dir_cap = os.path.join(base_dir, 'Static')

try:
    # Siempre incluir ambas rutas si existen, primero 'templates', luego 'Templates'
    search_paths = list(getattr(app.jinja_loader, 'searchpath', []))
    to_add = []
    if os.path.isdir(templates_dir) and templates_dir not in search_paths:
        to_add.append(templates_dir)
    if os.path.isdir(templates_dir_cap) and templates_dir_cap not in search_paths:
        to_add.append(templates_dir_cap)
    if to_add:
        # Insertar al inicio manteniendo el orden preferido
        for p in reversed(to_add):
            search_paths.insert(0, p)
        app.jinja_loader.searchpath = search_paths
        logger.info(f"Plantillas: rutas de búsqueda actualizadas: {app.jinja_loader.searchpath}")
except Exception as e:
    logger.warning(f"No se pudo ajustar rutas de plantillas: {e}")

if not os.path.isdir(static_dir) and os.path.isdir(static_dir_cap):
    # Reasignar static_folder si solo existe 'Static'
    try:
        app.static_folder = static_dir_cap
        logger.info("Usando carpeta 'Static' como fallback para archivos estáticos")
    except Exception as e:
        logger.warning(f"No se pudo reasignar static_folder a 'Static': {e}")

# Debug: Log de la configuración de la base de datos
logger.info(f"DATABASE_URL configurada: {'Sí' if os.environ.get('DATABASE_URL') else 'No'}")
logger.info(f"DB_USER configurada: {'Sí' if os.environ.get('DB_USER') else 'No'}")

# Asegurar ruta de plantillas y loguearla para diagnosticar TemplateNotFound
templates_path = templates_dir if os.path.isdir(templates_dir) else (templates_dir_cap if os.path.isdir(templates_dir_cap) else os.path.join(base_dir, 'templates'))
try:
    search_paths = getattr(app.jinja_loader, 'searchpath', [])
    logger.info(f"Rutas de búsqueda de plantillas iniciales: {search_paths}")
    if templates_path not in search_paths:
        search_paths.insert(0, templates_path)
        app.jinja_loader.searchpath = search_paths
        logger.info(f"Rutas de búsqueda de plantillas actualizadas: {app.jinja_loader.searchpath}")
    # Comprobar si existe la plantilla principal esperada
    home_tpl = os.path.join(templates_path, 'home', 'Home.html')
    logger.info(f"Existe templates/home/Home.html? {'Sí' if os.path.exists(home_tpl) else 'No'} ({home_tpl})")
    try:
        logger.info(f"Listado de templates/: {os.listdir(templates_path)}")
        home_dir = os.path.join(templates_path, 'home')
        if os.path.isdir(home_dir):
            logger.info(f"Listado de templates/home: {os.listdir(home_dir)}")
        else:
            logger.info("La carpeta templates/home no existe")
    except Exception as e_ls:
        logger.warning(f"No se pudo listar templates: {e_ls}")
except Exception as e:
    logger.warning(f"No se pudo ajustar rutas de plantillas: {e}")

try:
    app.config.from_object(Config)
    import os as _os
    app.secret_key = _os.getenv('SECRET_KEY') or 'isla_encanto'
    
    # Log de la URI final que se está usando (sin mostrar credenciales completas)
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    if 'mysql' in db_uri:
        logger.info("Usando MySQL como base de datos")
    else:
        logger.info("Usando SQLite como base de datos de fallback")
        
    logger.info("Configuración de Flask aplicada exitosamente")
except Exception as e:
    logger.error(f"Error al configurar Flask: {e}")
    raise

# inicializar extensiones
try:
    db.init_app(app)
    logger.info("SQLAlchemy inicializado correctamente")
    bcrypt.init_app(app)
    logger.info("Bcrypt inicializado correctamente")
except Exception as e:
    logger.error(f"Error al inicializar extensiones: {e}")
    raise

from itsdangerous import URLSafeTimedSerializer
import utils.extensions as extensions
extensions.serializer = URLSafeTimedSerializer(app.secret_key)

perfil_bp = Blueprint("perfil_usuario", __name__, url_prefix="/usuario")


# Inyectar el usuario actual en todas las plantillas (aunque flask_login no esté instalado)
@app.context_processor

def inject_current_user():
    try:
        from flask_login import current_user
        return {'current_user': current_user}
    except Exception:
        class _Anonymous:
            is_authenticated = False
        return {'current_user': _Anonymous()}


# Verificar y crear columnas necesarias en la tabla usuario
def init_database():
    try:
        with app.app_context():
            # Asegurar que el directorio instance existe y tiene permisos
            import os
            # Usar ruta relativa para desarrollo local
            instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
            
            if not os.path.exists(instance_dir):
                os.makedirs(instance_dir, exist_ok=True)
                app.logger.info(f'Directorio instance creado: {instance_dir}')
            
            try:
                # Crear las tablas primero
                db.create_all()
                app.logger.info('Tablas de la base de datos creadas/verificadas')
                
                # Luego verificar columnas
                inspector = inspect(db.engine)
                cols = [c['name'] for c in inspector.get_columns('usuario')] if 'usuario' in inspector.get_table_names() else []
                stmts = []
                # Agregar columnas para recuperación de contraseña si no existen
                if cols and 'reset_code' not in cols:
                    stmts.append("ALTER TABLE usuario ADD COLUMN reset_code VARCHAR(6) NULL")
                if cols and 'reset_expire' not in cols:
                    stmts.append("ALTER TABLE usuario ADD COLUMN reset_expire DATETIME NULL")
                # Columnas nuevas del modelo Usuario para compatibilidad con esquemas antiguos
                if cols and 'telefono' not in cols:
                    stmts.append("ALTER TABLE usuario ADD COLUMN telefono VARCHAR(20) NULL")
                if cols and 'avatar' not in cols:
                    stmts.append("ALTER TABLE usuario ADD COLUMN avatar VARCHAR(255) NULL")
                if cols and 'plan_tipo' not in cols:
                    stmts.append("ALTER TABLE usuario ADD COLUMN plan_tipo VARCHAR(50) NULL")
                if cols and 'membresia_activa' not in cols:
                    stmts.append("ALTER TABLE usuario ADD COLUMN membresia_activa TINYINT(1) DEFAULT 0")
                if cols and 'membresia_expira' not in cols:
                    stmts.append("ALTER TABLE usuario ADD COLUMN membresia_expira DATE NULL")
                if cols and 'notif_checkin' not in cols:
                    stmts.append("ALTER TABLE usuario ADD COLUMN notif_checkin TINYINT(1) DEFAULT 1")
                if cols and 'notif_checkout' not in cols:
                    stmts.append("ALTER TABLE usuario ADD COLUMN notif_checkout TINYINT(1) DEFAULT 1")
                for s in stmts:
                    try:
                        db.session.execute(text(s))
                        db.session.commit()
                        app.logger.info('Migración aplicada: %s', s)
                    except Exception as e:
                        db.session.rollback()
                        app.logger.exception('No se pudo aplicar la migración %s: %s', s, e)

                # Migraciones para tabla post (agregar columna 'orden')
                try:
                    post_cols = [c['name'] for c in inspector.get_columns('post')] if 'post' in inspector.get_table_names() else []
                except Exception:
                    post_cols = []
                if 'post' in inspector.get_table_names() and 'orden' not in post_cols:
                    try:
                        db.session.execute(text("ALTER TABLE post ADD COLUMN orden INTEGER NOT NULL DEFAULT 0"))
                        db.session.commit()
                        app.logger.info('Columna orden agregada a post')
                    except Exception as e:
                        db.session.rollback()
                        app.logger.exception('No se pudo agregar columna orden a post: %s', e)

                # Backfill orden para posts de categoría 'home'
                try:
                    from models.baseDatos import Post
                    home_posts = db.session.query(Post).filter(Post.categoria == 'home').order_by(Post.creado_en.asc()).all()
                    changed = False
                    for idx, p in enumerate(home_posts, start=1):
                        if getattr(p, 'orden', 0) in (None, 0):
                            p.orden = idx
                            changed = True
                    if changed:
                        db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    app.logger.warning('No se pudo hacer backfill de orden en posts home: %s', e)

                # Migrar imágenes legacy de static/img/uploads -> instance/uploads
                try:
                    from models.baseDatos import Post
                    import shutil
                    legacy_prefix = os.path.join(app.static_folder, 'img', 'uploads')
                    inst_uploads = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'uploads')
                    os.makedirs(inst_uploads, exist_ok=True)
                    posts = db.session.query(Post).filter(Post.imagen.isnot(None)).all()
                    migrated = False
                    for p in posts:
                        path = (p.imagen or '').strip()
                        if not path:
                            continue
                        # Si ya está en 'uploads/', no migrar
                        if path.startswith('uploads/'):
                            continue
                        # Si es 'img/uploads/...' intentar mover
                        if path.startswith('img/uploads/'):
                            fname = path.split('img/uploads/', 1)[1]
                            src = os.path.join(legacy_prefix, fname)
                            dst = os.path.join(inst_uploads, fname)
                            try:
                                if os.path.isfile(src):
                                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                                    shutil.move(src, dst)
                                    p.imagen = f'uploads/{fname}'
                                    migrated = True
                            except Exception as em:
                                app.logger.warning(f'No se pudo migrar imagen {src} -> {dst}: {em}')
                    if migrated:
                        db.session.commit()
                        app.logger.info('Migración de imágenes a instance/uploads completada')
                except Exception as e:
                    db.session.rollback()
                    app.logger.warning('No se pudo migrar imágenes legacy: %s', e)

            except Exception as e:
                app.logger.exception('Error revisando/alterando la tabla usuario al iniciar: %s', e)

    except Exception as e:
        app.logger.exception('Error inicializando la base de datos: %s', e)

# Inicializar/verificar esquema de base de datos en cualquier motor (SQLite o MySQL)
try:
    logger.info('Verificando esquema de base de datos y aplicando migraciones seguras...')
    init_database()
except Exception as _e:
    logger.warning(f"No se pudo inicializar/verificar automáticamente la base de datos: {_e}")

# ---------------- GOOGLE OAUTH ---------------- #
oauth = OAuth(app)
app.config['OAUTH'] = oauth

# Verificar que las credenciales estén cargadas
client_id = os.getenv("GOOGLE_CLIENT_ID")
client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

# Endpoints explícitos de Google para evitar fallos de descubrimiento
GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

if client_id and client_secret:
    app.logger.info(f'Google OAuth configurado con Client ID: {client_id[:10]}...')
    try:
        # Registrar con endpoints explícitos (más robusto en entornos con red limitada)
        oauth.register(
            name='google',
            client_id=client_id,
            client_secret=client_secret,
            authorize_url=GOOGLE_AUTHORIZE_URL,
            token_url=GOOGLE_TOKEN_URL,
            client_kwargs={"scope": "openid email profile", "timeout": 10}
        )
        app.logger.info('Google OAuth registrado exitosamente')
    except Exception as e:
        app.logger.warning(f'Error configurando Google OAuth: {e}. Usando modo desarrollo.')
        app.config['ENABLE_DEV_GOOGLE'] = True
        # Registrar cliente dummy para evitar errores
        oauth.register(
            name='google',
            client_id='dummy',
            client_secret='dummy',
            authorize_url=GOOGLE_AUTHORIZE_URL,
            token_url=GOOGLE_TOKEN_URL,
            client_kwargs={"scope": "openid email profile"}
        )
else:
    app.logger.warning('Credenciales de Google OAuth no encontradas. Usando modo desarrollo.')
    app.config['ENABLE_DEV_GOOGLE'] = True
    # Registrar cliente dummy para evitar errores
    oauth.register(
        name='google',
        client_id='dummy',
        client_secret='dummy',
        authorize_url=GOOGLE_AUTHORIZE_URL,
        token_url=GOOGLE_TOKEN_URL,
        client_kwargs={"scope": "openid email profile"}
    )



# ------------------- Registro de Blueprints -------------------
from routes.registro import registro_bp
from routes.main import main_bp
from routes.auth import auth_bp
from routes.dashboard.admin import admin_bp
from routes.recuperar_contraseña import recuperar_bp
from routes.usuario.hospedaje_usuario_routes import hospedaje_usuario_bp
from routes.usuario.perfil_usuario_routes import perfil_usuario_bp
from routes.dashboard.perfil_admin_routes import perfil_admin_bp


app.register_blueprint(registro_bp, url_prefix='/registro')
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')  # ✅ Registrar blueprint admin
app.register_blueprint(recuperar_bp, url_prefix='/recuperar')
app.register_blueprint(hospedaje_usuario_bp, url_prefix='/hospedaje')
app.register_blueprint(perfil_usuario_bp, url_prefix='/perfil')
app.register_blueprint(pagos_usuario_bp, url_prefix='/usuario')
app.register_blueprint(perfil_admin_bp)



# ------------------- Aliases de Rutas (compatibilidad con plantillas) -------------------
from routes import main as _main
from routes import auth as _auth
from routes import registro as _registro

# Rutas públicas
app.add_url_rule('/', endpoint='home', view_func=_main.home)
app.add_url_rule('/hospedaje', endpoint='hospedaje', view_func=_main.hospedaje)
app.add_url_rule('/restaurante', endpoint='restaurantes', view_func=_main.restaurantes)
app.add_url_rule('/nosotros', endpoint='nosotros', view_func=_main.nosotros)
app.add_url_rule('/Experiencias', endpoint='experiencias', view_func=_main.experiencias, methods=['GET', 'POST'])
app.add_url_rule('/login', endpoint='login', view_func=_registro.login, methods=['GET', 'POST'])

#Ruta de autenticación con Google (implementada en auth.py)
app.add_url_rule('/google-login', endpoint='google_login', view_func=_auth.google_login)


# Health check y verificación de entorno (sin filtrar secretos)
@app.route('/health')
def health_check():
    import os as _os
    def _bool_env(name, default=False):
        val = _os.getenv(name)
        if val is None:
            return default
        return str(val).lower() in ("1", "true", "yes", "on")

    # Estado DB
    db_status = 'unknown'
    http_code = 200
    try:
        db.engine.execute(text('SELECT 1'))
        db_status = 'connected'
    except Exception as e:
        logger.error(f"Health check DB failed: {e}")
        db_status = f'unavailable: {e}'
        http_code = 500

    # Entorno
    uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    is_sqlite = 'sqlite' in (uri or '')
    is_mysql = 'mysql' in (uri or '')

    static_dir = app.static_folder
    instance_dir = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'instance')

    def _is_writable(path):
        try:
            return _os.path.isdir(path) and _os.access(path, _os.W_OK)
        except Exception:
            return False

    env_report = {
        'flask_env': _os.getenv('FLASK_ENV', 'unset'),
        'secret_key_from_env': bool(_os.getenv('SECRET_KEY')),
        'database_url_set': bool(_os.getenv('DATABASE_URL')),
        'db_uri_kind': 'sqlite' if is_sqlite else ('mysql' if is_mysql else 'other'),
        'static_folder_exists': _os.path.isdir(static_dir),
        'static_folder_writable': _is_writable(static_dir),
        'instance_exists': _os.path.isdir(instance_dir),
        'instance_writable': _is_writable(instance_dir),
        'smtp': {
            'host_set': bool(_os.getenv('SMTP_HOST')),
            'user_set': bool(_os.getenv('SMTP_USER')),
            'password_set': bool(_os.getenv('SMTP_PASSWORD')),
            'use_tls': _bool_env('SMTP_USE_TLS', True),
            'use_ssl': _bool_env('SMTP_USE_SSL', False),
        },
        'google_oauth': {
            'client_id_set': bool(_os.getenv('GOOGLE_CLIENT_ID')),
            'client_secret_set': bool(_os.getenv('GOOGLE_CLIENT_SECRET')),
        },
    }

    return {
        'status': 'healthy' if http_code == 200 else 'unhealthy',
        'database': db_status,
        'env': env_report,
        'static_folder': static_dir,
        'timestamp': str(datetime.now())
    }, http_code

# Aliases para el administrador (dashboard restaurante)
#from routes import admin as _admin
#app.add_url_rule('/admin/restaurante', endpoint='admin_restaurante', view_func=_admin.admin_restaurante)
#app.add_url_rule('/admin/restaurante/nuevo', endpoint='admin_restaurante_nuevo', view_func=_admin.admin_restaurante_nuevo, methods=['GET','POST'])
#app.add_url_rule('/admin/restaurante/editar/<int:plato_id>', endpoint='admin_restaurante_editar', view_func=_admin.admin_restaurante_editar, methods=['GET','POST'])
#app.add_url_rule('/admin/restaurante/eliminar/<int:plato_id>', endpoint='admin_restaurante_eliminar', view_func=_admin.admin_restaurante_eliminar, methods=['POST'])


# ------------------- Configuración de logs -------------------
logging.basicConfig(level=logging.DEBUG)

# ------------------- Ejecución de la aplicación -------------------

# Servir archivos de medios dinámicos desde instance/uploads
@app.route('/media/<path:filename>')
def media_file(filename):
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'uploads')
    # Seguridad básica: normalizar y restringir a carpeta
    return send_from_directory(base, filename, conditional=True)
if __name__ == '__main__':
    import os
    
    # En desarrollo usa el servidor de Flask
    if os.getenv('FLASK_ENV') == 'development':
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        # En producción, usar Gunicorn es más seguro
        app.run(debug=False, host='0.0.0.0', port=5000)

