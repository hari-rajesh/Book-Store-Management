from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'

# Function to connect to the SQLite database
def connect_db():
    conn = sqlite3.connect('bookstore.db')
    return conn

# Initialize the database
def init_db():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS books
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         name TEXT,
                         author TEXT,
                         price REAL,
                         no_of_stocks INTEGER)''')  # Added no_of_stocks field
    # Rest of the code for other tables...
    cursor.execute('''CREATE TABLE IF NOT EXISTS customers
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    email TEXT,
                   password TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS purchases
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER,
                    book_id INTEGER,
                    quantity INTEGER,
                    FOREIGN KEY (customer_id) REFERENCES customers(id),
                    FOREIGN KEY (book_id) REFERENCES books(id))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS owners
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    email TEXT)''')

@app.route('/')
def index():
    # conn = connect_db()
    # cursor = conn.cursor()
    # cursor.execute("SELECT * FROM books")
    # books = cursor.fetchall()
    # conn.close()
    return render_template('login.html')
@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/owner')    
def owner():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()
    return render_template('owner.html', books = books)

@app.route('/customer')
def customer():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()
    return render_template('customer.html', books=books)

@app.route('/login', methods=['POST'])
def login():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()
    username = request.form['username'] 
    password = request.form['password']
    cursor.execute("SELECT * FROM customers WHERE name = ?", (username,))
    if username == 'owner' and password == 'password':
        return render_template('owner.html')
    user = cursor.fetchone()
    if user:
        # Assuming password_hash is stored as a hashed value in the database
        hh_pass = user[3]

        if password == hh_pass: 
            return render_template('customer.html', books=books)  # Credentials match
        else:
            return "Incorrect Password"  # Incorrect password
    else:
        return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    conn = connect_db()
    cursor = conn.cursor()
    if password == confirm_password:
        cursor.execute("INSERT INTO customers (name, email, password) VALUES (?, ?, ? )",
                   (username, email, password))
        conn.commit()
        conn.close()
    return render_template('login.html')

@app.route('/add_book', methods=['POST'])
def add_book():
    title = request.form['title']
    author = request.form['author']
    price = request.form['price']
    no_of_stocks = int(request.form['no_of_stocks'])  # Convert input to integer
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()
    cursor.execute("INSERT INTO books (name, author, price, no_of_stocks) VALUES (?, ?, ?, ?)",
                   (title, author, price, no_of_stocks))  # Include no_of_stocks in the query
    conn.commit()
    conn.close()
    
    return redirect(url_for('owner'))


@app.route('/update_book', methods=['POST'])
def update_book():
    title = request.form['title']
    price = request.form['price']
    no_of_stocks = int(request.form['no_of_stocks'])  # Convert input to integer
    conn = connect_db()
    cursor1 = conn.cursor()
    cursor2 = conn.cursor()
    cursor2.execute("SELECT * FROM books WHERE name=?",(title, ))
    req_book = cursor2.fetchone()
    iid = req_book[0]
    books = cursor1.fetchall()
    cursor2.execute("UPDATE books set price=?, no_of_stocks=? WHERE id = ?",
                   (price, no_of_stocks, iid))  # Include no_of_stocks in the query
    conn.commit()
    conn.close()
    
    return redirect(url_for('owner'), books = books)

@app.route('/delete_book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM books WHERE id=?", (book_id,))
    conn.commit()
    return redirect(url_for('owner'))

@app.route('/purchase_book', methods=['POST'])
def purchase_book():
    name = request.form['name']
    email = request.form['email']
    book_id = request.form['book_id']
    quantity = int(request.form['quantity'])

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()

    try:
        # Check if the requested quantity is available in stock
        cursor.execute("SELECT no_of_stocks FROM books WHERE id=?", (book_id,))
        current_stock = cursor.fetchone()[0]
        if quantity > current_stock:
            raise Exception('Not enough stock available!')

        # Reduce the stock in the books table
        new_stock = current_stock - quantity
        if new_stock == 0:
            cursor.execute("DELETE FROM books WHERE id=?", (book_id,))
        else:
            cursor.execute("UPDATE books SET no_of_stocks=? WHERE id=?", (new_stock, book_id))

        # Insert the purchase record
        cursor.execute("INSERT INTO customers (name, email) VALUES (?, ?)", (name, email))
        customer_id = cursor.lastrowid
        cursor.execute("INSERT INTO purchases (customer_id, book_id, quantity) VALUES (?, ?, ?)", (customer_id, book_id, quantity))

        conn.commit()
        flash('Purchase successful!')
    except Exception as e:
        conn.rollback()
        flash(str(e))
    finally:
        conn.close()

    return redirect(url_for('customer'))



if __name__ == '__main__':
    init_db()
    app.run(debug=True)
