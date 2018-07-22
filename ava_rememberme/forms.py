from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Email, Regexp, Length
from wtforms.validators import InputRequired


class RegisterForm(FlaskForm):
    nome = StringField(
        u'Nome',
        validators=[InputRequired(message=u'É necessário escrever seu nome.')],
        render_kw={"placeholder": "Seu Nome"})
    email = StringField(
        'Email',
        validators=[
            DataRequired(),
            Email(message=
                  u'Seu email foi escrito incorretamente, tente novamente.')
        ],
        render_kw={"placeholder": "Email"})
    uninoveRA = StringField(
        u'RA',
        validators=[
            Regexp('^[\d]*$', message=u'Seu RA só deve conter números.'),
            Length(
                max=10,
                message=
                u'Seu RA deve conter no mínimo 9 números, e não deve conter letras.'
            ),
            DataRequired(message=u'É necessário escrever seu RA.')
        ],
        render_kw={"placeholder": "RA UNINOVE"})
    uninoveSenha = PasswordField(
        u'Senha AVA',
        validators=[
            Regexp(
                '^[\d]*$',
                message=u'Sua senha do AVA deve conter somente números.'),
            DataRequired(message=u'É necessário escrever sua senha do AVA.')
        ],
        render_kw={"placeholder": "Senha UNINOVE"})
    termosCondicoes = BooleanField(
        u'Li e aceito o Termo de Responsabilidade descrito abaixo.',
        validators=[
            DataRequired(
                message=u'Você deve ler e aceitar o Termo de Responsabilidade.'
            )
        ])
