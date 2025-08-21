from flask import Flask, render_template
from models.usuario import db  # Corrige aquí la importación
from config import Config   # Agrega esto si usas config.py
from routes.registro import registro_bp
from flask_login import current_user

app = Flask(__name__)
app.config.from_object(Config) # Configura la base de datos
db.init_app(app)               # Inicializa SQLAlchemy con la app
app.register_blueprint(registro_bp, url_prefix='/registro')

app.secret_key = 'islaencanto'  

# Ruta para la página principal
@app.route("/")
def home():
    return render_template("home/Home.html")

# Rutas adicionales
@app.route("/hospedaje")
def hospedaje():
    return render_template("home/Hospedaje.html")

@app.route("/restaurante")
def restaurantes():
    return render_template("home/Restaurante.html")

@app.route("/nosotros")
def nosotros():
    return render_template("home/Nosotros.html")

@app.route("/Experiencias")
def experiencias():
    return render_template("home/Experiencias.html")

@app.route("/login")
def login():
    return render_template("home/Login.html")

@app.context_processor
def inject_user():
    return dict(current_user=current_user)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5000)


