import os
from flask import Flask
from flask import render_template
from data.users import User
from data.categories import Category
from data.products import Product
from data.db_session import global_init, create_session
from data.forms.registration import RegisterForm
from data.forms.add_product import AddProductForm
from data.forms.login import LoginForm
from flask import redirect
from flask_login import LoginManager, login_user, logout_user, login_required
from flask import request
from flask_restful import Api
from data.api import user_resources
from data.api import products_resources
from requests import get, post, delete, put

UPLOAD_FOLDER_FOR_AVATARS_USERS = 'static/image/uploads/avatars_users/'
UPLOAD_FOLDER_FOR_AVATARS_PRODUCTS = 'static/image/uploads/avatars_products/'
ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif']

SECRET_KEY_FOR_ADMINS = 'вкусные семечки'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

api = Api(app)
api.add_resource(user_resources.UsersListResource, '/api/users')
api.add_resource(user_resources.UsersResource, '/api/users/<int:user_id>')

api.add_resource(products_resources.ProductsListResource, '/api/products')
api.add_resource(products_resources.ProductsResource, '/api/products/<int:product_id>')


login_manager = LoginManager()
login_manager.init_app(app)

global_init('db/garden_seeds.db')
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
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('registration.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            surname=form.surname.data,
            name=form.name.data,
            age=form.age.data,
            email=form.email.data,
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()

        file = request.files.get('file')
        if file and file.filename != '':
            ext = file.filename.rsplit('.', 1)[1].lower()
            if ext in ALLOWED_EXTENSIONS:
                filename = f"{user.id}.{ext}"

                file.save(os.path.join(UPLOAD_FOLDER_FOR_AVATARS_USERS, filename))

                user.image_path = f'static/image/uploads/avatars_users/{filename}'

                db_sess.commit()
        else:
            filename = "default_logo.png"
            user.image_path = f'static/image/logo/{filename}'
            db_sess.commit()
        return redirect('/')
    return render_template('registration.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = create_session()
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

    db_sess = create_session()
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
        delete(f'http://127.0.0.1:5000/api/products/{product_id}')
    return redirect(request.referrer or '/catalog')

@app.route('/admin/product/add_product', methods=['GET', 'POST'])
def add_product():
    form = AddProductForm()
    db_sess = create_session()
    categories = db_sess.query(Category).all()
    form.category_id.choices = [(c.id, c.name) for c in categories]
    if form.validate_on_submit():
        if db_sess.query(Product).filter(Product.name == form.name.data).first():
            return render_template('add_product.html', title='Добавление товара',
                                   form=form,
                                   message="Такой товар уже есть")

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
        if file and file.filename != '':
            ext = file.filename.rsplit('.', 1)[1].lower()
            if ext in ALLOWED_EXTENSIONS:
                filename = f"{product.id}.{ext}"

                file.save(os.path.join(UPLOAD_FOLDER_FOR_AVATARS_PRODUCTS, filename))

                product.image_path = f'static/image/uploads/avatars_products/{filename}'

                db_sess.commit()
        else:
            filename = "default_product_logo.jpg"
            product.image_path = f'static/image/logo/{filename}'
            db_sess.commit()
        return redirect('/')
    return render_template('add_product.html', title='Добавление товара',
                           form=form, categories=categories)



@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")

if __name__ == '__main__':
    app.run()