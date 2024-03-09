from flask import Flask, request, jsonify
import psycopg2
import psycopg2.extras

app = Flask(__name__)

# Параметры подключения к базе данных
DATABASE_URL = "postgres://postgresUser:postgresPW@localhost:5455/postgresDB"

# Подключение к базе данных
def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

# ---PRODUCTS---
@app.route('/products', methods=['POST'])
def create_product():
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("INSERT INTO Products (Name, Description, Price, Quantity) VALUES (%s, %s, %s, %s) RETURNING *;",
                (data['name'], data['description'], data['price'], data['quantity']))
    new_product = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return jsonify(new_product), 201


@app.route('/products/<int:productId>', methods=['GET'])
def get_product(productId):
    try:
        # Установление соединения с базой данных
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Выполнение запроса к базе данных
        cursor.execute("SELECT * FROM Products WHERE ProductID = %s", (productId,))
        product = cursor.fetchone()
        cursor.close()
        conn.close()

        # Проверка на наличие товара с таким ID
        if product:
            # Преобразование записи в словарь
            product_data = {
                "ProductID": product["productid"],
                "Name": product["name"],
                "Description": product["description"],
                "Price": str(product["price"]),  # DECIMAL возвращается как Decimal, преобразуем в строку
                "Quantity": product["quantity"],
                "CreatedAt": product["createdat"].isoformat()
            }
            return jsonify(product_data), 200
        else:
            return jsonify({"error": "Product not found"}), 404
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return jsonify({"error": "Internal server error"}), 500


@app.route('/products/<int:productId>', methods=['PUT'])
def update_product(productId):
    # Получение данных из тела запроса
    data = request.json
    name = data.get('name')
    description = data.get('description')
    price = data.get('price')
    quantity = data.get('quantity')

    try:
        # Установление соединения с базой данных
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Обновление данных о товаре в базе данных
        cursor.execute("""
            UPDATE Products SET Name = %s, Description = %s, Price = %s, Quantity = %s
            WHERE ProductID = %s
            RETURNING *;
        """, (name, description, price, quantity, productId))

        updated_product = cursor.fetchone()
        conn.commit()  # Не забудьте подтвердить изменения
        cursor.close()
        conn.close()

        if updated_product:
            # Преобразование обновленной записи в словарь
            product_data = {
                "ProductID": updated_product["productid"],
                "Name": updated_product["name"],
                "Description": updated_product["description"],
                "Price": str(updated_product["price"]),
                "Quantity": updated_product["quantity"],
                "CreatedAt": updated_product["createdat"].isoformat()
            }
            return jsonify(product_data), 200
        else:
            return jsonify({"error": "Product not found"}), 404
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return jsonify({"error": "Internal server error"}), 500


@app.route('/products/<int:productId>', methods=['DELETE'])
def delete_product(productId):
    try:
        # Установление соединения с базой данных
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Выполнение запроса на удаление товара
        cursor.execute("DELETE FROM Products WHERE ProductID = %s RETURNING *;", (productId,))
        deleted_product = cursor.fetchone()
        conn.commit()  # Подтверждение изменений
        cursor.close()
        conn.close()

        if deleted_product:
            # Возврат подтверждения об успешном удалении
            return jsonify({"message": "Product deleted successfully"}), 200
        else:
            # Товар с указанным ID не найден
            return jsonify({"error": "Product not found"}), 404
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return jsonify({"error": "Internal server error"}), 500

# ---CART---
@app.route('/carts', methods=['POST'])
def create_cart():
    data = request.get_json()
    userId = data['userId']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO Carts (UserID) VALUES (%s) RETURNING CartID;', (userId,))
    cart_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'cartId': cart_id}), 201

@app.route('/carts/<int:cartId>', methods=['GET'])
def read_cart(cartId):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute('''
    SELECT p.ProductID, p.Name, p.Description, p.Price, ci.Quantity 
    FROM CartItems ci 
    JOIN Products p ON ci.ProductID = p.ProductID 
    WHERE ci.CartID = %s;
    ''', (cartId,))
    items = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([dict(item) for item in items])

@app.route('/carts/<int:cartId>/add', methods=['PUT'])
def add_product_to_cart(cartId):
    data = request.get_json()
    productId = data['productId']
    quantity = data['quantity']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO CartItems (CartID, ProductID, Quantity) VALUES (%s, %s, %s);', (cartId, productId, quantity))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Product added to cart successfully.'}), 200


@app.route('/carts/<int:cartId>', methods=['DELETE'])
def clear_cart(cartId):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM CartItems WHERE CartID = %s; DELETE FROM carts WHERE cartid = %s', (cartId,cartId,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Cart cleared successfully.'}), 200

# --ORDER--
@app.route('/orders', methods=['POST'])
def create_order():
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()

    # Calculate total price from cart items and products
    cur.execute(
        'SELECT SUM(p.Price * ci.Quantity) FROM CartItems ci JOIN Products p ON ci.ProductID = p.ProductID WHERE ci.CartID = %s',
        (data['cartId'],))
    total_price = cur.fetchone()[0]

    # Insert the new order
    cur.execute(
        'INSERT INTO Orders (CartID, UserID, TotalPrice, Status) VALUES (%s, (SELECT UserID FROM Carts WHERE CartID = %s), %s, %s) RETURNING OrderID;',
        (data['cartId'], data['cartId'], total_price, 'Pending'))
    order_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({'orderId': order_id}), 201


# Read order information
@app.route('/orders/<int:order_id>', methods=['GET'])
def read_order(order_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute('SELECT * FROM Orders WHERE OrderID = %s', (order_id,))
    order = cur.fetchone()
    cur.close()
    conn.close()

    if order:
        return jsonify(dict(order)), 200
    else:
        return jsonify({'error': 'Order not found'}), 404


# Update order status
@app.route('/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    data = request.json
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('UPDATE Orders SET Status = %s WHERE OrderID = %s', (data['status'], order_id))
    conn.commit()

    if cur.rowcount == 0:
        cur.close()
        conn.close()
        return jsonify({'error': 'Order not found'}), 404

    cur.close()
    conn.close()
    return jsonify({'message': 'Order status updated'}), 200


# Delete an order
@app.route('/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute('DELETE FROM Orders WHERE OrderID = %s', (order_id,))
    conn.commit()

    if cur.rowcount == 0:
        cur.close()
        conn.close()
        return jsonify({'error': 'Order not found'}), 404

    cur.close()
    conn.close()
    return jsonify({'message': 'Order deleted'}), 200

if __name__ == '__main__':
    app.run(debug=True)
