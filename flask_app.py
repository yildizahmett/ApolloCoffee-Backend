from flask import Flask, request
import functools
from flask_jwt_extended import JWTManager, verify_jwt_in_request, get_jwt, create_access_token
from pyrebase import pyrebase
import datetime

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin'

JWT_ACCESS_TOKEN_EXPIRES = datetime.timedelta(hours=2)
JWT_SECRET_KEY = "secret"

FIREBASE_CONFIG = {
    "apiKey": "AIzaSyAZJaDG7Akl5j87wi02ppkofkoL89v0rSQ",
    "authDomain": "web-hw3-3768c.firebaseapp.com",
    "databaseURL": "https://web-hw3-3768c-default-rtdb.europe-west1.firebasedatabase.app/",
    "projectId": "web-hw3-3768c",
    "storageBucket": "web-hw3-3768c.appspot.com",
    "messagingSenderId": "453382869152",
    "appId": "1:453382869152:web:7d25d7afedb3d2648df9c5",
}

def customer_auth():
    def wrapper(f):
        @functools.wraps(f)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims['sub']['type'] != 'customer':
                return {"message": "Invalid token [From Decorator]"}, 403
            return f(*args, **kwargs)
        return decorator
    return wrapper

def admin_auth():
    def wrapper(f):
        @functools.wraps(f)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims['sub']['type'] != 'admin':
                return {"message": "Invalid token [From Decorator]"}, 403
            return f(*args, **kwargs)
        return decorator
    return wrapper

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = JWT_ACCESS_TOKEN_EXPIRES
jwt = JWTManager(app)

firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
db = firebase.database()

@app.route("/admin/login", methods=['POST'])
def admin_login():
    try:
        data = request.get_json()
        username = data["username"]
        password = data["password"]

        if username != ADMIN_USERNAME or password != ADMIN_PASSWORD:
            return {"message": "Invalid credentials"}, 401

        token_identity = {"type": "admin"}
        access_token = create_access_token(identity=token_identity)
        return {"access_token": access_token}, 200

    except Exception as e:
        print(e)
        return {"message": "An error occured"}, 500

@app.route("/admin/add-coffee", methods=['POST'])
@admin_auth()
def admin_add_coffee():
    try:
        data = request.get_json()

        if "name" not in data or "tall_price" not in data or "grande_price" not in data or "venti_price" not in data or "image_url" not in data:
            return {"message": "Invalid data"}, 400

        coffees = db.child("coffees").get().val()
        for coffee in coffees:
            if coffees[coffee]["name"] == data["name"]:
                return {"message": "Coffee already exists"}, 400

        coffee = {
            "name": data["name"],
            "tall_price": data["tall_price"],
            "grande_price": data["grande_price"],
            "venti_price": data["venti_price"],
            "image_url": data["image_url"]
        }

        db.child("coffees").push(coffee)
        return {"message": "Coffee added successfully"}, 200

    except Exception as e:
        print(e)
        return {"message": "An error occured"}, 500

@app.route("/admin/get-coffees", methods=['GET'])
@admin_auth()
def admin_get_coffees():
    try:
        coffees = db.child("coffees").get().val()

        if coffees is None:
            return {"message": "No coffees found"}, 404

        return coffees, 200

    except Exception as e:
        print(e)
        return {"message": "An error occured"}, 500

@app.route("/admin/get-coffee", methods=['POST'])
@admin_auth()
def admin_get_coffee():
    try:
        data = request.get_json()

        if "id" not in data:
            return {"message": "Invalid data"}, 400

        coffee = db.child("coffees").child(data["id"]).get().val()

        if coffee is None:
            return {"message": "Coffee not found"}, 404

        return coffee, 200

    except Exception as e:
        print(e)
        return {"message": "An error occured"}, 500

@app.route("/admin/update-coffee", methods=['POST'])
@admin_auth()
def admin_update_coffee():
    try:
        data = request.get_json()

        if "id" not in data or "name" not in data or "tall_price" not in data or "grande_price" not in data or "venti_price" not in data or "image_url" not in data:
            return {"message": "Invalid data"}, 400

        coffee = {
            "name": data["name"],
            "tall_price": data["tall_price"],
            "grande_price": data["grande_price"],
            "venti_price": data["venti_price"],
            "image_url": data["image_url"]
        }

        db.child("coffees").child(data["id"]).update(coffee)
        return {"message": "Coffee updated successfully"}, 200

    except Exception as e:
        print(e)
        return {"message": "An error occured"}, 500

@app.route("/admin/delete-coffee", methods=['POST'])
@admin_auth()
def admin_delete_coffee():
    try:
        data = request.get_json()

        if "id" not in data:
            return {"message": "Invalid data"}, 400

        db.child("coffees").child(data["id"]).remove()
        return {"message": "Coffee deleted successfully"}, 200

    except Exception as e:
        print(e)
        return {"message": "An error occured"}, 500

@app.route("/admin/get-orders", methods=['GET'])
@admin_auth()
def admin_get_orders():
    try:
        orders = db.child("orders").get().val()

        if orders is None:
            return {"message": "No orders found"}, 404

        return orders, 200

    except Exception as e:
        print(e)
        return {"message": "An error occured"}, 500


