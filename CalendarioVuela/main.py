from flask import Flask, render_template, request, redirect, url_for,flash, jsonify
import sqlite3
from datetime import datetime, timedelta 
import base64
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

app = Flask(__name__)
app.config['DATABASE'] = 'clientes.db'
app.secret_key = 'your_secret_key'
def get_db_connection():
    connection = sqlite3.connect(app.config['DATABASE'])
    connection.row_factory = sqlite3.Row
    return connection

def init_db():
    with app.app_context():
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fechas (
                id INTEGER PRIMARY KEY,
                fecha TEXT,
                status TEXT,
                nombre_mes TEXT,
                nombre_dia TEXT,
                horario DATE,
                cantidad INTEGER,
                descripcion TEXT
            )
        ''')
        
        cursor.execute('''
    CREATE TABLE IF NOT EXISTS fecha_mapping (
        fecha_id INTEGER PRIMARY KEY,
        fecha_nombre TEXT UNIQUE
    )
''')
        cursor.execute('''
    CREATE TABLE IF NOT EXISTS horarios (
        id INTEGER PRIMARY KEY,
        fecha_id INTEGER,
        
        horario TIME,
        capacidad INTEGER,
        FOREIGN KEY(fecha_id) REFERENCES fechas(id)
    )
''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY,
                fecha_id INTEGER,
                fecha_nombre TEXT,
                horario DATE,
                nombre TEXT,
                cantidad INT,
                telefono TEXT,
                status TEXT,
                
                FOREIGN KEY(fecha_id) REFERENCES fechas(id)
            )
        ''')
        # Crear la tabla si no existe
        cursor.execute('''CREATE TABLE IF NOT EXISTS descripcion (
                            id INTEGER PRIMARY KEY,
                            texto TEXT
                        )''')
        db.commit()
        db.close()


# Configuración del servidor SMTP de Zoho
SERVIDOR_CORREO = 'smtp.zoho.com'
PUERTO = 587
USUARIO = 'vuela@wabo.com.ar'  # Cambia esto a tu dirección de correo
CONTRASEÑA = 'test1234@A'  # Cambia esto a tu contraseña real







@app.route('/enviar_correo', methods=['POST'])
def enviar_correo():
    try:
        # Obtén los datos del formulario enviado desde el frontend
        datos = request.get_json()
        
        destinatario = datos.get('to')  # Cambiado a 'to' para que coincida con el JSON
        asunto = datos.get('asunto')
        mensaje = datos.get('mensaje')

        # Crea el objeto MIME para el correo electrónico
        msg = MIMEMultipart()
        msg['From'] = USUARIO
        msg['To'] = destinatario
        msg['Subject'] = asunto

        # Agrega el cuerpo del mensaje
        msg.attach(MIMEText(mensaje, 'html'))

        # Inicia una conexión segura con el servidor SMTP de Zoho
        with smtplib.SMTP(SERVIDOR_CORREO, PUERTO) as servidor:
            servidor.starttls()
            servidor.login(USUARIO, CONTRASEÑA)
            texto = msg.as_string()
            
            # Envía el correo electrónico
            servidor.sendmail(USUARIO, destinatario, texto)

        # Cierra la conexión
        print("Correo enviado con éxito a", destinatario)

        return jsonify({'mensaje': 'Correo enviado con éxito'})
    except Exception as e:
        error_msg = str(e)
        print("Error al enviar el correo:", error_msg)
        return jsonify({'error': error_msg}), 500


@app.route('/enviar_correo_con_imagen', methods=['POST'])
def enviar_correo_con_imagen():
    try:
        # Obtén los datos del formulario enviado desde el frontend
        datos = request.get_json()
        
        destinatario = datos.get('to')  # Cambiado a 'to' para que coincida con el JSON
        asunto = datos.get('asunto')
        mensaje = datos.get('mensaje')
        imagen_base64 = datos.get('imagen')  # Obtiene la imagen en base64

        # Crea el objeto MIME para el correo electrónico
        msg = MIMEMultipart()
        msg['From'] = USUARIO
        msg['To'] = destinatario
        msg['Subject'] = asunto

        # Agrega el cuerpo del mensaje
        msg.attach(MIMEText(mensaje, 'html'))

        # Decodifica la imagen base64 y adjúntala al correo
        image_data = base64.b64decode(imagen_base64)
        image_attachment = MIMEImage(image_data, name='comprobante.png')
        msg.attach(image_attachment)

        # Inicia una conexión segura con el servidor SMTP de Zoho
        with smtplib.SMTP(SERVIDOR_CORREO, PUERTO) as servidor:
            servidor.starttls()
            servidor.login(USUARIO, CONTRASEÑA)
            texto = msg.as_string()
            
            # Envía el correo electrónico
            servidor.sendmail(USUARIO, destinatario, texto)

        # Cierra la conexión
        print("Correo enviado con éxito a", destinatario)

        return jsonify({'mensaje': 'Correo enviado con éxito'})
    except Exception as e:
        error_msg = str(e)
        print("Error al enviar el correo:", error_msg)
        return jsonify({'error': error_msg}), 500



        
@app.route('/ver_tabla/<int:date_id>/<fecha_nombre>')
def ver_tabla(date_id,fecha_nombre):
    # Lógica para mostrar la tabla de clientes de la fecha con ID 'date_id'
    
    return render_template('tabla.html',  date_id=date_id,fecha_nombre=fecha_nombre)

def get_existing_dates():
    with app.app_context():
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("""
    SELECT fechas.*, 
           SUM(CASE WHEN clientes.cantidad <> 10 THEN clientes.cantidad ELSE 0 END) AS total_cantidad, 
           strftime('%Y-%m-%d', fechas.fecha) AS fecha_orden 
    FROM fechas 
    LEFT JOIN clientes ON fechas.id = clientes.fecha_id 
    GROUP BY fechas.id
""")
        rows = cursor.fetchall()
        db.close()

        # Create a list of dictionaries with the data calculated
        dates = []
        for row in rows:
            date_data = dict(row)
            date_data['total_cantidad'] = row['total_cantidad'] or 0  # Set to 0 if None
            date_data['disponibles'] = 96 - date_data['total_cantidad']
            dates.append(date_data)

        return dates




def obtener_fecha_id_del_cliente(cliente_id):
    with app.app_context():
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT fecha_id FROM clientes WHERE id = ?", (cliente_id,))
        fecha_id = cursor.fetchone()
        db.close()
        if fecha_id:
            return fecha_id['fecha_id']
        return None  # En caso de que no se encuentre la fecha correspondiente

def obtener_cliente_por_id(cliente_id):
    with app.app_context():
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,))
        cliente = cursor.fetchone()
        db.close()
        return cliente
    

@app.route('/editar_cliente/<int:cliente_id>', methods=['GET', 'POST'])
def editar_cliente(cliente_id):
    if request.method == 'POST':
        horario = request.form['horario']
        nombre = request.form['nombre']
        cantidad = request.form['cantidad']
        telefono = request.form['telefono']
        status = request.form['status']

        with app.app_context():
            db = get_db_connection()
            db.execute('UPDATE clientes SET horario=?, nombre=?, cantidad=?, telefono=?, status=? WHERE id=?',
                       (horario, nombre, cantidad, telefono, status, cliente_id))
            db.commit()
            db.close()

        fecha_id = obtener_fecha_id_del_cliente(cliente_id)
        fecha_nombre = get_fecha_nombre(fecha_id)
        flash('Cliente editado exitosamente', 'success')
        
        # Redirigir al usuario a la página de éxito y pasar los datos del cliente y la fecha
        cliente = {
            'horario': horario,
            'nombre': nombre,
            'cantidad': cantidad,
            'telefono': telefono,
            'status': status
        }
        return render_template('exito.html', cliente=cliente, fecha_nombre=fecha_nombre)

    cliente = obtener_cliente_por_id(cliente_id)
    return render_template('editar_cliente.html', cliente=cliente)
# Nueva función para editar solo el estado del cliente
@app.route('/editar_status_cliente/<int:cliente_id>', methods=['POST'])
def editar_status_cliente(cliente_id):
    if request.method == 'POST':
        status = request.form['status']

        with app.app_context():
            db = get_db_connection()
            db.execute('UPDATE clientes SET status=? WHERE id=?', (status, cliente_id))
            db.commit()
            db.close()

        flash('Estado del cliente editado exitosamente', 'success')
        return redirect(url_for('view_date', date_id=obtener_fecha_id_del_cliente(cliente_id), fecha_nombre="nombre_de_la_fecha"))




    cliente = obtener_cliente_por_id(cliente_id)
    return render_template('editar_cliente.html', cliente=cliente)

# ...

@app.route('/eliminar_fecha/<int:date_id>', methods=['POST'])
def eliminar_fecha(date_id):
    with app.app_context():
        db = get_db_connection()
        
        # Eliminar la fecha de la tabla 'fechas'
        db.execute('DELETE FROM fechas WHERE id = ?', (date_id,))
        db.commit()
        
        # Eliminar la entrada correspondiente en la tabla 'fecha_mapping'
        db.execute('DELETE FROM fecha_mapping WHERE fecha_id = ?', (date_id,))
        db.commit()
        
        db.close()

    flash('Fecha eliminada exitosamente', 'success')
    return redirect(url_for('index'))


def get_fecha_nombre(date_id):
    with app.app_context():
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT fecha FROM fechas WHERE id = ?", (date_id,))
        fecha = cursor.fetchone()
        db.close()
        if fecha:
            return fecha['fecha']
        return None  # En caso de que no se encuentre la fecha correspondiente


def get_clients_by_date(date_id):
    with app.app_context():
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM clientes WHERE fecha_id = ?", (date_id,))
        clients = cursor.fetchall()
        db.close()
        return clients

@app.route('/ver_horarios/<int:fecha_id>', methods=['GET'])
def ver_horarios(fecha_id):
    with app.app_context():
        db = get_db_connection()
        cursor = db.cursor()
        
        # Obtén la fecha correspondiente a partir de su ID
        cursor.execute('SELECT fecha FROM fechas WHERE id = ?', (fecha_id,))
        fecha = cursor.fetchone()
        
        # Obtén los horarios para la fecha específica
        cursor.execute('SELECT horario, capacidad FROM horarios WHERE fecha_id = ?', (fecha_id,))
        horarios = cursor.fetchall()
        
        db.close()

    return render_template('tabla_horarios.html', fecha=fecha, horarios=horarios)

@app.route('/')
def index():
    dates = get_existing_dates()
    print("Registros de fechas:", dates)  # Agrega esta línea para depuración
    return render_template('index.html', dates=dates)
def get_formatted_fecha(date_id):
    with app.app_context():
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT fecha FROM fechas WHERE id = ?", (date_id,))
        fecha_data = cursor.fetchone()
        db.close()
        if fecha_data:
            fecha_str = fecha_data['fecha']
            nombre_mes, nombre_dia = convertir_fecha(fecha_str)
            if nombre_mes and nombre_dia:
                fecha_formateada = f"{nombre_dia} {fecha_str[-2:]} DE {nombre_mes} {fecha_str[:4]}"
                return fecha_formateada
        return None  # En caso de que no se encuentre la fecha correspondiente


@app.route('/fecha/<int:date_id>', methods=['GET', 'POST'])
def view_date(date_id):
    fecha_nombre = get_fecha_nombre(date_id)  # Obtener el nombre de la fecha desde la base de datos
    fecha_formateada = get_formatted_fecha(date_id)
    if request.method == 'POST':
        horario = request.form['horario']
        nombre = request.form['nombre']
        cantidad = request.form['cantidad']
        telefono = request.form['telefono']
        status = request.form['status']

        with app.app_context():
            db = get_db_connection()
            db.execute('INSERT INTO clientes (fecha_id, horario, nombre, cantidad, telefono, status) VALUES (?, ?, ?, ?, ?, ?)',
                       (date_id, horario, nombre, cantidad, telefono, status))
            db.commit()
            db.close()

            # Mostrar mensaje de éxito
            flash('Cliente agregado exitosamente', 'success')

        # Redirigir al usuario a la página de la tabla después de agregar un cliente
        return redirect(url_for('ver_tabla', date_id=date_id, fecha_nombre=fecha_nombre))

    # Agrega mensajes de depuración para verificar si los clientes se están recuperando correctamente
    clients = get_clients_by_date(date_id)
    print("Clientes recuperados:", clients)

    return render_template('tabla.html', clients=clients, date_id=date_id, fecha_nombre=fecha_nombre,fecha_formateada=fecha_formateada)





def convertir_fecha(fecha_str):
    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
        # Diccionario de nombres de meses en español en mayúsculas
        meses_espanol = {
            1: 'ENERO', 2: 'FEBRERO', 3: 'MARZO', 4: 'ABRIL', 5: 'MAYO',
            6: 'JUNIO', 7: 'JULIO', 8: 'AGOSTO', 9: 'SEPTIEMBRE', 10: 'OCTUBRE',
            11: 'NOVIEMBRE', 12: 'DICIEMBRE'
        }
        nombre_mes = meses_espanol[fecha.month].upper()

        # Diccionario de nombres de días en español en mayúsculas
        dias_espanol = {
            0: 'LUNES', 1: 'MARTES', 2: 'MIÉRCOLES', 3: 'JUEVES', 4: 'VIERNES',
            5: 'SÁBADO', 6: 'DOMINGO'
        }
        nombre_dia = dias_espanol[fecha.weekday()].upper()

        return nombre_mes, nombre_dia
    except ValueError:
        return None, None  # En caso de que la fecha no sea válida




























# Función para generar los horarios desde las 10:30 hasta las 18:00 en intervalos de 30 minutos
def generar_horarios():
    horarios = []
    hora_inicio = datetime.strptime("10:30", "%H:%M")
    hora_fin = datetime.strptime("18:00", "%H:%M")
    intervalo = timedelta(minutes=30)

    while hora_inicio <= hora_fin:
        horarios.append(hora_inicio.strftime("%H:%M"))
        hora_inicio += intervalo

    return horarios
# Ruta para crear una fecha con horarios predefinidos
@app.route('/crear_fecha', methods=['POST'])
def crear_fecha():
    fecha = request.form['fecha']
    status = "Abierto"
    nombre_mes, nombre_dia = convertir_fecha(fecha)  # Convierte la fecha

    if nombre_mes and nombre_dia:
        with app.app_context():
            db = get_db_connection()
            cursor = db.cursor()
            cursor.execute('INSERT INTO fechas (fecha, status, nombre_mes, nombre_dia) VALUES (?, ?, ?, ?)',
                           (fecha, status, nombre_mes, nombre_dia))
            db.commit()

            # Obtener el ID de la fecha recién insertada
            fecha_id = cursor.lastrowid

            # Genera los horarios predefinidos (10:30, 11:00, 11:30, ...) y sus capacidades
            horarios = ["10:30", "11:00", "11:30", "12:00", "12:30", "13:00", "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30", "17:00", "17:30", "18:00"]
            capacidad = 7  # Capacidad máxima para cada horario

            for horario in horarios:
                cursor.execute('INSERT INTO horarios (fecha_id, horario, capacidad) VALUES (?, ?, ?)',
                               (fecha_id, horario, capacidad))
                db.commit()

            # Guardar la relación en la tabla fecha_mapping
            cursor.execute('INSERT INTO fecha_mapping (fecha_id, fecha_nombre) VALUES (?, ?)',
                           (fecha_id, fecha))
            db.commit()

            db.close()

    return redirect(url_for('index'))



def row_to_dict(row):
    return dict(row)

# Ruta para obtener todas las fechas
@app.route('/api/fechas', methods=['GET'])
def get_fechas():
    dates = get_existing_dates()
    return jsonify(dates)

# Ruta para obtener todos los clientes
@app.route('/api/clientes', methods=['GET'])
def get_clientes():
    with app.app_context():
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM clientes")
        rows = cursor.fetchall()
        db.close()
        # Convierte los objetos Row en diccionarios
        clientes = [row_to_dict(row) for row in rows]
        return jsonify(clientes)



# Ruta para obtener la suma de la cantidad en una fecha específica
@app.route('/api/clientes/suma_cantidad/<fecha>', methods=['GET'])
def get_suma_cantidad_por_fecha(fecha):
    with app.app_context():
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT SUM(clientes.cantidad) FROM clientes JOIN fechas ON clientes.fecha_id = fechas.id WHERE fechas.fecha = ?", (fecha,))
        suma_cantidad = cursor.fetchone()[0]
        db.close()
        return jsonify({"suma_cantidad": suma_cantidad})
    


# Ruta para obtener las fechas "Abierto"
@app.route('/fechas_abiertas', methods=['GET'])
def get_fechas_abiertas():
    with app.app_context():
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT fecha FROM fechas WHERE status = 'Abierto'")
        fechas_abiertas = cursor.fetchall()
        db.close()
        # Extraer las fechas del resultado
        fechas_abiertas = [fecha['fecha'] for fecha in fechas_abiertas]
        return jsonify(fechas_abiertas)


# Ruta para obtener la resta de 7 menos la suma de la cantidad en una fecha y horario específicos
@app.route('/api/clientes/resta_cantidad/<fecha>', methods=['GET'])
def get_resta_cantidad_por_fecha(fecha):
    with app.app_context():
        db = get_db_connection()
        cursor = db.cursor()
        
        # Lista de horarios desde 10:30 hasta 18:00
        horarios = ["10:30", "11:00", "11:30", "12:00", "12:30", "13:00", "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30", "17:00", "17:30", "18:00"]
        
        # Diccionario para almacenar los resultados
        resta_cantidad_por_horario = {}
        
        for horario in horarios:
            cursor.execute("""
                SELECT fecha_nombre, 6 - SUM(cantidad) as resta_cantidad
                FROM clientes
                WHERE horario = ? AND fecha_id IN (SELECT id FROM fechas WHERE fecha = ?)
                GROUP BY fecha_nombre
            """, (horario, fecha,))
            
            result = cursor.fetchall()
            
            if result:
                # Si se encontraron resultados, agregarlos al diccionario
                resta_cantidad_por_horario[horario] = {row[0]: row[1] for row in result}
            else:
                # Si no se encontraron resultados, indicar que está disponible
                resta_cantidad_por_horario[horario] = {'Disponible': 6}
        
        db.close()

        return jsonify(resta_cantidad_por_horario)
# Ruta para obtener los horarios libres en una fecha específica
@app.route('/api/clientes/horarios_libres/<fecha>', methods=['GET'])
def get_horarios_libres(fecha):
    with app.app_context():
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("""
            SELECT horarios.horario
            FROM horarios
            LEFT JOIN (
                SELECT fecha_id, horario, SUM(cantidad) as cantidad_total
                FROM clientes
                WHERE fecha_id = (SELECT id FROM fechas WHERE fecha = ?)
                GROUP BY fecha_id, horario
            ) as c ON horarios.fecha_id = c.fecha_id AND horarios.horario = c.horario
            WHERE horarios.fecha_id = (SELECT id FROM fechas WHERE fecha = ?) AND (c.cantidad_total IS NULL OR c.cantidad_total < ?)
        """, (fecha, fecha, 7,))
        
        result = cursor.fetchall()
        db.close()

        # Construir una lista de horarios libres
        horarios_libres = [row[0] for row in result]

        return jsonify(horarios_libres)

# Ruta para obtener los horarios libres en una fecha específica con cantidad personalizada
@app.route('/api/clientes/horarios_libres/<fecha>/<int:cantidad>', methods=['GET'])
def get_horarios_libres_con_cantidad(fecha, cantidad):
    with app.app_context():
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("""
            SELECT horarios.horario
            FROM horarios
            LEFT JOIN (
                SELECT fecha_id, horario, SUM(cantidad) as cantidad_total
                FROM clientes
                WHERE fecha_id = (SELECT id FROM fechas WHERE fecha = ?)
                GROUP BY fecha_id, horario
            ) as c ON horarios.fecha_id = c.fecha_id AND horarios.horario = c.horario
            WHERE horarios.fecha_id = (SELECT id FROM fechas WHERE fecha = ?) AND (c.cantidad_total IS NULL OR c.cantidad_total < ?)
        """, (fecha, fecha, cantidad,))
        
        result = cursor.fetchall()
        db.close()

        # Construir una lista de horarios libres
        horarios_libres = [row[0] for row in result]

        return jsonify(horarios_libres)


# Ruta para el formulario HTML de consulta de horarios
@app.route('/consultar_horarios', methods=['GET'])
def consultar_horarios():
    return render_template('formulario_consulta.html')  # Reemplaza 'formulario_consulta.html' con el nombre de tu archivo HTML


@app.route('/formulario_consulta_datos')
def confirma_datos_reserva():
    # Lógica para mostrar la tabla de clientes de la fecha con ID 'date_id'
    
    return render_template('formulario_consulta_datos.html')

@app.route('/reserva_exitosa')
def reserva_exitosa():
    # Lógica para mostrar la tabla de clientes de la fecha con ID 'date_id'
    
    return render_template('reserva_exitosa.html')



@app.route('/crear_cliente', methods=['POST'])
def crear_cliente_api():
    data = request.get_json()

    # Verificar que se proporcionen todos los campos necesarios
    if 'horario' not in data or 'nombre' not in data or 'cantidad' not in data or 'telefono' not in data or 'status' not in data or 'fecha_nombre' not in data:
        return jsonify({'error': f'Todos los campos son obligatorios, {data}'}), 400  # Aquí incluimos {data} en el mensaje de error

    # Obtener los datos del cliente desde la solicitud JSON
    horario = data['horario']
    nombre = data['nombre']
    cantidad = data['cantidad']
    telefono = data['telefono']
    status = data['status']
    fecha_nombre = data['fecha_nombre']

    try:
        db = get_db_connection()
        cursor = db.cursor()

        # Obtener fecha_id basado en fecha_nombre
        cursor.execute('SELECT fecha_id FROM fecha_mapping WHERE fecha_nombre = ?', (fecha_nombre,))
        result = cursor.fetchone()
        if result:
            fecha_id = result[0]
        else:
            return jsonify({'error': 'Fecha no encontrada'}), 404

        # Insertar el cliente en la tabla clientes
        cursor.execute('''
            INSERT INTO clientes (fecha_id, fecha_nombre, horario, nombre, cantidad, telefono, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (fecha_id, fecha_nombre, horario, nombre, cantidad, telefono, status))
        db.commit()
        db.close()
        return jsonify({'message': 'Cliente creado con éxito'}), 201
    except sqlite3.Error as e:
        return jsonify({'error': 'Error al crear el cliente en la base de datos'}), 500


