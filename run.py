from flask import Flask, render_template
import logging
import os
from config import Config
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

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = 'isla_encanto'

# inicializar extensiones
db.init_app(app)
bcrypt.init_app(app)

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
try:
    with app.app_context():
        try:
            inspector = inspect(db.engine)
            cols = [c['name'] for c in inspector.get_columns('usuario')] if 'usuario' in inspector.get_table_names() else []
            stmts = []
            # Agregar columnas para recuperación de contraseña si no existen
            if 'reset_code' not in cols:
                stmts.append("ALTER TABLE usuario ADD COLUMN reset_code VARCHAR(6) NULL")
            if 'reset_expire' not in cols:
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

        # Crear las tablas faltantes
        try:
            db.create_all()
        except Exception as e:
            app.logger.exception('Error creando tablas al iniciar: %s', e)
except Exception:
    # Ignorar si la app no está lista todavía
    pass

# ---------------- GOOGLE OAUTH ---------------- #
oauth = OAuth(app)
app.config['OAUTH'] = oauth

oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
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


# Aliases para el administrador (dashboard restaurante)
#from routes import admin as _admin
#app.add_url_rule('/admin/restaurante', endpoint='admin_restaurante', view_func=_admin.admin_restaurante)
#app.add_url_rule('/admin/restaurante/nuevo', endpoint='admin_restaurante_nuevo', view_func=_admin.admin_restaurante_nuevo, methods=['GET','POST'])
#app.add_url_rule('/admin/restaurante/editar/<int:plato_id>', endpoint='admin_restaurante_editar', view_func=_admin.admin_restaurante_editar, methods=['GET','POST'])
#app.add_url_rule('/admin/restaurante/eliminar/<int:plato_id>', endpoint='admin_restaurante_eliminar', view_func=_admin.admin_restaurante_eliminar, methods=['POST'])


# ------------------- Configuración de logs -------------------
logging.basicConfig(level=logging.DEBUG)

with app.app_context():
        # Asegurar columnas necesarias en la tabla usuario
        try:
            inspector = inspect(db.engine)
            cols = [c['name'] for c in inspector.get_columns('usuario')] if 'usuario' in inspector.get_table_names() else []
            stmts = []
            if 'reset_code' not in cols:
                stmts.append("ALTER TABLE usuario ADD COLUMN reset_code VARCHAR(6) NULL")
            if 'reset_expire' not in cols:
                stmts.append("ALTER TABLE usuario ADD COLUMN reset_expire DATETIME NULL")
            for s in stmts:
                try:
                    db.session.execute(text(s))
                    db.session.commit()
                    app.logger.info('Migración aplicada: %s', s)
                except Exception as e:
                    app.logger.exception('No se pudo aplicar la migración %s: %s', s, e)
        except Exception as e:
            app.logger.exception('Error revisando/alterando la tabla usuario: %s', e)

        # Crear tablas faltantes
        db.create_all()
# ------------------- Ejecución de la aplicación -------------------
if __name__ == '__main__':

    app.run(debug=True, host='0.0.0.0', port=5000)