@app.route("/customer/login", methods=['POST'])
def customer_login():
    try:
        data = request.get_json()
        email = data["email"]
        password = data["password"]

        users = db.child("users").get().val()
        for user in users:
            if users[user]["email"] == email and users[user]["password"] == password:
                token_identity = {"type": "customer", "id": user}
                access_token = create_access_token(identity=token_identity)
                return {"access_token": access_token}, 200

        return {"message": "Invalid credentials"}, 401

    except Exception as e:
        print(e)
        return {"message": "An error occured"}, 500

@app.route("/customer/register", methods=['POST'])
def customer_register():
    try:
        data = request.get_json()

        if "email" not in data or "password" not in data or "name" not in data or "surname" not in data or "phone_number" not in data or "address" not in data:
            return {"message": "Invalid data"}, 400

        users = db.child("users").get().val()
        if users is not None:
            for user in users:
                if users[user]["email"] == data["email"]:
                    return {"message": "User already exists"}, 400

        user = {
            "email": data["email"],
            "password": data["password"],
            "name": data["name"],
            "surname": data["surname"],
            "phone_number": data["phone_number"],
            "address": data["address"]
        }

        db.child("users").push(user)
        return {"message": "User added successfully"}, 200

    except Exception as e:
        print(e)
        return {"message": "An error occured"}, 500

@app.route("/customer/get-user", methods=['GET'])
@customer_auth()
def customer_get_user():
    try:
        id = get_jwt()["sub"]["id"]

        user = db.child("users").child(id).get().val()

        if user is None:
            return {"message": "User not found"}, 404

        user["id"] = id
        del user["password"]

        return user, 200

    except Exception as e:
        print(e)
        return {"message": "An error occured"}, 500

@app.route("/customer/update-user", methods=['POST'])
@customer_auth()
def customer_update_user():
    try:
        data = request.get_json()

        if "email" not in data or "password" not in data or "name" not in data or "surname" not in data or "phone_number" not in data or "address" not in data:
            return {"message": "Invalid data"}, 400

        id = get_jwt()["sub"]["id"]

        user = {
            "email": data["email"],
            "password": data["password"],
            "name": data["name"],
            "surname": data["surname"],
            "phone_number": data["phone_number"],
            "address": data["address"]
        }

        db.child("users").child(id).update(user)
        return {"message": "User updated successfully"}, 200

    except Exception as e:
        print(e)
        return {"message": "An error occured"}, 500

@app.route("/customer/get-coffees", methods=['GET'])
@customer_auth()
def customer_get_coffees():
    try:
        coffees = db.child("coffees").get().val()

        if coffees is None:
            return {"message": "No coffees found"}, 404

        return coffees, 200

    except Exception as e:
        print(e)
        return {"message": "An error occured"}, 500

# Make order with coffee id, size and quantity. Please check sizes and quantities.
# There can be more than one coffee in the order.
# Sizes: tall, grande, venti
# Quantities: 1 to 20
@app.route("/customer/make-order", methods=['POST'])
@customer_auth()
def customer_make_order():
    try:
        data = request.get_json()

        if "deliver_time" not in data or "coffees" not in data or len(data["coffees"]) == 0:
            return {"message": "Invalid data"}, 400

        user_id = get_jwt()["sub"]["id"]

        user = db.child("users").child(user_id).get().val()
        if user is None:
            return {"message": "User not found"}, 404

        order = {
            "user_id": user_id,
            "user_name": user["name"],
            "user_surname": user["surname"],
            "user_address": user["address"],
            "user_phone_number": user["phone_number"],
            "deliver_time": data["deliver_time"],
            "coffees": []
        }

        order_coffees = data["coffees"]
        for order_coffee in order_coffees:
            coffee = db.child("coffees").child(order_coffee["id"]).get().val()
            if coffee is None:
                return {"message": "Coffee not found"}, 404

            if order_coffee["size"] not in ["tall", "grande", "venti"]:
                return {"message": "Invalid size for {}".format(order_coffee["name"])}, 400

            if order_coffee["quantity"] not in range(1, 21):
                return {"message": "Invalid size for {}".format(order_coffee["name"])}, 400

            # Add coffee to order  in a list
            coff = {
                "id": order_coffee["id"],
                "name": coffee["name"],
                "size": order_coffee["size"],
                "quantity": order_coffee["quantity"],
                "price": coffee[order_coffee["size"] + "_price"]
            }

            order["coffees"].append(coff)

        order["date"] = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        db.child("orders").push(order)
        return {"message": "Order added successfully"}, 200

    except Exception as e:
        print(e)
        return {"message": "An error occured"}, 500

@app.route("/customer/get-orders", methods=['GET'])
@customer_auth()
def customer_get_orders():
    try:
        user_id = get_jwt()["sub"]["id"]

        orders = db.child("orders").get().val()
        if orders is None:
            return {"message": "No orders found"}, 404

        user_orders = []
        for order in orders:
            if orders[order]["user_id"] == user_id:
                user_orders.append(orders[order])

        if len(user_orders) == 0:
            return {"message": "No orders found"}, 404

        return user_orders, 200

    except Exception as e:
        print(e)
        return {"message": "An error occured"}, 500


if __name__ == "__main__":
    app.run(debug=True)
