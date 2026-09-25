from flask import Flask, render_template, request, session, redirect, send_from_directory
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "rozhan-secret-key")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "rozhan.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ================= DATABASE INITIALIZATION =================

def init_database():

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            wallet_balance INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price INTEGER NOT NULL,
            description TEXT,
            image TEXT
        )
    """)

    conn.commit()
    conn.close()


# ساخت خودکار دیتابیس هنگام اجرای برنامه
init_database()


# ================= FILE CHECK =================

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


# ================= WALLET =================

def get_wallet_balance():

    user_id = session.get("user_id")

    if not user_id:
        return 0

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT wallet_balance
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    )

    result = cursor.fetchone()

    conn.close()

    if not result or result[0] is None:
        return 0

    return result[0]


# ================= CART =================

def get_cart_data():

    cart = session.get("cart", {})

    if not cart:
        return [], 0

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cart_items = []
    cart_total = 0

    for product_id, quantity in cart.items():

        try:
            product_id = int(product_id)
            quantity = int(quantity)
        except (ValueError, TypeError):
            continue

        if quantity <= 0:
            continue

        cursor.execute(
            """
            SELECT id, name, price, description, image
            FROM products
            WHERE id = ?
            """,
            (product_id,)
        )

        product = cursor.fetchone()

        if not product:
            continue

        item_total = product[2] * quantity

        cart_items.append({
            "id": product[0],
            "name": product[1],
            "price": product[2],
            "description": product[3],
            "image": product[4],
            "quantity": quantity,
            "total": item_total
        })

        cart_total += item_total

    conn.close()

    return cart_items, cart_total


# ================= HOME =================

@app.route("/")
def home():

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, price, description, image
        FROM products
        ORDER BY id DESC
    """)

    products = cursor.fetchall()

    conn.close()

    cart_items, cart_total = get_cart_data()

    cart_count = sum(
        item["quantity"]
        for item in cart_items
    )

    wallet_balance = get_wallet_balance()

    return render_template(
        "rozhan.html",
        user_name=session.get("user_name"),
        is_admin=session.get("is_admin", 0),
        products=products,
        cart_items=cart_items,
        cart_total=cart_total,
        cart_count=cart_count,
        wallet_balance=wallet_balance
    )


# ================= UPLOADS =================

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename
    )


# ================= REGISTER =================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        phone = request.form["phone"]
        password = request.form["password"]
        password_confirm = request.form["password_confirm"]

        if password != password_confirm:
            return "رمز عبور و تکرار رمز عبور یکسان نیستند ❌"

        password_hash = generate_password_hash(password)

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM users WHERE phone = ?",
            (phone,)
        )

        existing_user = cursor.fetchone()

        if existing_user:
            conn.close()
            return "این شماره تلفن قبلاً ثبت شده است ❌"

        cursor.execute(
            """
            INSERT INTO users (name, phone, password, wallet_balance)
            VALUES (?, ?, ?, ?)
            """,
            (name, phone, password_hash, 0)
        )

        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("rozhan.html")


