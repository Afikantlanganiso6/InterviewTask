from flask import Flask, render_template, request, redirect, url_for, flash, g
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flash messages

DATABASE = 'users.db'

# Connect to DB
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # to access columns by name
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Initialize DB with schema.sql
def init_db():
    with app.app_context():
        db = get_db()
        with open('schema.sql', 'r') as f:
            db.executescript(f.read())
        db.commit()

# Home page - list users
@app.route('/')
def index():
    db = get_db()
    users = db.execute('SELECT * FROM users').fetchall()
    return render_template('index.html', users=users)

# Create user form
@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']

        if not name or not email:
            flash('Name and Email are required!', 'error')
            return redirect(url_for('create'))

        db = get_db()
        try:
            db.execute('INSERT INTO users (name, email) VALUES (?, ?)', (name, email))
            db.commit()
            flash('User created successfully!', 'success')
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            flash('Email must be unique!', 'error')
            return redirect(url_for('create'))

    return render_template('create.html')


# Edit user form
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (id,)).fetchone()
    if user is None:
        flash('User not found!')
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']

        if not name or not email:
            flash('Name and Email are required!')
            return redirect(url_for('edit', id=id))

        try:
            db.execute('UPDATE users SET name = ?, email = ? WHERE id = ?', (name, email, id))
            db.commit()
            flash('User updated successfully!')
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            flash('Email must be unique!')
            return redirect(url_for('edit', id=id))

    return render_template('edit.html', user=user)

# Delete user
@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    db = get_db()
    db.execute('DELETE FROM users WHERE id = ?', (id,))
    db.commit()
    flash('User deleted successfully!')
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()  # create DB if not exists
    app.run(debug=True)
