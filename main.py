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
from flask import redirect
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
    return render_template('base.html', title='Главная')


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
    if form.validate_on_submit():
        with create_session() as db_sess:
            user = db_sess.query(User).filter(User.email == form.email.data).first()
            if not user:
                return render_template('login.html',
                                       message="Такого пользователя не нашлось",
                                       form=form)
            if user.check_password(form.password.data):
                if form.is_admin.data:
                    if form.secret_password.data != SECRET_KEY_FOR_ADMINS:
                        return render_template('login.html',
                                               message="Неправильный секретный пароль",
                                               form=form)
                    else:
                        if not user.is_admin:
                            user.is_admin = True
                            db_sess.commit()
                else:
                    user.is_admin = False
                    db_sess.commit()
                login_user(user, remember=form.remember_me.data)
                return redirect("/")
            return render_template('login.html',
                                   message="Неправильный логин или пароль",
                                   form=form)
    return render_template('login.html', title='Авторизация', form=form)

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


@app.route('/checkout', methods=['GET'])
def checkout():
    if not current_user.is_authenticated:
        form = LoginForm()
        return render_template('login.html',
                               title='Авторизация', form=form, message='Для заказа необходима авторизация')
    cart = session['cart']
    total = int(request.args.get('total', 0))

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

@app.context_processor
def cart_count():
    cart = session.get('cart', {})
    count = sum(cart.values())
    return dict(cart_count=count)


@app.route('/user_profile')
@login_required
def profile():
    with create_session() as db_sess:
        orders = db_sess.query(Order).filter(Order.user_id == current_user.id).options(
            joinedload(Order.items).joinedload(OrderItem.product)
        ) \
            .all()

    return render_template('user_profile.html',
                           user=current_user,
                           orders=orders)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")

if __name__ == '__main__':
    app.run()