# ================= LOGIN =================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        phone = request.form["phone"]
        password = request.form["password"]

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, name, phone, password, is_admin, wallet_balance
            FROM users
            WHERE phone = ?
            """,
            (phone,)
        )

        user = cursor.fetchone()

        conn.close()

        if user and check_password_hash(user[3], password):

            session["user_id"] = user[0]
            session["user_name"] = user[1]
            session["user_phone"] = user[2]
            session["is_admin"] = user[4]
            session["wallet_balance"] = user[5] or 0

            return redirect("/")

        return "شماره تلفن یا رمز عبور اشتباه است ❌"

    return render_template("rozhan.html")


# ================= LOGOUT =================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# ================= ADD WALLET BALANCE =================

@app.route("/wallet/add", methods=["POST"])
def add_wallet_balance():

    if not session.get("user_id"):
        return "ابتدا باید وارد حساب کاربری شوید ❌"

    amount = request.form.get("amount", "").strip()

    if not amount:
        return "لطفاً مبلغ را وارد کنید ❌"

    try:
        amount = int(amount)
    except ValueError:
        return "مبلغ وارد شده معتبر نیست ❌"

    if amount <= 0:
        return "مبلغ باید بیشتر از صفر باشد ❌"

    if amount > 100_000_000:
        return "حداکثر مبلغ قابل افزایش در هر بار ۱۰۰ میلیون تومان است ❌"

    user_id = session.get("user_id")

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT wallet_balance
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    )

    result = cursor.fetchone()

    if not result:
        conn.close()
        return "کاربر پیدا نشد ❌"

    current_balance = result[0] or 0

    max_sqlite_integer = 9_223_372_036_854_775_807

    if current_balance + amount > max_sqlite_integer:
        conn.close()
        return "موجودی کیف پول بیش از حد مجاز است ❌"

    new_balance = current_balance + amount

    cursor.execute(
        """
        UPDATE users
        SET wallet_balance = ?
        WHERE id = ?
        """,
        (new_balance, user_id)
    )

    conn.commit()
    conn.close()

    session["wallet_balance"] = new_balance

    return redirect("/#wallet")


# ================= PAY WITH WALLET =================

@app.route("/wallet/pay", methods=["POST"])
def pay_with_wallet():

    if not session.get("user_id"):
        return "ابتدا باید وارد حساب کاربری شوید ❌"

    cart_items, cart_total = get_cart_data()

    if not cart_items or cart_total <= 0:
        return "سبد خرید شما خالی است ❌"

    user_id = session.get("user_id")

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    try:

        conn.execute("BEGIN IMMEDIATE")

        cursor.execute(
            """
            SELECT wallet_balance
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        )

        result = cursor.fetchone()

        if not result:
            conn.rollback()
            conn.close()
            return "کاربر پیدا نشد ❌"

        current_balance = result[0] or 0

        if current_balance < cart_total:
            conn.rollback()
            conn.close()

            return (
                "موجودی کیف پول شما کافی نیست ❌"
                "<br><br>"
                f"مبلغ سبد خرید: {cart_total:,} تومان"
                "<br>"
                f"موجودی کیف پول: {current_balance:,} تومان"
                "<br><br>"
                '<a href="/#wallet">رفتن به کیف پول 💰</a>'
            )

        new_balance = current_balance - cart_total

        cursor.execute(
            """
            UPDATE users
            SET wallet_balance = ?
            WHERE id = ?
            """,
            (new_balance, user_id)
        )

        conn.commit()

        session["wallet_balance"] = new_balance

        session["cart"] = {}
        session.modified = True

        conn.close()

        return f"""
<!DOCTYPE html>
<html lang="fa" dir="rtl">

<head>

    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>
        پرداخت موفق | ما سه نفر
    </title>

    <link
        rel="stylesheet"
        href="/static/css/style.css"
    >

</head>

<body>

    <main>

        <section class="section">

            <div class="form-box">

                <div class="section-icon">
                    🎉
                </div>

                <h2>
                    پرداخت با موفقیت انجام شد
                </h2>

                <p>
                    سفارش شما با موفقیت پرداخت شد ❤️
                </p>

                <div class="wallet-balance">
                    {cart_total:,} تومان
                </div>

                <p>
                    مبلغ پرداخت شده
                </p>

                <div class="wallet-balance">
                    {new_balance:,} تومان
                </div>

                <p>
                    موجودی جدید کیف پول
                </p>

                <br>

                <a
                    href="/#products"
                    class="main-button"
                >
                    🛍️ بازگشت به فروشگاه
                </a>

            </div>

        </section>

    </main>

</body>

</html>
"""

    except Exception:

        conn.rollback()
        conn.close()

        return "پرداخت انجام نشد؛ لطفاً دوباره تلاش کنید ❌"


# ================= ADMIN =================

