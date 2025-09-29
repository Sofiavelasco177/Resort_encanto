from flask import Flask, render_template
import logging
import os
from datetime import datetime
from config import Config

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
from flask import Blueprint

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__, static_folder='Static', static_url_path='/static')

# Debug: Log de la configuración de la base de datos
logger.info(f"DATABASE_URL configurada: {'Sí' if os.environ.get('DATABASE_URL') else 'No'}")
logger.info(f"DB_USER configurada: {'Sí' if os.environ.get('DB_USER') else 'No'}")

try:
    app.config.from_object(Config)
    app.secret_key = 'isla_encanto'
    
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
                for s in stmts:
                    try:
                        db.session.execute(text(s))
                        db.session.commit()
                        app.logger.info('Migración aplicada: %s', s)
                    except Exception as e:
                        app.logger.exception('No se pudo aplicar la migración %s: %s', s, e)

            except Exception as e:
                app.logger.exception('Error revisando/alterando la tabla usuario al iniciar: %s', e)

    except Exception as e:
        app.logger.exception('Error inicializando la base de datos: %s', e)

# Inicializar la base de datos solo si la app está lista
try:
    # Deshabilitado temporalmente para evitar errores al inicio
    # init_database()
    pass
except Exception:
    # Ignorar si la app no está lista todavía
    pass

# ---------------- GOOGLE OAUTH ---------------- #
oauth = OAuth(app)
app.config['OAUTH'] = oauth

# Verificar que las credenciales estén cargadas
client_id = os.getenv("GOOGLE_CLIENT_ID")
client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

if client_id and client_secret:
    app.logger.info(f'Google OAuth configurado con Client ID: {client_id[:10]}...')
    try:
        # Configurar OAuth con timeout más corto
        oauth.register(
            name='google',
            client_id=client_id,
            client_secret=client_secret,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile", "timeout": 10}  # Timeout de 10 segundos
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
            authorize_url='https://accounts.google.com/oauth2/auth',
            token_url='https://oauth2.googleapis.com/token',
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
        authorize_url='https://accounts.google.com/oauth2/auth',
        token_url='https://oauth2.googleapis.com/token',
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


app.register_blueprint(registro_bp, url_prefix='/registro')
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')  # ✅ Registrar blueprint admin
app.register_blueprint(recuperar_bp, url_prefix='/recuperar')
app.register_blueprint(hospedaje_usuario_bp, url_prefix='/hospedaje')
app.register_blueprint(perfil_usuario_bp, url_prefix='/perfil')



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


# Health check endpoint para debug
@app.route('/health')
def health_check():
    try:
        # Probar conexión a la base de datos
        db.engine.execute(text('SELECT 1'))
        return {
            'status': 'healthy', 
            'database': 'connected',
            'timestamp': str(datetime.now())
        }, 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            'status': 'unhealthy', 
            'database': 'disconnected',
            'error': str(e),
            'timestamp': str(datetime.now())
        }, 500

# Aliases para el administrador (dashboard restaurante)
#from routes import admin as _admin
#app.add_url_rule('/admin/restaurante', endpoint='admin_restaurante', view_func=_admin.admin_restaurante)
#app.add_url_rule('/admin/restaurante/nuevo', endpoint='admin_restaurante_nuevo', view_func=_admin.admin_restaurante_nuevo, methods=['GET','POST'])
#app.add_url_rule('/admin/restaurante/editar/<int:plato_id>', endpoint='admin_restaurante_editar', view_func=_admin.admin_restaurante_editar, methods=['GET','POST'])
#app.add_url_rule('/admin/restaurante/eliminar/<int:plato_id>', endpoint='admin_restaurante_eliminar', view_func=_admin.admin_restaurante_eliminar, methods=['POST'])


# ------------------- Configuración de logs -------------------
logging.basicConfig(level=logging.DEBUG)

# ------------------- Ejecución de la aplicación -------------------
if __name__ == '__main__':
    import os
    
    # En desarrollo usa el servidor de Flask
    if os.getenv('FLASK_ENV') == 'development':
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        # En producción, usar Gunicorn es más seguro
        app.run(debug=False, host='0.0.0.0', port=5000)

