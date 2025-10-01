from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from models.baseDatos import db, nuevaHabitacion, Usuario, InventarioHabitacion, InventarioItem
from datetime import datetime
from flask import session

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# Restringir el acceso a administradores para todas las rutas de este blueprint
@admin_bp.before_request
def _require_admin():
    user = session.get('user')
    if not user or user.get('rol') != 'admin':
        flash('Acceso restringido solo para administradores', 'warning')
        return redirect(url_for('registro.login'))

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
            img_folder = os.path.join(current_app.static_folder, "img")
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

# ==========================
# 📄 INVENTARIO DE HABITACIÓN (vista)
# ==========================
@admin_bp.route("/inventario")
def inventario_view():
    room_id = request.args.get('room_id', type=int)
    habitacion = None
    if room_id:
        habitacion = nuevaHabitacion.query.get(room_id)
    hotel_name = "Hotel Isla Encanto"
    return render_template("dashboard/inventario.html", habitacion=habitacion, hotel_name=hotel_name)

@admin_bp.route("/inventario", methods=["POST"])
def inventario_save():
    form = request.form
    # Create record
    # Helper to parse date 'YYYY-MM-DD' -> date
    def _pdate(val):
        try:
            return datetime.strptime(val, '%Y-%m-%d').date() if val else None
        except Exception:
            return None

    rec = InventarioHabitacion(
        habitacion_id = (int(form.get('habitacion_id')) if form.get('habitacion_id') else None),
        hotel = form.get('hotel'),
        room_number = form.get('room_number'),
        room_type = form.get('room_type'),
        inspection_date = _pdate(form.get('inspection_date')),
        inspector = form.get('inspector'),
        observations = form.get('observations'),
        rating_cleaning = int(form.get('rating_cleaning', 0) or 0),
        rating_furniture = int(form.get('rating_furniture', 0) or 0),
        rating_equipment = int(form.get('rating_equipment', 0) or 0),
        inspector_signature = form.get('inspector_signature'),
        inspector_date = _pdate(form.get('inspector_date')),
        supervisor_signature = form.get('supervisor_signature'),
        supervisor_date = _pdate(form.get('supervisor_date')),
    )

    # Parse dynamic items: expect names like item__category__key fields: check, qty, text
    # For simplicity, define a fixed list mapping to our form elements
    def add_item(category, key, label, checked, quantity=None, value_text=None):
        itm = InventarioItem(
            record=rec,
            category=category,
            key=key,
            label=label,
            checked=bool(checked),
            quantity=(int(quantity) if (quantity is not None and str(quantity).strip() != '') else None),
            value_text=(value_text if value_text else None)
        )
        db.session.add(itm)

    # Map of fields: (category, checkbox name, qty name, text name, label)
    mappings = [
        ("dorm_mob", 'bed', 'bed_qty', None, 'Cama'),
        ("dorm_mob", 'nightstand', 'nightstand_qty', None, 'Mesitas de noche'),
        ("dorm_mob", 'lamps', 'lamps_qty', None, 'Lámparas de mesa'),
        ("dorm_mob", 'closet', None, None, 'Armario/Closet'),
        ("dorm_mob", 'chair', 'chair_qty', None, 'Silla/Sillón'),
        ("dorm_mob", 'desk', None, None, 'Escritorio'),
        ("dorm_mob", 'mirror', None, None, 'Espejo de pared'),
        ("ropa", 'mattress', None, 'mattress_state', 'Colchón'),
        ("ropa", 'pillows', 'pillows_qty', None, 'Almohadas'),
        ("ropa", 'sheets', None, None, 'Sábanas juego completo'),
        ("ropa", 'comforter', None, None, 'Edredón/Colcha'),
        ("ropa", 'blanket', None, None, 'Cobertor adicional'),
        ("ropa", 'cushions', 'cushions_qty', None, 'Cojines decorativos'),
        ("banio", 'bath_mirror', None, None, 'Espejo'),
        ("banio", 'towel_rack', None, None, 'Toallero/Perchero'),
        ("banio", 'trash_bin', None, None, 'Papelera'),
        ("banio", 'scale', None, None, 'Balanza/Báscula'),
        ("banio", 'hairdryer', None, None, 'Secador de cabello'),
        ("banio_am", 'bath_towels', 'bath_towels_qty', None, 'Toallas grandes'),
        ("banio_am", 'hand_towels', 'hand_towels_qty', None, 'Toallas de mano'),
        ("banio_am", 'soap', None, None, 'Jabón/Gel de baño'),
        ("banio_am", 'shampoo', None, None, 'Shampoo'),
        ("banio_am", 'conditioner', None, None, 'Acondicionador'),
        ("banio_am", 'lotion', None, None, 'Loción corporal'),
        ("banio_am", 'dental_kit', None, None, 'Kit dental'),
        ("banio_am", 'toilet_paper', 'toilet_paper_qty', None, 'Papel higiénico'),
        ("electro", 'tv', None, 'tv_model', 'Televisor'),
        ("electro", 'remote', None, None, 'Control remoto TV'),
        ("electro", 'phone', None, None, 'Teléfono'),
        ("electro", 'alarm', None, None, 'Radio reloj despertador'),
        ("electro", 'safe', None, None, 'Caja fuerte'),
        ("electro", 'minibar', None, None, 'Minibar/Refrigerador'),
        ("electro", 'coffee_maker', None, None, 'Cafetera/Hervidor'),
        ("menaje", 'glasses', 'glasses_qty', None, 'Vasos de vidrio'),
        ("menaje", 'cups', 'cups_qty', None, 'Tazas/Mugs'),
        ("menaje", 'spoons', 'spoons_qty', None, 'Cucharas'),
        ("menaje", 'opener', None, None, 'Abrebotellas'),
        ("menaje", 'coffee', 'coffee_qty', None, 'Café/Té'),
        ("menaje", 'sugar', 'sugar_qty', None, 'Azúcar/Endulzante'),
        ("otros", 'curtains', None, None, 'Cortinas decorativas'),
        ("otros", 'blackout', None, None, 'Cortinas blackout'),
        ("otros", 'directory', None, None, 'Directorio de servicios'),
        ("otros", 'menu', None, None, 'Menú room service'),
        ("otros", 'smoke_detector', None, None, 'Detector de humo'),
        ("otros", 'evacuation_map', None, None, 'Mapa de evacuación'),
        ("otros", 'hangers', 'hangers_qty', None, 'Perchas en closet'),
        ("otros", 'umbrella', None, None, 'Paraguas'),
    ]

    try:
        db.session.add(rec)
        for cat, key, qty_key, text_key, label in mappings:
            checked = form.get(key) == 'on'
            qty = form.get(qty_key) if qty_key else None
            text_val = form.get(text_key) if text_key else None
            add_item(cat, key, label, checked, qty, text_val)
        db.session.commit()
        flash("✅ Inventario guardado", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"❌ Error guardando inventario: {e}", "danger")
    return redirect(url_for('admin.inventario_view'))

@admin_bp.route('/inventarios')
def inventarios_list():
    registros = InventarioHabitacion.query.order_by(InventarioHabitacion.created_at.desc()).limit(50).all()
    return render_template('dashboard/inventarios_list.html', registros=registros)

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
            img_folder = os.path.join(current_app.static_folder, "img")
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
