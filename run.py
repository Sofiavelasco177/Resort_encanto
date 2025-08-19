from flask import Flask, render_template
from models.usuario import db  # Corrige aquí la importación
from config import Config   # Agrega esto si usas config.py

app = Flask(__name__)
app.config.from_object(Config) # Configura la base de datos
db.init_app(app)               # Inicializa SQLAlchemy con la app

# Ruta para la página principal
@app.route("/")
def home():
    return render_template("home.html")

# Rutas adicionales
@app.route("/hospedaje")
def hospedaje():
    return render_template("hospedaje.html")

@app.route("/restaurante")
def restaurantes():
    return render_template("restaurante.html")

@app.route("/nosotros")
def nosotros():
    return render_template("nosotros.html")

@app.route("/Experiencias")
def experiencias():
    return render_template("Experiencias.html")

@app.route("/login")
def login():
    return render_template("login.html")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5000)


