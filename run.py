from flask import Flask, render_template

app = Flask(__name__)

# Ruta para la página principal
@app.route("/")
def home():
    return render_template("home.html")

# Rutas adicionales
@app.route("/hospedaje")
def hospedaje():
    return "Página de Hospedaje"

@app.route("/restaurantes")
def restaurantes():
    return "Página de Restaurantes"

@app.route("/nosotros")
def nosotros():
    return "Página de Nosotros"

@app.route("/login")
def login():
    return "Página de Login/Registro"

if __name__ == "__main__":
    app.run(debug=True)
