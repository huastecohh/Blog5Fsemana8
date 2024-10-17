import firebase_admin
from flask import Flask, redirect, render_template, request, url_for
from firebase_admin import credentials, firestore
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from werkzeug.utils import secure_filename
from firebase_admin import storage

# Configurar Flask
app = Flask(__name__)

# Configurar la carpeta para almacenar los archivos
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Función para verificar la extensión de un archivo
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Inicializar Firebase
cred = credentials.Certificate('c:/credencial/prueba-556fc-firebase-adminsdk-nmfeq-77ba6f19b7.json')
firebase_admin.initialize_app(cred, {
    'storageBucket': 'prueba-556fc.appspot.com'  # Especifica el nombre de tu bucket
})

# Inicializar almacenamiento base de datos
db = firestore.client()

# Modelo de blog
class BlogPost:
    def __init__(self, title, content, author, created_at):
        self.title = title
        self.content = content
        self.author = author
        self.created_at = created_at

    def to_dict(self):
        return {
            'title': self.title,
            'content': self.content,
            'author': self.author,
            'created_at': self.created_at
        }

# Ruta principal para ver los blogs y el contenedor de nuevo blog
@app.route("/")
def index():
    posts_ref = db.collection('blog_posts')
    posts = posts_ref.stream()  # Obtener todos los documentos de la colección
    posts_list = []
    for post in posts:
        posts_list.append(post.to_dict())  # Convertir cada post a diccionario
    return render_template("index.html", posts=posts_list)

# Ruta para crear un nuevo blog
@app.route("/new_blog", methods=["GET", "POST"])
def new_blog():
    if request.method == "POST":
        title = request.form['title']
        content = request.form['content']
        author = request.form['author']
        image_file = request.files['image']
        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)

            # Subir la imagen a Firebase Storage
            blob = storage.bucket().blob(f'blog_images/{filename}')
            blob.upload_from_file(image_file)

            # Hacer la imagen accesible públicamente
            blob.make_public()

            # Obtener URL pública de la imagen
            image_url = blob.public_url

            # Guardar los datos del blog y la imagen en Firebase Firestore
            blog_data = {
                'title': title,
                'content': content,
                'author': author,
                'image_url': image_url,
                'created_at': datetime.utcnow()
            }
            db.collection('blog_posts').add(blog_data)

            return redirect(url_for('index'))

    return render_template("new_blog.html")

# Ruta para ver blogs cargados previamente
@app.route('/blogs')
def blogs():
    posts_ref = db.collection('blog_posts')
    posts = posts_ref.stream()
    posts_list = []
    for post in posts:
        posts_list.append(post.to_dict())
    return render_template('blogs.html', posts=posts_list)

# Ruta para enviar un blog por correo electrónico
@app.route('/send_blog', methods=['POST'])
def send_blog():
    post_id = request.form['post_id']
    post_ref = db.collection('blog_posts').document(post_id)
    post = post_ref.get()
    if post.exists:
        post_data = post.to_dict()
        send_email(post_data['title'], post_data['content'])
        return 'Blog enviado con exito!'
    else:
        return 'Blog no encontrado!'

# Función para enviar correo electrónico
def send_email(subject, message):
    # Configuración del servidor de correo electrónico
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login('tu_correo_electronico', 'tu_contrasenia')
    
    # Crear mensaje de correo electrónico
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = 'tu_correo_electronico'
    msg['To'] = 'destinatario_correo_electronico'
    msg.attach(MIMEText(message, 'plain'))

    # Enviar correo electrónico
    server.sendmail('tu_correo_electronico', 'destinatario_correo_electronico', msg.as_string())
    server.quit()




if __name__ == '__main__':
    import os
    HOST = os.environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(os.environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555
    app.run(HOST, PORT)
