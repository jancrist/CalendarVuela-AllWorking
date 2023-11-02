from flask import Flask, render_template, request, redirect, url_for,flash
import sqlite3

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
                fecha TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY,
                fecha_id INTEGER,
                horario TEXT,
                nombre TEXT,
                cantidad TEXT,
                telefono TEXT,
                status TEXT,
                FOREIGN KEY(fecha_id) REFERENCES fechas(id)
            )
        ''')
        db.commit()
        db.close()
@app.route('/ver_tabla/<int:date_id>/<fecha_nombre>')
def ver_tabla(date_id,fecha_nombre):
    # Lógica para mostrar la tabla de clientes de la fecha con ID 'date_id'
    return render_template('tabla.html', date_id=date_id,fecha_nombre=fecha_nombre)
def get_existing_dates():
    with app.app_context():
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM fechas")
        dates = cursor.fetchall()
        db.close()
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


@app.route('/')
def index():
    dates = get_existing_dates()
    return render_template('index.html', dates=dates)



@app.route('/fecha/<int:date_id>', methods=['GET', 'POST'])
def view_date(date_id):
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
            fecha_nombre = get_fecha_nombre(date_id)
            # Mostrar mensaje de éxito
            flash('Cliente agregado exitosamente', 'success')

        # Redirigir al usuario a la página de la tabla después de agregar un cliente
        return redirect(url_for('ver_tabla', date_id=date_id,fecha_nombre=fecha_nombre))

    # Agrega mensajes de depuración para verificar si los clientes se están recuperando correctamente
    clients = get_clients_by_date(date_id)
    print("Clientes recuperados:", clients)

    return render_template('tabla.html', clients=clients, date_id=date_id)


@app.route('/crear_fecha', methods=['POST'])
def crear_fecha():
    fecha = request.form['fecha']

    with app.app_context():
        db = get_db_connection()
        db.execute('INSERT INTO fechas (fecha) VALUES (?)', (fecha,))
        db.commit()
        db.close()

    return redirect(url_for('index'))
@app.route('/crear_cliente/<int:date_id>', methods=['GET', 'POST'])
def crear_cliente(date_id):
    if request.method == 'POST':
        horario = request.form['horario']
        nombre = request.form['nombre']
        cantidad = request.form['cantidad']
        telefono = request.form['telefono']
        status = request.form['status']
        
        print(f'Insertando cliente: date_id={date_id}, horario={horario}, nombre={nombre}, cantidad={cantidad}, telefono={telefono}, status={status}')

        db = get_db_connection()
        db.execute('INSERT INTO clientes (fecha_id, horario, nombre, cantidad, telefono, status) VALUES (?, ?, ?, ?, ?, ?)',
                   (date_id, horario, nombre, cantidad, telefono, status))
        db.commit()
        db.close()

        print('Cliente insertado correctamente.')
        fecha_nombre = get_fecha_nombre(date_id)
        # Guardar los datos del cliente en un diccionario
        cliente = {
            'horario': horario,
            'nombre': nombre,
            'cantidad': cantidad,
            'telefono': telefono,
            'status': status
        }

        # Redirigir al usuario a la página de éxito y pasar los datos del cliente
        return render_template('exito.html', cliente=cliente,fecha_nombre=fecha_nombre)

    return render_template('crear_cliente.html', date_id=date_id)


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
