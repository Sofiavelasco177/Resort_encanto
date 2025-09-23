from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.extensions import db, bcrypt, serializer
from models.baseDatos import Usuario
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

recuperar_bp = Blueprint('recuperar', __name__)

# ------------------ Función para enviar correo ------------------
def enviar_email(destinatario, asunto, cuerpo):
    try:
        remitente = "jhdavidjuan@gmail.com"      # tu Gmail
        password = "svohvdxhjowanqra"            # contraseña de aplicación

        msg = MIMEMultipart()
        msg["From"] = remitente
        msg["To"] = destinatario
        msg["Subject"] = asunto
        msg.attach(MIMEText(cuerpo, "html"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(remitente, password)
        server.sendmail(remitente, destinatario, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"❌ Error al enviar correo: {e}")

# ------------------ RUTA: Solicitar recuperación ------------------
@recuperar_bp.route('/recuperar_contrasena', methods=['GET', 'POST'])
def recuperar_contrasena():
    if request.method == 'POST':
        correo = request.form['correo']
        usuario = Usuario.query.filter_by(correo=correo).first()

        if usuario:
            token = serializer.dumps(correo, salt='password-reset-salt')
            enlace = url_for('recuperar.restablecer_contrasena', token=token, _external=True)

            asunto = "Recuperación de contraseña"
            cuerpo = f"""
            <p>Hola {usuario.nombre if hasattr(usuario, 'nombre') else ''},</p>
            <p>Para restablecer tu contraseña, haz clic aquí:</p>
            <a href="{enlace}">{enlace}</a>
            <p>Este enlace expira en 1 hora.</p>
            """

            enviar_email(correo, asunto, cuerpo)
            flash("Te hemos enviado un correo con instrucciones.", "success")
        else:
            flash("El correo electrónico no está registrado.", "error")

    return render_template('home/recuperar_contraseña.html')

# ------------------ RUTA: Restablecer contraseña ------------------
@recuperar_bp.route('/restablecer_contrasena/<token>', methods=['GET', 'POST'])
def restablecer_contrasena(token):
    try:
        correo = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except:
        flash("El enlace es inválido o ha caducado.", "error")
        return redirect(url_for('recuperar.recuperar_contrasena'))

    usuario = Usuario.query.filter_by(correo=correo).first()
    if not usuario:
        flash("El usuario no existe.", "error")
        return redirect(url_for('recuperar.recuperar_contrasena'))

    if request.method == 'POST':
        nueva_contrasena = request.form['nueva_contrasena']
        hashed_password = bcrypt.generate_password_hash(nueva_contrasena).decode('utf-8')

        usuario.contrasena = hashed_password
        db.session.commit()

        flash("Tu contraseña ha sido restablecida.", "success")

        # 🔹 Redirección según el rol
        if usuario.rol == "admin":
            return redirect(url_for('main.home_admin'))   # dashboard/home_admin.html
        else:
            return redirect(url_for('main.home_usuario')) # usuario/home_usuario.html

    return render_template('home/restablecer_contraseña.html')
