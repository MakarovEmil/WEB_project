import os
import datetime
from flask import Flask
from flask import render_template
from data.users import User
from data.categories import Category
from data.products import Product
from data.order_item import OrderItem
from data.orders import Order
from data.db_session import global_init, create_session
from data.forms.registration import RegisterForm
from data.forms.add_product import AddProductForm
from data.forms.login import LoginForm
from flask import redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required
from flask_login import current_user
from flask import request
from flask_restful import Api
from data.api import user_resources
from data.api import products_resources
from requests import get, post, delete, put
from flask import session
from sqlalchemy.orm import joinedload

UPLOAD_FOLDER_FOR_AVATARS_USERS = 'static/image/uploads/avatars_users/'
UPLOAD_FOLDER_FOR_AVATARS_PRODUCTS = 'static/image/uploads/avatars_products/'
PRODUCT_DEFAULT_LOGO = 'static/image/logo/default_product_logo.jpg'
USER_DEFAULT_LOGO = 'static/image/logo/default_logo.png'
ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif']

SECRET_KEY_FOR_ADMINS = 'вкусные семечки'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(
    days=365
)

api = Api(app)
api.add_resource(user_resources.UsersListResource, '/api/users')
api.add_resource(user_resources.UsersResource, '/api/users/<int:user_id>')

api.add_resource(products_resources.ProductsListResource, '/api/products')
api.add_resource(products_resources.ProductsResource, '/api/products/<int:product_id>')


login_manager = LoginManager()
login_manager.init_app(app)

global_init('db/garden_seeds.db')


