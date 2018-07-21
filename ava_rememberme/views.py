from ava_rememberme import app, celery
from ava_rememberme.database import db_session
from ava_rememberme.database_models import Users, Profiles
from ava_rememberme.forms import RegisterForm
from ava_rememberme.tasks import registerUserChecker, emailSendConfirmation, getAllAssignments
from flask import render_template, request, flash, redirect, url_for


@app.route('/', methods=('GET', 'POST'))
def index():

    form = RegisterForm()

    if request.method == 'POST':

        if form.validate():
            novoUsuario = Users(form.email.data, form.nome.data,
                                form.uninoveRA.data, form.uninoveSenha.data)

            result = registerUserChecker.delay(
                novoUsuario.uninove_ra, novoUsuario.uninove_senha).get()

            # returns message from user checker
            if result['code']:
                userWithSettingsCommit(novoUsuario)
                emailSendConfirmation.delay(novoUsuario.email,
                                            novoUsuario.nome)

                flash(u'Seu lembrete foi configurado com sucesso.', 'success')
                return redirect(url_for('index'))

            flash(result['message'], 'error')
            return redirect(url_for('index'))

        else:
            flash(form.errors, 'form')
            return redirect(url_for('index'))

    return render_template("register.html", form=form)


@app.route('/hehe')
def register():

    # newUser = Users('martin@hotmail.com.br', 316105653, 111401)
    # userWithSettingsCommit(newUser)
    return render_template("register.html")


@app.route('/materias')
def materias():
    teste = getAllAssignments.delay()

    return 'hehe'


def userWithSettingsCommit(user):

    db_session.add(user)
    db_session.flush()
    settings = Profiles(user.user_id)
    db_session.add(settings)
    db_session.commit()
