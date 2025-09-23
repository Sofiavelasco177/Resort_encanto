from flask import Blueprint, render_template, request, redirect, url_for
from utils.extensions import db

perfil_usuario_bp = Blueprint('perfil_usuario', __name__, template_folder='../templates')

# Datos simulados de ejemplo
usuario = {
    "nombre": "Carlos Mendoza",
    "email": "c.mendoza@example.com",
    "telefono": "+1 (555) 123-4567",
    "membresia": "Oro",
    "foto": "https://via.placeholder.com/150",
    "reservas": [
        {"hotel": "Hotel Paraíso", "fecha": "2025-10-10", "estado": "Activa"},
        {"hotel": "Resort Encanto", "fecha": "2025-09-01", "estado": "Completada"}
    ]
}

# 👉 Ruta para mostrar perfil
@perfil_usuario_bp.route("/perfil_usuario")
def perfil():
    reservas_activas = [r for r in usuario["reservas"] if r["estado"] == "Activa"]
    estancias_pasadas = [r for r in usuario["reservas"] if r["estado"] == "Completada"]
    return render_template(
        "usuario/perfil_usuario.html",  # 👈 corregido (usuario, no usuarios)
        usuario=usuario,
        reservas_activas=reservas_activas,
        estancias_pasadas=estancias_pasadas
    )

# 👉 Ruta para editar perfil
@perfil_usuario_bp.route("/editar_perfil", methods=["POST"])
def editar_perfil():
    usuario["nombre"] = request.form["nombre"]
    usuario["email"] = request.form["email"]
    usuario["telefono"] = request.form["telefono"]
    return redirect(url_for("perfil_usuario.perfil"))  # 👈 corregido