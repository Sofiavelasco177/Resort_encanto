from flask import Blueprint, render_template, request, redirect, url_for, current_app, flash, session, jsonify
from models.baseDatos import db, Reserva, nuevaHabitacion
import os
import requests
import hmac
import hashlib

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
    # Usar esquema preferido si está configurado (https en prod detrás de proxy)
    scheme = current_app.config.get('PREFERRED_URL_SCHEME', 'http')
    redirect_url = url_for('pagos_usuario.wompi_retorno', _external=True, _scheme=scheme)

    # Wompi usa montos en centavos
    amount_in_cents = int((reserva.total or 0) * 100)
    reference = f"RES-{reserva.id}"
    habitacion = nuevaHabitacion.query.get(reserva.habitacion_id)

    return render_template(
        'usuario/checkout_wompi.html',
        reserva=reserva,
        habitacion=habitacion,
        wompi_public_key=public_key,
        amount_in_cents=amount_in_cents,
        reference=reference,
        redirect_url=redirect_url,
        currency='COP',
        country='CO'
    )


@pagos_usuario_bp.route('/pago/wompi/retorno')
def wompi_retorno():
    # Validación con API de Wompi
    tx_id = request.args.get('id')
    ref = request.args.get('reference')
    status_q = request.args.get('status') or request.args.get('statusMessage')

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

    status_final = (status_q or '').upper()

    # Intentar verificar con Wompi si tenemos id de transacción
    if tx_id:
        base = _wompi_base_url()
        try:
            resp = requests.get(f"{base}/v1/transactions/{tx_id}", timeout=10)
            if resp.ok:
                data = resp.json() or {}
                status_final = (data.get('data', {}).get('status') or status_final or '').upper()
                ref_api = data.get('data', {}).get('reference')
                # Si la referencia de API no coincide, no arriesgar estado
                if ref_api and ref_api != ref:
                    current_app.logger.warning('Referencia Wompi no coincide. ref=%s api=%s', ref, ref_api)
            else:
                current_app.logger.warning('No se pudo verificar transacción Wompi %s: %s', tx_id, resp.text)
        except Exception as e:
            current_app.logger.exception('Error verificando Wompi: %s', e)

    _apply_status_to_reserva(reserva, status_final)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()

    if status_final == 'APPROVED':
        flash('Pago aprobado. ¡Gracias!', 'success')
    elif status_final in ('DECLINED', 'ERROR', 'VOIDED'):  # distintos estados negativos
        flash('El pago no fue aprobado. Puedes intentarlo nuevamente.', 'danger')
    else:
        flash('Pago en proceso. Te informaremos cuando sea confirmado.', 'info')

    return redirect(url_for('perfil_usuario.perfil'))


@pagos_usuario_bp.route('/pago/wompi/webhook', methods=['POST'])
def wompi_webhook():
    # Valida firma HMAC para garantizar que el evento proviene de Wompi
    secret = os.getenv('WOMPI_EVENTS_SECRET') or os.getenv('WOMPI_WEBHOOK_SECRET') or ''
    sig = request.headers.get('X-Event-Signature', '')
    if not secret or not sig:
        return jsonify({'ok': False, 'error': 'missing_signature'}), 400

    try:
        expected = 'sha256=' + hmac.new(secret.encode('utf-8'), request.data, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, sig):
            current_app.logger.warning('Firma de webhook inválida. Expected %s got %s', expected, sig)
            return jsonify({'ok': False, 'error': 'invalid_signature'}), 400
    except Exception as e:
        current_app.logger.exception('Error validando firma: %s', e)
        return jsonify({'ok': False, 'error': 'signature_error'}), 400

    payload = request.get_json(silent=True) or {}
    event = payload.get('event') or payload.get('eventName') or ''
    data = payload.get('data') or {}
    tx = data.get('transaction') or {}
    status = (tx.get('status') or '').upper()
    ref = tx.get('reference') or ''

    if not ref.startswith('RES-'):
        return jsonify({'ok': True})  # ignorar eventos que no son de reservas

    try:
        rid = int(ref.split('-')[1])
    except Exception:
        return jsonify({'ok': True})

    reserva = Reserva.query.get(rid)
    if not reserva:
        return jsonify({'ok': True})

    _apply_status_to_reserva(reserva, status)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception('Error guardando estado reserva: %s', e)
        return jsonify({'ok': False}), 500

    return jsonify({'ok': True})


def _wompi_base_url():
    # Determina sandbox o producción según la llave pública
    pub = os.getenv('WOMPI_PUBLIC_KEY', '')
    if pub.startswith('pub_test'):
        return 'https://sandbox.wompi.co'
    return 'https://production.wompi.co'


def _apply_status_to_reserva(reserva: Reserva, wompi_status: str):
    st = (wompi_status or '').upper()
    if st == 'APPROVED':
        # Mantener bloqueadas las fechas: 'Completada' confirma ocupación
        reserva.estado = 'Completada'
    elif st in ('DECLINED', 'ERROR', 'VOIDED'):  # cancelada/declinada
        # Liberar fechas: 'Cancelada' libera disponibilidad para ese rango
        reserva.estado = 'Cancelada'
    else:
        reserva.estado = 'Activa'