@app.route("/admin")
def admin():

    if not session.get("user_id"):
        return "ابتدا باید وارد حساب کاربری شوید ❌"

    if not session.get("is_admin"):
        return "شما اجازه ورود به پنل مدیریت را ندارید ❌"

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, price, description, image
        FROM products
        ORDER BY id DESC
    """)

    products = cursor.fetchall()

    conn.close()

    return render_template(
        "admin.html",
        products=products
    )


# ================= ADD PRODUCT =================

@app.route("/admin/add-product", methods=["POST"])
def add_product():

    if not session.get("user_id"):
        return "ابتدا باید وارد حساب کاربری شوید ❌"

    if not session.get("is_admin"):
        return "شما اجازه افزودن محصول را ندارید ❌"

    name = request.form.get("name", "").strip()
    price = request.form.get("price", "").strip()
    description = request.form.get("description", "").strip()

    image = request.files.get("image")

    if not name:
        return "نام محصول وارد نشده است ❌"

    if not price:
        return "قیمت محصول وارد نشده است ❌"

    image_filename = ""

    if image and image.filename:

        if not allowed_file(image.filename):
            return "فرمت تصویر مجاز نیست ❌"

        original_name = secure_filename(image.filename)

        if not original_name:
            return "نام فایل تصویر معتبر نیست ❌"

        image_filename = original_name

        image_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            image_filename
        )

        print("مسیر ذخیره تصویر:")
        print(image_path)

        image.save(image_path)

        print("تصویر با موفقیت ذخیره شد ✅")

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO products (name, price, description, image)
        VALUES (?, ?, ?, ?)
        """,
        (
            name,
            price,
            description,
            image_filename
        )
    )

    conn.commit()
    conn.close()

    return redirect("/admin")


# ================= DELETE PRODUCT =================

@app.route("/admin/delete-product/<int:product_id>", methods=["POST"])
def delete_product(product_id):

    if not session.get("user_id"):
        return "ابتدا باید وارد حساب کاربری شوید ❌"

    if not session.get("is_admin"):
        return "شما اجازه حذف محصول را ندارید ❌"

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT image FROM products WHERE id = ?",
        (product_id,)
    )

    product = cursor.fetchone()

    if not product:
        conn.close()
        return "محصول پیدا نشد ❌"

    image_filename = product[0]

    cursor.execute(
        "DELETE FROM products WHERE id = ?",
        (product_id,)
    )

    conn.commit()
    conn.close()

    if image_filename:

        image_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            image_filename
        )

        if os.path.exists(image_path):
            os.remove(image_path)

    return redirect("/admin")


# ================= ADD TO CART =================

@app.route("/cart/add/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM products WHERE id = ?",
        (product_id,)
    )

    product = cursor.fetchone()

    conn.close()

    if not product:
        return "محصول پیدا نشد ❌"

    cart = session.get("cart", {})

    product_id = str(product_id)

    if product_id in cart:
        cart[product_id] += 1
    else:
        cart[product_id] = 1

    session["cart"] = cart
    session.modified = True

    return redirect("/#cart")


# ================= INCREASE CART ITEM =================

@app.route("/cart/increase/<int:product_id>", methods=["POST"])
def increase_cart_item(product_id):

    cart = session.get("cart", {})

    product_id = str(product_id)

    if product_id in cart:
        cart[product_id] += 1

    session["cart"] = cart
    session.modified = True

    return redirect("/#cart")


# ================= DECREASE CART ITEM =================

@app.route("/cart/decrease/<int:product_id>", methods=["POST"])
def decrease_cart_item(product_id):

    cart = session.get("cart", {})

    product_id = str(product_id)

    if product_id in cart:

        cart[product_id] -= 1

        if cart[product_id] <= 0:
            del cart[product_id]

    session["cart"] = cart
    session.modified = True

    return redirect("/#cart")


# ================= REMOVE FROM CART =================

@app.route("/cart/remove/<int:product_id>", methods=["POST"])
def remove_from_cart(product_id):

    cart = session.get("cart", {})

    product_id = str(product_id)

    if product_id in cart:
        del cart[product_id]

    session["cart"] = cart
    session.modified = True

    return redirect("/#cart")


# ================= RUN =================

if __name__ == "__main__":
    app.run(debug=True, port=8000)