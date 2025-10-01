from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_from_directory, current_app
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from utils.extensions import db
from models.baseDatos import Usuario, MetodoPago, Reserva, Notificacion, ActividadUsuario, Factura, nuevaHabitacion

perfil_usuario_bp = Blueprint('perfil_usuario', __name__, template_folder='../templates')

def _current_user():
    uid = session.get('user', {}).get('id')
    return Usuario.query.get(uid) if uid else None

# Vista principal de perfil
@perfil_usuario_bp.route("/perfil_usuario")
def perfil():
    user = _current_user()
    if not user:
        flash('Inicia sesión para ver tu perfil', 'warning')
        return redirect(url_for('registro.login'))

    metodos = MetodoPago.query.filter_by(usuario_id=user.idUsuario).all()
    reservas = Reserva.query.filter_by(usuario_id=user.idUsuario).order_by(Reserva.check_in.desc()).all()
    notifs = Notificacion.query.filter_by(usuario_id=user.idUsuario).order_by(Notificacion.creado_en.desc()).limit(10).all()
    actividad = ActividadUsuario.query.filter_by(usuario_id=user.idUsuario).order_by(ActividadUsuario.creado_en.desc()).limit(10).all()
    facturas = Factura.query.filter_by(usuario_id=user.idUsuario).order_by(Factura.creado_en.desc()).limit(10).all()

    return render_template(
        "usuario/perfil_usuario.html",
        user=user,
        metodos=metodos,
        reservas=reservas,
        notifs=notifs,
        actividad=actividad,
        facturas=facturas,
    )

# Actualizar perfil y avatar
@perfil_usuario_bp.route("/perfil_usuario/editar", methods=["POST"])
def editar_perfil():
    user = _current_user()
    if not user:
        flash('Inicia sesión primero', 'warning')
        return redirect(url_for('registro.login'))

    user.usuario = request.form.get('usuario') or user.usuario
    user.correo = request.form.get('correo') or user.correo
    user.telefono = request.form.get('telefono') or user.telefono
    user.direccion = request.form.get('direccion') or user.direccion
    user.plan_tipo = request.form.get('plan_tipo') or user.plan_tipo
    user.membresia_activa = True if request.form.get('membresia_activa') == 'on' else False
    exp = request.form.get('membresia_expira')
    if exp:
        try:
            user.membresia_expira = datetime.strptime(exp, '%Y-%m-%d').date()
        except Exception:
            pass
    user.notif_checkin = True if request.form.get('notif_checkin') == 'on' else False
    user.notif_checkout = True if request.form.get('notif_checkout') == 'on' else False

    # Avatar
    avatar_file = request.files.get('avatar')
    if avatar_file and avatar_file.filename:
        filename = secure_filename(avatar_file.filename)
        dest = os.path.join(current_app.static_folder, 'img', 'avatars')
        os.makedirs(dest, exist_ok=True)
        avatar_file.save(os.path.join(dest, filename))
        user.avatar = f"img/avatars/{filename}"

    try:
        db.session.commit()
        flash('Perfil actualizado', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {e}', 'danger')
    return redirect(url_for('perfil_usuario.perfil'))

# Métodos de pago CRUD
@perfil_usuario_bp.route('/perfil_usuario/metodo_pago/nuevo', methods=['POST'])
def mp_nuevo():
    user = _current_user()
    mp = MetodoPago(
        usuario_id=user.idUsuario,
        marca=request.form.get('marca'),
        ultimos4=request.form.get('ultimos4'),
        tipo=request.form.get('tipo'),
        exp_mes=int(request.form.get('exp_mes') or 0) or None,
        exp_anio=int(request.form.get('exp_anio') or 0) or None,
        predeterminado=(request.form.get('predeterminado') == 'on')
    )
    if mp.predeterminado:
        MetodoPago.query.filter_by(usuario_id=user.idUsuario, predeterminado=True).update({'predeterminado': False})
    db.session.add(mp)
    db.session.commit()
    flash('Método de pago agregado', 'success')
    return redirect(url_for('perfil_usuario.perfil'))

@perfil_usuario_bp.route('/perfil_usuario/metodo_pago/<int:mid>/eliminar', methods=['POST'])
def mp_eliminar(mid):
    mp = MetodoPago.query.get_or_404(mid)
    db.session.delete(mp)
    db.session.commit()
    flash('Método de pago eliminado', 'warning')
    return redirect(url_for('perfil_usuario.perfil'))

@perfil_usuario_bp.route('/perfil_usuario/metodo_pago/<int:mid>/predeterminado', methods=['POST'])
def mp_predeterminado(mid):
    user = _current_user()
    MetodoPago.query.filter_by(usuario_id=user.idUsuario, predeterminado=True).update({'predeterminado': False})
    mp = MetodoPago.query.get_or_404(mid)
    mp.predeterminado = True
    db.session.commit()
    flash('Método predeterminado actualizado', 'success')
    return redirect(url_for('perfil_usuario.perfil'))

# Descargar factura
@perfil_usuario_bp.route('/perfil_usuario/factura/<int:fid>')
def descargar_factura(fid):
    fac = Factura.query.get_or_404(fid)
    # Si file_path es relativo a static
    if not os.path.isabs(fac.file_path):
        dirpath = current_app.static_folder
        filename = fac.file_path.replace('\\', '/').split('/')[-1]
        subdir = fac.file_path.replace(filename, '').strip('/\\')
        full_dir = os.path.join(dirpath, subdir)
        return send_from_directory(full_dir, filename, as_attachment=True)
    # Si es absoluto
    base = os.path.dirname(fac.file_path)
    fname = os.path.basename(fac.file_path)
    return send_from_directory(base, fname, as_attachment=True)