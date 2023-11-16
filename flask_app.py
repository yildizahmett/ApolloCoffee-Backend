from flask import Flask, request
import functools
from flask_jwt_extended import JWTManager, verify_jwt_in_request, get_jwt, create_access_token
from pyrebase import pyrebase

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin'

JWT_ACCESS_TOKEN_EXPIRES = 100000
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
        return {"coffees": coffees}, 200
    
        if coffees is None:
            return {"message": "No coffees found"}, 404
    
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
    






@app.route("/customer/login", methods=['GET'])
def customer_login():
    try:
        return {"access_token": "selam"}, 200
    
    except Exception as e:
        print(e)
        return {"message": "An error occured"}, 500

@app.route("/customer/protected", methods=['GET'])
@customer_auth()
def customer_protected():
    return {"message": "Customer Protected Route"}, 200



if __name__ == "__main__":
    app.run(debug=True)
