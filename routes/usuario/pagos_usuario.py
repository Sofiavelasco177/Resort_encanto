from flask import Blueprint, render_template, request, redirect, url_for, current_app, flash, session
from models.baseDatos import db, Reserva, nuevaHabitacion
import os

pagos_usuario_bp = Blueprint('pagos_usuario', __name__)


def _current_user_id():
    return session.get('user', {}).get('id')


@pagos_usuario_bp.route('/pago/checkout/<int:reserva_id>')
def checkout_reserva(reserva_id):
    reserva = Reserva.query.get_or_404(reserva_id)
    # Seguridad básica: la reserva debe pertenecer al usuario actual
    uid = _current_user_id()
    if not uid or reserva.usuario_id != uid:
        flash('No autorizado para pagar esta reserva', 'danger')
        return redirect(url_for('registro.login'))

    public_key = os.getenv('WOMPI_PUBLIC_KEY', 'pub_test_ATgfa6zjR4rV4i2O1RrE8Gxx')  # Placeholder test key
    redirect_url = url_for('pagos_usuario.wompi_retorno', _external=True)

    # Wompi usa montos en centavos
    amount_in_cents = int((reserva.total or 0) * 100)
    reference = f"RES-{reserva.id}"

    return render_template(
        'usuario/checkout_wompi.html',
        reserva=reserva,
        wompi_public_key=public_key,
        amount_in_cents=amount_in_cents,
        reference=reference,
        redirect_url=redirect_url,
        currency='COP'
    )


@pagos_usuario_bp.route('/pago/wompi/retorno')
def wompi_retorno():
    # Nota: aquí idealmente se valida la transacción con el API de Wompi.
    # Para este paso inicial, marcamos la reserva como 'Activa'->'Completada' si viene 'id' y 'status'=APPROVED
    # y mostramos feedback al usuario.
    tx_id = request.args.get('id')
    status = request.args.get('status') or request.args.get('statusMessage')
    ref = request.args.get('reference')

    if not ref or not ref.startswith('RES-'):
        flash('Referencia de pago inválida', 'danger')
        return redirect(url_for('main.home_usuario'))

    try:
        rid = int(ref.split('-')[1])
    except Exception:
        flash('Referencia de pago inválida', 'danger')
        return redirect(url_for('main.home_usuario'))

    reserva = Reserva.query.get(rid)
    if not reserva:
        flash('Reserva no encontrada', 'danger')
        return redirect(url_for('main.home_usuario'))

    # Estado tentativo
    if (status or '').upper() in ('APPROVED', 'SUCCESS'):  # según retorno de Wompi
        reserva.estado = 'Completada'
        db.session.commit()
        flash('Pago aprobado. ¡Gracias!', 'success')
    else:
        reserva.estado = 'Activa'  # se mantiene, a la espera de validación
        db.session.commit()
        flash('Pago en proceso o no aprobado. Puedes intentarlo nuevamente.', 'warning')

    return redirect(url_for('perfil_usuario.perfil'))
