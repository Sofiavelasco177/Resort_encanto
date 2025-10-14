from flask import Blueprint, render_template, request, redirect, url_for, session, current_app
from jinja2 import TemplateNotFound
from datetime import datetime
from models.baseDatos import nuevaHabitacion, Post, PlatoRestaurante

main_bp = Blueprint('main', __name__)

#Rutas Home ---------------------------------------------------------
 
@main_bp.route('/')
def home():
    # Contenido dinámico del home (ordenado por 'orden')
    posts = Post.query.filter_by(categoria='home').order_by(Post.orden.asc(), Post.creado_en.desc()).all()
    try:
        return render_template('home/Home.html', posts=posts)
    except TemplateNotFound as e:
        # Evitar 500 y dar pistas claras en logs
        current_app.logger.error(f"Plantilla no encontrada: {e}. Se esperaba 'home/Home.html'")
        return (
            "<h1>Plantilla no encontrada</h1>"
            "<p>No se encontró templates/home/Home.html en el contenedor.</p>"
            "<p>Revisa los Application Logs para ver el listado de archivos en templates/ y templates/home.</p>",
            500,
        )

@main_bp.route('/hospedaje')
def hospedaje():
    # Mostrar habitaciones públicas organizadas sin depender de groupby Jinja (evita TypeError con None)
    habitaciones = nuevaHabitacion.query.order_by(nuevaHabitacion.numero.asc()).all()

    # Agrupar en Python con fallback de plan y orden preferido
    prefer_order = ["Oro", "Plata", "Bronce", "Sin plan"]
    habitaciones_por_plan = {}
    for h in habitaciones:
        plan_label = (h.plan or '').strip() or 'Sin plan'
        habitaciones_por_plan.setdefault(plan_label, []).append(h)

    # Ordenar cada grupo por numero si existe, luego por id
    for key, items in habitaciones_por_plan.items():
        items.sort(key=lambda x: (x.numero if getattr(x, 'numero', None) is not None else 1_000_000, x.id))

    # Orden estable de planes
    presentes = list(habitaciones_por_plan.keys())
    plan_order = [p for p in prefer_order if p in presentes] + sorted([p for p in presentes if p not in prefer_order])

    return render_template('home/Hospedaje.html', habitaciones=habitaciones, habitaciones_por_plan=habitaciones_por_plan, plan_order=plan_order)

@main_bp.route('/restaurante')
def restaurantes():
    return render_template('home/Restaurante.html')

@main_bp.route('/nosotros')
def nosotros():
    # Mostrar solo contenido categorizado como 'nosotros'
    posts = Post.query.filter_by(categoria='nosotros', activo=True).order_by(Post.creado_en.desc()).limit(10).all()
    return render_template('home/Nosotros.html', posts=posts)

@main_bp.route('/Experiencias', methods=['GET', 'POST'])
def experiencias():
    comentarios = []
    if request.method == 'POST':
        contenido = request.form.get('contenido')
        rating = request.form.get('rating', 0)
        # Import current_user lazily to avoid hard dependency on flask_login at import time
        try:
            from flask_login import current_user
        except Exception:
            current_user = None

        if current_user and getattr(current_user, 'is_authenticated', False):
            username = getattr(current_user, 'usuario', None) or getattr(current_user, 'username', None) or session.get('user', {}).get('nombre')
            nuevo = {
                'user': {'username': username or 'Anónimo', 'avatar': None},
                'contenido': contenido,
                'rating': int(rating) if rating else 0,
                'created_at': datetime.now()
            }
            comentarios.append(nuevo)
    return render_template('home/Experiencias.html', comentarios=comentarios)

#Rutas Usuario -----------------------------------------------------------

@main_bp.route('/home_usuario')
def home_usuario():
    posts = Post.query.filter_by(categoria='home').order_by(Post.orden.asc(), Post.creado_en.desc()).all()
    return render_template('usuario/home_usuario.html', posts=posts)

@main_bp.route('/hospedaje_usuario')
def hospedaje_usuario():
    # Redirigir a la ruta del blueprint que carga los datos de habitaciones para usuarios
    return redirect(url_for('hospedaje_usuario.hospedaje_usuario'))

@main_bp.route('/restaurante_usuario')
def restaurante_usuario():
    # Obtener platos activos, agrupados por categoria
    platos = PlatoRestaurante.query.filter_by(activo=True).order_by(PlatoRestaurante.categoria.asc(), PlatoRestaurante.orden.asc(), PlatoRestaurante.creado_en.desc()).all()
    grupos = {}
    for p in platos:
        cat = p.categoria or 'Otros'
        grupos.setdefault(cat, []).append(p)
    categorias = ['Entradas','Principales','Postres','Bebidas']
    # mantener orden predefinido y añadir otras categorías al final
    cat_presentes = [c for c in categorias if c in grupos]
    extra = [c for c in grupos.keys() if c not in categorias]
    categorias_final = cat_presentes + extra
    return render_template('usuario/restaurante_usuario.html', grupos=grupos, categorias=categorias_final)

@main_bp.route('/experiencias_usuario')
def experiencias_usuario():
    return render_template('usuario/experiencias_usuario.html')

#@main_bp.route('/perfil_usuario')
#def perfil_usuario():
    #return render_template('usuario/perfil_usuario.html')


#Rutas Admin ------------------------------------------------------------

@main_bp.route('/home_admin')
def home_admin():
    # Traer posts de la categoría 'home' ordenados por 'orden' (asc)
    posts = Post.query.filter_by(categoria='home').order_by(Post.orden.asc(), Post.creado_en.desc()).all()
    return render_template('dashboard/home_admin.html', posts=posts)

@main_bp.route('/hospedaje_admin')
def hospedaje_admin():
    # Redirigir a la ruta del blueprint de administrador
    return redirect(url_for('admin.hospedaje_index'))

@main_bp.route('/restaurante_admin')
def restaurante_admin():
    return render_template('dashboard/restaurante_admin.html')

@main_bp.route('/experiencias_admin')
def experiencias_admin():
    return render_template('dashboard/experiencias_admin.html')

@main_bp.route('/nosotros_admin')
def nosotros_admin():
    return render_template('dashboard/nosotros_admin.html')



# Ruta de login demo para pruebas rápidas ---------------------------------

@main_bp.route('/demo-login', methods=['GET', 'POST'])
def demo_login():
    # Demo login kept for quick testing under /demo-login
    if request.method == 'POST':
        username = request.form.get('usuario')
        password = request.form.get('password')

        if username == "admin" and password == "1234":
            session['rol'] = 'admin'
            return redirect(url_for('main.home_admin'))
        else:
            session['rol'] = 'usuario'
            return redirect(url_for('main.home_usuario'))

    return render_template('home/Login.html')