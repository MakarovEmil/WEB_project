import os
from flask import Flask
from flask import render_template
from data.users import User
from data.db_session import global_init, create_session
from data.forms.registration import RegisterForm
from data.forms.login import LoginForm
from flask import redirect
from flask_login import LoginManager, login_user, logout_user, login_required
from flask import request
from flask_restful import Api
from data.api import user_resources

UPLOAD_FOLDER_FOR_AVATARS_USERS = 'static/image/uploads/avatars_users/'
UPLOAD_FOLDER_FOR_AVATARS_PRODUCTS = 'static/image/uploads/avatars_products/'
ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif']

SECRET_KEY_FOR_ADMINS = 'вкусные семечки'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

api = Api(app)
api.add_resource(user_resources.UsersListResource, '/api/users')
api.add_resource(user_resources.UsersResource, '/api/users/<int:user_id>')


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

                # Сохраняем файл
                file.save(os.path.join(UPLOAD_FOLDER_FOR_AVATARS_USERS, filename))

                # Обновляем путь в БД
                user.image_path = f'static/image/uploads/avatars/{filename}'

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


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")

if __name__ == '__main__':
    app.run()