@app.route('/crear_cliente/<int:date_id>', methods=['GET', 'POST'])
def crear_cliente(date_id):
    if request.method == 'POST':
        horario = request.form['horario']
        nombre = request.form['nombre']
        cantidad = request.form['cantidad']
        telefono = request.form['telefono']
        status = request.form['status']
        
        print(f'Insertando cliente: date_id={date_id}, horario={horario}, nombre={nombre}, cantidad={cantidad}, telefono={telefono}, status={status}')

        # Obtener la fecha_nombre correspondiente al date_id
        fecha_nombre = get_fecha_nombre(date_id)

        db = get_db_connection()
        db.execute('INSERT INTO clientes (fecha_id, fecha_nombre, horario, nombre, cantidad, telefono, status) VALUES (?, ?, ?, ?, ?, ?, ?)',
                   (date_id, fecha_nombre, horario, nombre, cantidad, telefono, status))
        db.commit()
        db.close()

        print('Cliente insertado correctamente.')

        # Guardar los datos del cliente en un diccionario
        cliente = {
            'horario': horario,
            'nombre': nombre,
            'cantidad': cantidad,
            'telefono': telefono,
            'status': status
        }

        # Redirigir al usuario a la página de éxito y pasar los datos del cliente
        return render_template('exito.html', cliente=cliente, fecha_nombre=fecha_nombre)

    return render_template('crear_cliente.html', date_id=date_id)

def get_notas(date_id):
    with app.app_context():
        db = get_db_connection()
        cursor = db.execute('SELECT notas FROM fechas WHERE id=?', (date_id,))
        notas = cursor.fetchone()
        db.close()

        return notas[0] if notas else ""


@app.route('/editar_fecha/<int:date_id>', methods=['GET', 'POST'])
def editar_fecha(date_id):
    if request.method == 'POST':
        
        status = request.form['status']
          # Obtener las notas del formulario

        with app.app_context():
            db = get_db_connection()
            db.execute('UPDATE fechas SET status=? WHERE id=?',
                       (status, date_id))
            db.commit()
            db.close()

        flash('Fecha editada exitosamente', 'success')
        return redirect(url_for('index'))

    # Obtén la fecha y las notas actuales para mostrarlas en el formulario de edición
    fecha = get_fecha_nombre(date_id)
      # Debes crear una función para obtener las notas desde la base de datos

    return render_template('editar_fecha.html', date_id=date_id, fecha=fecha)



    
if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=8001)
