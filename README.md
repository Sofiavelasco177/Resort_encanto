# Resort Encanto - Aplicación Flask

Una aplicación web para la gestión de un resort con funcionalidades de reservas, autenticación y administración.

## 🚀 Despliegue con Docker

### Requisitos previos
- Docker instalado
- Docker Compose instalado

### Configuración rápida

1. **Clonar el repositorio**
```bash
git clone <tu-repositorio>
cd Resort_encanto
```



3. **Construir y ejecutar con Docker Compose**
```bash
docker-compose up --build
```

La aplicación estará disponible en http://localhost:5000

### Comandos útiles

**Construir la imagen Docker:**
```bash
docker build -t resort-encanto .
```

**Ejecutar el contenedor:**
```bash
docker run -p 5000:5000 --env-file .env resort-encanto
```

**Ver logs:**
```bash
docker-compose logs -f
```

**Detener los servicios:**
```bash
docker-compose down
```

## 📦 Despliegue en servicios cloud

### Railway
1. Conecta tu repositorio a Railway
2. Configura las variables de entorno
3. Deploy automático



### DigitalOcean App Platform
1. Conecta tu repositorio
2. Selecciona Dockerfile como método de build
3. Configura variables de entorno
4. Deploy

## 🔧 Desarrollo local

**Con Docker:**
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

**Sin Docker:**
```bash
python -m venv venv
venv\Scripts\activate  # En Windows
# source venv/bin/activate  # En Linux/Mac
pip install -r requirements.txt
python run.py
```

## 📝 Variables de entorno requeridas

- `GOOGLE_CLIENT_ID`: ID del cliente de Google OAuth
- `GOOGLE_CLIENT_SECRET`: Secret del cliente de Google OAuth
- `SECRET_KEY`: Clave secreta de Flask
- `FLASK_ENV`: Entorno de Flask (development/production)

## 🗄️ Base de datos

Por defecto usa SQLite. La base de datos se almacena en `instance/tu_base_de_datos.db` y se persiste usando volúmenes de Docker.

## 🏗️ Estructura del proyecto

```
Resort_encanto/
├── run.py                 # Punto de entrada
├── config.py             # Configuración
├── requirements.txt      # Dependencias
├── Dockerfile           # Imagen Docker
├── docker-compose.yml   # Orquestación
├── gunicorn.conf.py     # Configuración Gunicorn
├── models/              # Modelos de base de datos
├── routes/              # Rutas de la aplicación
├── templates/           # Plantillas HTML
├── static/              # Archivos estáticos
└── utils/               # Utilidades
```
