from flask import (current_app, flash, redirect, render_template, request,
                   url_for)
from itsdangerous import (BadSignature, BadTimeSignature, URLSafeSerializer,
                          URLSafeTimedSerializer)
from sqlalchemy.orm.exc import NoResultFound

from ava_rememberme import app
from ava_rememberme.database import db_session
from ava_rememberme.database_models import Profiles, Users
from ava_rememberme.forms import RegisterForm
from ava_rememberme.tasks import (emailSendConfirmation, emailSendDueDates,
                                  getAllAssignments, registerUserChecker)


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
                                            novoUsuario.nome,
                                            current_app.config['SECRET_KEY'])

                flash(
                    u'Um email foi enviado  para {}. Por favor confirme para começar utilizar o serviço.',
                    'success'.format(novoUsuario.email))
                return redirect(url_for('index'))

            # erro da uninove
            flash(result['message'], 'error')
            return redirect(url_for('index'))

        # erro na validação do form
        else:
            flash(form.errors, 'form')
            return redirect(url_for('index'))

    return render_template("register.html", form=form)


@app.route('/confirm/<token>')
def confirm(token):

    # TODO: exceptions with max token age exceeded

    # 24 hours
    TOKEN_MAX_AGE = 60 * 24

    tokenParser = URLSafeTimedSerializer(app.config['SECRET_KEY'])

    userEmail = None
    try:
        userEmail = tokenParser.loads(token, salt='user-confirmation')
        print(userEmail)
    except BadTimeSignature:
        message = "O tempo de espera de 24 horas expirou, foi enviado um novo e-mail de confirmação."
        return render_template(
            'confirmation_status.html', color="red", message=message)
    except BadSignature:
        message = "Algo de errado aconteceu."
        return render_template(
            'confirmation_status.html', color="red", message=message)

    currentUser = Users.query.filter(Users.email == userEmail).first()

    if currentUser is None:
        message = "Usuário não foi encontrado"
        return render_template(
            'confirmation_status.html', color="red", message=message)
    elif currentUser.isActive():
        message = 'Usuário já confirmado'
        return render_template(
            'confirmation_status.html', color="olive", message=message)

    currentUser.activate()
    db_session.commit()

    message = "Usuário confirmado com sucesso."
    return render_template(
        'confirmation_status.html', color="green", message=message)


@app.route('/unsubscribe/<token>')
def unsubscribe(token):

    tokenParser = URLSafeSerializer(app.config['SECRET_KEY'])

    userEmail = None
    try:
        userEmail = tokenParser.loads(token, salt='user-unsubscribe')
        print(userEmail)
    except BadSignature:
        message = "Algo de errado aconteceu."
        return render_template(
            'confirmation_status.html', color="red", message=message)

    currentUser = Users.query.filter(Users.email == userEmail).first()

    if currentUser is None:
        message = "Usuário não foi encontrado"
        return render_template(
            'confirmation_status.html', color="red", message=message)

    currentUser.deactivate()
    db_session.commit()

    return 'hehe'


@app.route('/template')
def testaTemplate():

    teste = URLSafeTimedSerializer(
        app.config['SECRET_KEY'], salt='user-confirmation')
    sent = teste.dumps('martin@hotmail.com.br')

    materias = [{
        'disciplina': 'Desenvolvimento Orientado a objetos',
        'tipo': 'Fórum',
        'nome': 'Herança',
        'dias': '56'
    }, {
        'disciplina': 'Simulação e Estatística',
        'tipo': 'Questionário',
        'nome': 'Central limit Theorem',
        'dias': '30'
    }]

    return render_template(
        '/email/assignments.html',
        materias=materias,
        userName="Fernando Paiva",
        uninove_RA=316105653,
        action_url=url_for('unsubscribe', token=sent, _external=True))


def userWithSettingsCommit(user):

    db_session.add(user)
    db_session.flush()
    settings = Profiles(user.user_id)
    db_session.add(settings)
    db_session.commit()