def save_file(file, entity_id, upload_folder):
    if not file or file.filename == '':
        return None

    ext = file.filename.rsplit('.', 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return None

    filename = f"{entity_id}.{ext}"
    file.save(os.path.join(upload_folder, filename))
    return f'{upload_folder}/{filename}'


def delete_file(file_path, default_path=None):
    if not file_path:
        return
    if default_path and file_path == default_path:
        return
    full_path = os.path.join(os.path.dirname(__file__), file_path)
    if os.path.exists(full_path):
        os.remove(full_path)

@login_manager.user_loader
def load_user(user_id):
    db_sess = create_session()
    return db_sess.get(User, user_id)

@app.route('/', methods=['GET', 'POST'])
def index():
    current_month = datetime.datetime.now().month

    with create_session() as db_sess:
        popular_products = db_sess.query(Product) \
            .join(OrderItem, OrderItem.product_id == Product.id) \
            .group_by(Product.id) \
            .limit(4) \
            .all()

        categories = db_sess.query(Category).all()

        seasonal_products = db_sess.query(Product) \
            .filter(Product.sowing_month_start <= current_month) \
            .filter(Product.sowing_month_end >= current_month) \
            .limit(4) \
            .all()

    return render_template('index.html',
                           title='Главная',
                           popular_products=popular_products,
                           categories=categories,
                           seasonal_products=seasonal_products,
                           now=datetime.datetime.now())


@app.route('/register', methods=['GET', 'POST'])
def registration():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('registration.html', title='Регистрация',
                                   form=form, message="Пароли не совпадают")

        with create_session() as db_sess:
            if db_sess.query(User).filter(User.email == form.email.data).first():
                return render_template('registration.html', title='Регистрация',
                                       form=form, message="Такой пользователь уже есть")

            user = User(
                surname=form.surname.data,
                name=form.name.data,
                age=form.age.data,
                email=form.email.data,
            )
            user.set_password(form.password.data)
            db_sess.add(user)
            db_sess.flush()

            file = request.files.get('file')
            avatar_path = save_file(file, user.id,
                                    UPLOAD_FOLDER_FOR_AVATARS_USERS)
            user.image_path = avatar_path if avatar_path else USER_DEFAULT_LOGO

            db_sess.commit()
            return redirect('/login')

    return render_template('user.html', title='Регистрация', form=form)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = RegisterForm()

    with create_session() as db_sess:
        user = db_sess.get(User, current_user.id)

        if request.method == 'GET':
            form.email.data = user.email
            form.surname.data = user.surname
            form.name.data = user.name
            form.age.data = user.age

        if form.validate_on_submit():
            user.email = form.email.data
            user.surname = form.surname.data
            user.name = form.name.data
            user.age = form.age.data

            if form.age.data <= 1:
                return render_template('user.html', title='Редактирование профиля',
                                       form=form, user=user, message="Некоректный возраст")

            if form.password.data:
                if form.password.data != form.password_again.data:
                    return render_template('user.html', title='Редактирование профиля',
                                           form=form, user=user, message="Пароли не совпадают")
                user.set_password(form.password.data)

            if request.form.get('delete_avatar') == 'on':
                delete_file(user.image_path, USER_DEFAULT_LOGO)
                user.image_path = USER_DEFAULT_LOGO

            file = request.files.get('file')
            if file and file.filename != '':
                delete_file(user.image_path, USER_DEFAULT_LOGO)
                avatar_path = save_file(file, user.id, UPLOAD_FOLDER_FOR_AVATARS_USERS)
                if avatar_path:
                    user.image_path = avatar_path

            db_sess.commit()
            return redirect('/')

        return render_template('user.html', title='Редактирование профиля',
                               form=form, user=user)
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    next_url = request.args.get('next', '/')
    if form.validate_on_submit():
        with create_session() as db_sess:
            user = db_sess.query(User).filter(User.email == form.email.data).first()
            if not user:
                return render_template('login.html',
                                       message="Такого пользователя не нашлось",
                                       form=form,
                                       next=next_url)
            if user.check_password(form.password.data):
                if form.is_admin.data:
                    if form.secret_password.data != SECRET_KEY_FOR_ADMINS:
                        return render_template('login.html',
                                               message="Неправильный секретный пароль",
                                               form=form,
                                               next=next_url)
                    else:
                        if not user.is_admin:
                            user.is_admin = True
                            db_sess.commit()
                else:
                    user.is_admin = False
                    db_sess.commit()
                login_user(user, remember=form.remember_me.data)
                return redirect(next_url)
            return render_template('login.html',
                                   message="Неправильный логин или пароль",
                                   form=form,
                                   next=next_url)
    return render_template('login.html', title='Авторизация', form=form, next=next_url)

@app.route('/catalog')
def catalog():
    search_query = request.args.get('search', '')
    category_id = request.args.get('category', 0)

    with create_session() as db_sess:
        query = db_sess.query(Product)

        if search_query:
            query = query.filter(Product.name.like(f'%{search_query}%'))

        if category_id and int(category_id) > 0:
            query = query.filter(Product.category_id == int(category_id))

        products = query.all()
        categories = db_sess.query(Category).all()

        return render_template('catalog.html',
                               products=products,
                               categories=categories,
                               search_query=search_query,
                               current_category=int(category_id) if category_id else 0)


@app.route('/admin/products/mass-delete', methods=['POST'])
def mass_delete():
    product_ids = request.form.getlist('product_ids')
    for product_id in product_ids:
        with create_session() as db_sess:
            product = db_sess.get(Product, product_id)
        delete_file(product.image_path, PRODUCT_DEFAULT_LOGO)
        delete(f'http://127.0.0.1:5000/api/products/{product_id}')
    return redirect(request.referrer or '/catalog')

@app.route('/admin/product/add_product', methods=['GET', 'POST'])
def add_product():
    form = AddProductForm()
    with create_session() as db_sess:
        categories = db_sess.query(Category).all()
        form.category_id.choices = [(c.id, c.name) for c in categories]
        if form.validate_on_submit():
            if db_sess.query(Product).filter(Product.name == form.name.data).first():
                return render_template('product.html', title='Добавление товара',
                                       form=form,
                                       message="Такой товар уже есть", product=None)

            if form.stock.data < 0 or form.price.data < 0:
                return render_template('product.html', title='Добавление товара',
                                       form=form,
                                       message="Некоректная цена или остаток товара", product=None)

            product = Product(
                name=form.name.data,
                price=form.price.data,
                stock=form.stock.data,
                description=form.description.data,
                category_id = form.category_id.data,
                difficulty=form.difficulty.data,
                sowing_month_start=form.sowing_month_start.data,
                sowing_month_end=form.sowing_month_end.data
            )
            db_sess.add(product)
            db_sess.commit()

            file = request.files.get('file')
            image_path = save_file(file, product.id, UPLOAD_FOLDER_FOR_AVATARS_PRODUCTS)
            product.image_path = image_path if image_path else PRODUCT_DEFAULT_LOGO

            db_sess.commit()
            return redirect('/')
    return render_template('product.html', title='Добавление товара',
                           form=form, categories=categories, product=None)


@app.route('/admin/product/delete/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    with create_session() as db_sess:
        product = db_sess.get(Product, product_id)
        if product:
            delete_file(product.image_path, PRODUCT_DEFAULT_LOGO)
            delete(f'http://127.0.0.1:5000/api/products/{product_id}')
            db_sess.commit()

    return redirect(request.referrer or '/catalog')


@app.route('/admin/product/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    form = AddProductForm()
    with create_session() as db_sess:
        categories = db_sess.query(Category).all()
        form.category_id.choices = [(c.id, c.name) for c in categories]
        product = db_sess.get(Product, product_id)

        if not product:
            return redirect('/catalog')

        if request.method == 'GET':
            form.name.data = product.name
            form.price.data = product.price
            form.stock.data = product.stock
            form.description.data = product.description
            form.category_id.data = product.category_id
            form.difficulty.data = product.difficulty
            form.sowing_month_start.data = product.sowing_month_start
            form.sowing_month_end.data = product.sowing_month_end

        if form.validate_on_submit():

            if form.stock.data < 0 or form.price.data < 0:
                return render_template('product.html', title='Добавление товара',
                                       form=form,
                                       message="Некоректная цена или остаток товара", product=None)

            product.name = form.name.data
            product.price = form.price.data
            product.stock = form.stock.data
            product.description = form.description.data
            product.category_id = form.category_id.data
            product.difficulty = form.difficulty.data
            product.sowing_month_start = form.sowing_month_start.data
            product.sowing_month_end = form.sowing_month_end.data

            if request.form.get('delete_photo') == 'on':
                delete_file(product.image_path, PRODUCT_DEFAULT_LOGO)
                product.image_path = PRODUCT_DEFAULT_LOGO

            file = request.files.get('file')
            if file and file.filename != '':
                delete_file(product.image_path, PRODUCT_DEFAULT_LOGO)
                image_path = save_file(file, product.id,
                                       UPLOAD_FOLDER_FOR_AVATARS_PRODUCTS)
                if image_path:
                    product.image_path = image_path

            db_sess.commit()
            return redirect('/catalog')

    return render_template('product.html', title='Редактирование товара',
                           form=form, product=product)


@app.route('/product/<int:product_id>')
def product_card(product_id):
    with create_session() as db_sess:
        product = db_sess.get(Product, product_id)
        popularity_count = db_sess.query(OrderItem).filter(OrderItem.product_id == product.id).count()
        similar_products = db_sess.query(Product).filter(
            Product.category_id == product.category_id,
            Product.id != product.id).limit(4).all()
    return render_template('product_card.html', title='Карточка товара',
                           product=product, popularity_count=popularity_count, similar_products=similar_products)


@app.route('/cart/add/<int:product_id>', methods=['POST'])
def add(product_id):
    quantity = int(request.form.get('quantity'))
    with create_session() as db_sess:
        product = db_sess.get(Product, int(product_id))
    if not product:
        return redirect(request.referrer)

    cart = session.get('cart', {})

    current = int(cart.get(str(product_id), 0))
    new_quantity = current + quantity

    if int(product.stock) < new_quantity:
        if int(product.stock) < new_quantity:
            return render_template('product_card.html',
                                   product=product,
                                   message='Недостаточно товара на складе')

    cart[str(product_id)] = new_quantity
    session.permanent = True
    session['cart'] = cart

    return redirect('/catalog')


@app.route('/cart')
def cart():
    cart = session.get('cart', {})

    items = []
    total = 0

    with create_session() as db_sess:

        for product_id, quantity in cart.items():
            product = db_sess.get(Product, int(product_id))
            if product:
                item_total = product.price * quantity
                items.append({
                    'product': product,
                    'quantity': quantity,
                    'item_total': item_total
                })
                total += item_total

    return render_template('cart.html',
                           items=items,
                           total=total)


@app.route('/cart/change/<int:product_id>', methods=['POST'])
def change_cart(product_id):
    cart = session.get('cart', {})
    quantity = int(request.form.get('quantity'))
    cart[str(product_id)] = quantity
    session['cart'] = cart
    return redirect(request.referrer or '/cart')


@app.route('/cart/remove/<int:product_id>', methods=['POST'])
def remove(product_id):
    cart = session.get('cart', {})
    cart.pop(str(product_id), None)
    session['cart'] = cart
    return redirect(request.referrer or '/cart')


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if not current_user.is_authenticated:
        return redirect(url_for('login', next='/checkout'))
    cart = session['cart']

    with create_session() as db_sess:
        total = 0
        for product_id, quantity in cart.items():
            product = db_sess.get(Product, int(product_id))
            if product:
                total += product.price * quantity

    discount = 0
    if current_user.total_spent >= 10000:
        discount = 10
    elif current_user.total_spent >= 3000:
        discount = 5
    elif current_user.total_spent >= 1000:
        discount = 3
    final_total = total * (100 - discount) / 100

    with create_session() as db_sess:

        order = Order(
            user_id=current_user.id,
            order_date=datetime.datetime.now(),
            total_amount=final_total,
            discount_percent=discount
        )
        db_sess.add(order)
        db_sess.commit()
        order_id = order.id

        for product_id, quantity in cart.items():
            product = db_sess.get(Product, int(product_id))
            order_item = OrderItem(
                order_id=order_id,
                product_id=product_id,
                quantity=quantity,
                price_at_moment=product.price
            )
            product.stock -= quantity
            db_sess.add(order_item)

        user = db_sess.get(User, current_user.id)
        user.total_orders_count += 1
        user.total_spent += final_total


        db_sess.commit()

        session.pop('cart', None)


    return redirect('/')


@app.route('/order/<int:order_id>')
def order_card(order_id):
    with create_session() as db_sess:
        order = db_sess.query(Order).options(joinedload(Order.user),
            joinedload(Order.items).joinedload(OrderItem.product)
        ) \
            .filter(Order.id == order_id) \
            .first()

        return render_template('order_card.html', title='Карточка заказа', order=order)


@app.route('/admin/reports', methods=['GET', 'POST'])
@login_required
def reports():

    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    report_type = request.args.get('report_type', 'orders')

    orders = []
    total_amount = 0
    total_orders = 0
    avg_check = 0

    error_message = None
    products_data = None
    customers_data = None

    if date_from and date_to:
        try:
            start_date = datetime.datetime.strptime(date_from, '%Y-%m-%d')
            end_date = datetime.datetime.strptime(date_to, '%Y-%m-%d')

            if start_date > end_date:
                error_message = "Ошибка: дата «от» не может быть позже даты «до»"
            else:
                with create_session() as db_sess:
                    if report_type == 'orders':
                        orders = db_sess.query(Order) \
                            .options(joinedload(Order.user)) \
                            .filter(Order.order_date >= start_date) \
                            .filter(Order.order_date <= end_date) \
                            .order_by(Order.order_date) \
                            .all()

                        total_orders = len(orders)
                        total_amount = sum(order.total_amount for order in orders)
                        if total_orders > 0:
                            avg_check = total_amount // total_orders
                    elif report_type == 'products':
                        all_products = db_sess.query(Product).all()

                        products_list = []

                        for product in all_products:
                            quantity = 0
                            total = 0

                            for item in product.order_items:
                                if start_date <= item.order.order_date <= end_date:
                                    quantity += item.quantity
                                    total += item.quantity * item.price_at_moment

                            if quantity > 0:
                                products_list.append({
                                    'id': product.id,
                                    'name': product.name,
                                    'quantity': quantity,
                                    'total': total
                                })

                        products_list.sort(key=lambda x: x['total'], reverse=True)

                        products_data = {
                            'total_products_sold': len(products_list),
                            'total_quantity': sum(p['quantity'] for p in products_list),
                            'total_amount': sum(p['total'] for p in products_list),
                            'details': products_list
                        }

                    elif report_type == 'customers':
                        orders_for_customers = db_sess.query(Order) \
                            .options(joinedload(Order.user)) \
                            .filter(Order.order_date >= start_date) \
                            .filter(Order.order_date <= end_date) \
                            .all()

                        customers_dict = {}
                        for order in orders_for_customers:
                            user_id = order.user.id
                            if user_id not in customers_dict:
                                customers_dict[user_id] = {
                                    'user_id': user_id,
                                    'name': f"{order.user.surname} {order.user.name}",
                                    'orders_count': 0,
                                    'total_spent': 0
                                }
                            customers_dict[user_id]['orders_count'] += 1
                            customers_dict[user_id]['total_spent'] += order.total_amount

                        customers_list = list(customers_dict.values())
                        customers_list.sort(key=lambda x: x['total_spent'], reverse=True)

                        total_customers = len(customers_list)
                        total_amount_customers = sum(c['total_spent'] for c in customers_list)
                        avg_per_customer = total_amount_customers // total_customers if total_customers > 0 else 0

                        customers_data = {
                            'total_customers': total_customers,
                            'total_amount': total_amount_customers,
                            'avg_per_customer': avg_per_customer,
                            'details': customers_list
                        }

        except ValueError:
            error_message = "Ошибка: неверный формат даты"

    return render_template('reports.html',
                         title='Отчёты',
                         date_from=date_from,
                         date_to=date_to,
                         report_type=report_type,
                         orders=orders,
                         total_amount=total_amount,
                         total_orders=total_orders,
                         avg_check=avg_check,
                         products_data=products_data,
                         customers_data=customers_data,
                         error_message=error_message)
@app.context_processor
def cart_count():
    cart = session.get('cart', {})
    count = sum(cart.values())
    return dict(cart_count=count)


@app.route('/user_profile')
@login_required
def user_profile():
    return show_user_profile(current_user.id)


@app.route('/admin/user/<int:user_id>')
@login_required
def admin_user_profile(user_id):
    return show_user_profile(user_id)


def show_user_profile(user_id):
    with create_session() as db_sess:
        user = db_sess.get(User, user_id)

        orders = db_sess.query(Order) \
            .options(joinedload(Order.items).joinedload(OrderItem.product)) \
            .filter(Order.user_id == user.id) \
            .order_by(Order.order_date.desc()) \
            .all()

    return render_template('user_profile.html',
                           title='Профиль пользователя',
                           user=user,
                           orders=orders)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")

if __name__ == '__main__':
    app.run()