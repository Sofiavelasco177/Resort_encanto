from flask import Flask, render_template

app = Flask(__name__)

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
    app.run(debug=True, host="0.0.0.0", port=5000)
