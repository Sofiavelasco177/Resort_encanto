from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.baseDatos import db, nuevaHabitacion, Usuario
from flask import session

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# Ruta para mostrar formulario de edición de habitación
@admin_bp.route("/hospedaje/editar/<int:habitacion_id>", methods=["GET"])
def hospedaje_editar(habitacion_id):
    habitacion = nuevaHabitacion.query.get_or_404(habitacion_id)
    return render_template("dashboard/editar_habitacion.html", habitacion=habitacion)

# Ruta para actualizar habitación en la base de datos
@admin_bp.route("/hospedaje/editar/<int:habitacion_id>", methods=["POST"])
def hospedaje_actualizar(habitacion_id):
    habitacion = nuevaHabitacion.query.get_or_404(habitacion_id)
    try:
        habitacion.nombre = request.form["nombre"]
        habitacion.precio = float(request.form["precio"])
        habitacion.cupo_personas = int(request.form.get("cupo_personas", 1))
        habitacion.estado = request.form.get("estado", "Disponible")
        imagen_file = request.files.get("imagen")
        if imagen_file and imagen_file.filename:
            import os
            from werkzeug.utils import secure_filename
            filename = secure_filename(imagen_file.filename)
            img_folder = os.path.join("Static", "img")
            os.makedirs(img_folder, exist_ok=True)
            save_path = os.path.join(img_folder, filename)
            imagen_file.save(save_path)
            habitacion.imagen = f"img/{filename}"
        db.session.commit()
    # flash("✅ Habitación actualizada correctamente", "success")
    except Exception as e:
        db.session.rollback()
    # flash(f"❌ Error al actualizar la habitación: {e}", "danger")
    return redirect(url_for("admin.hospedaje_index"))
from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.baseDatos import db, nuevaHabitacion, Usuario
from flask import session

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# ==========================
# 📌 SECCIÓN HOSPEDAJE
# ==========================
@admin_bp.route("/hospedaje")
def hospedaje_index():
    habitaciones = nuevaHabitacion.query.all()
    return render_template("dashboard/hospedaje_admin.html", habitaciones=habitaciones)

#añadir nueva habitacion ---------------------------------------------------------

@admin_bp.route("/hospedaje/nueva", methods=["POST"])
def hospedaje_nueva():
    try:
        nombre = request.form["nombre"]
        descripcion = request.form["descripcion"]
        print(f"[DEBUG] Descripción recibida: {descripcion}")
        precio = float(request.form["precio"])
        cupo_personas = int(request.form.get("cupo_personas", 1))
        estado = request.form.get("estado", "Disponible")
        imagen_file = request.files.get("imagen")
        imagen_path = None
        if imagen_file and imagen_file.filename:
            import os
            from werkzeug.utils import secure_filename
            filename = secure_filename(imagen_file.filename)
            img_folder = os.path.join("Static", "img")
            os.makedirs(img_folder, exist_ok=True)
            save_path = os.path.join(img_folder, filename)
            imagen_file.save(save_path)
            imagen_path = f"img/{filename}"

        habitacion = nuevaHabitacion(
            nombre=nombre,
            descripcion=descripcion,
            precio=precio,
            estado=estado,
            cupo_personas=cupo_personas,
            imagen=imagen_path
        )
        db.session.add(habitacion)
        db.session.commit()

        flash("✅ Habitación creada correctamente", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"❌ Error al crear la habitación: {e}", "danger")

    return redirect(url_for("admin.hospedaje_index"))

#editar habitacion ----------------------------------------------------------

@admin_bp.route("/hospedaje/editar/<int:habitacion_id>", methods=["POST"])
def hospedaje_editar(habitacion_id):
    habitacion = nuevaHabitacion.query.get_or_404(habitacion_id)
    try:
        habitacion.nombre = request.form["nombre"]
        habitacion.descripcion = request.form["descripcion"]
        habitacion.precio = float(request.form["precio"])
        habitacion.estado = request.form["estado"]
        habitacion.cupo_personas = int(request.form["cupo_personas"])
        db.session.commit()
        flash("✅ Habitación actualizada correctamente", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"❌ Error al editar la habitación: {e}", "danger")
    return redirect(url_for("admin.hospedaje_index"))

#eliminar habitacion ----------------------------------------------------------

@admin_bp.route("/hospedaje/eliminar/<int:habitacion_id>", methods=["POST"])
def hospedaje_eliminar(habitacion_id):
    habitacion = nuevaHabitacion.query.get_or_404(habitacion_id)
    try:
        db.session.delete(nuevaHabitacion)
        db.session.commit()
        flash("🗑️ Habitación eliminada", "warning")
    except Exception as e:
        db.session.rollback()
        flash(f"❌ Error al eliminar: {e}", "danger")

    return redirect(url_for("admin.hospedaje_index"))

# ==========================
# 📌 SECCIÓN RESTAURANTE
# ==========================
_platos_demo = []

@admin_bp.route("/home_dashboard")
def home_dashboard():
    return render_template("dashboard/home_dashboard.html")

@admin_bp.route("/restaurante")
def admin_restaurante():
    return render_template("dashboard/restaurante_admin.html", platos=_platos_demo)

#añadir nuevo plato ---------------------------------------------------------

@admin_bp.route("/restaurante/nuevo", methods=["POST"])
def admin_restaurante_nuevo():
    nombre = request.form.get("nombre")
    categoria = request.form.get("categoria")
    precio = float(request.form.get("precio") or 0)
    nuevo_id = max([p["id"] for p in _platos_demo]) + 1 if _platos_demo else 1
    _platos_demo.append({"id": nuevo_id, "nombre": nombre, "categoria": categoria, "precio": precio})
    return redirect(url_for("admin.admin_restaurante"))

#editar plato ----------------------------------------------------------

@admin_bp.route("/restaurante/editar/<int:plato_id>", methods=["GET", "POST"])
def admin_restaurante_editar(plato_id):
    plato = next((p for p in _platos_demo if p["id"] == plato_id), None)
    if not plato:
        return redirect(url_for("admin.admin_restaurante"))

    if request.method == "POST":
        plato["nombre"] = request.form.get("nombre")
        plato["categoria"] = request.form.get("categoria")
        plato["precio"] = float(request.form.get("precio") or 0)
        return redirect(url_for("admin.admin_restaurante"))

    return render_template("dashboard/restaurante_admin.html", platos=_platos_demo, plato=plato)

#eliminar plato ----------------------------------------------------------

@admin_bp.route("/restaurante/eliminar/<int:plato_id>", methods=["POST"])
def admin_restaurante_eliminar(plato_id):
    global _platos_demo
    _platos_demo = [p for p in _platos_demo if p["id"] != plato_id]
