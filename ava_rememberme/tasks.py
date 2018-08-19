import json
import os
import datetime

from celery.result import allow_join_result
from flask import current_app, url_for
from itsdangerous import URLSafeSerializer, URLSafeTimedSerializer

from ava_rememberme import celery

from .exceptions import AssignmentExpired
from .mail import Mailgun

EMAIL_TEMPLATE_LOCATION = "/home/martin/Documentos/Programming/Python/Projetos/Uninove-RememberMe/ava_rememberme/templates/email/"
EMAIL_DOMAIN = "mg.martinmariano.com"
DEBUG = True


@celery.task()
def databaseRefreshAssignments():
    """Refresh the whole database, logging in each user on AVA Platform,
    only for online disiciplines and checks if user has a new assignment,
    then updates the database.
    """

    from .database_models import Users, Assignments
    from .database import db_session

    allUsers = Users.get()

    for user in allUsers:

        # skip cycle if user not confirmed
        if not user.isActive():
            continue

        onlineDisciplines = [
            discipline for discipline in user.disciplines
            if discipline.isOnline is True
        ]

        assignmentList = None
        result = getUserAssignments.apply_async(
            (user.uninove_ra, user.uninove_senha, onlineDisciplines[0].idCurso,
             onlineDisciplines[0].codCurso))

        with allow_join_result():
            assignmentList = result.get()

        for assignment in assignmentList:
            newAssignment = Assignments(user.user_id, assignment['name'],
                                        onlineDisciplines[0].discipline_id,
                                        assignment['type'],
                                        assignment['days_left'])
            db_session.add(newAssignment)
        db_session.commit()

    return 'done'


@celery.task()
def databaseRefreshDisciplines():
    """Refresh the whole database, logging in each user on AVA Platform,
    gathers all disciplines with any assignment or forum with a due date,
    then updates the database.
    """

    from .database_models import Users, Disciplines
    from .database import db_session

    allUsers = Users.get()

    for user in allUsers:
        print(user)

        # skip cycle if user not confirmed
        if not user.isActive():
            continue

        disciplineList = None
        result = getAllDisciplines.apply_async((user.uninove_ra,
                                                user.uninove_senha))
        with allow_join_result():
            disciplineList = result.get()

        # verificar se é a melhor maneira de fazê-lo, as matérias repetem-se para
        # todos os usuários
        for discipline in disciplineList:

            currentDiscipline = Disciplines.query.filter(
                Disciplines.idCurso == discipline['IDCurso']).first()
            # if discipline doesnt exists, then insert and associate user
            if currentDiscipline is None:
                currentDiscipline = Disciplines(user.user_id,
                                                str.title(discipline['Name']),
                                                discipline['isOnline'],
                                                discipline['IDCurso'],
                                                discipline['CodCurso'])
            currentDiscipline.users.append(user)
            db_session.add(currentDiscipline)
            db_session.commit()

    return 'done'


@celery.task()
def registerUserChecker(uninove_ra, uninove_senha):
    """Checks if given ra and password can login into uninove ava.

    :param uninove_ra: string
    :param uninove_senha: string
    :returns: dict

    """
    from .engine import AVAscraper
    with AVAscraper(debug=DEBUG) as scraper:
        scraper.uninove_ra = uninove_ra
        scraper.uninove_senha = uninove_senha
        result = scraper.loginAva()
        return result


@celery.task()
def getUserAssignments(uninove_ra, uninove_senha, idCurso, codCurso):
    """Get list of all user assignments.

    :param uninove_ra: string
    :param uninove_senha: string
    :returns: name, status, days_left, type
    :rtype: dict

    """
    from .engine import AVAscraper
    with AVAscraper(debug=DEBUG) as scraper:
        scraper.uninove_ra = uninove_ra
        scraper.uninove_senha = uninove_senha
        scraper.loginAva()
        questionarios = scraper.getQuestionarios(idCurso, codCurso)

        for questionario in questionarios:
            questionario['days_left'] = datetime.datetime.now(
            ) + datetime.timedelta(days=int(questionario['days_left']))

        return questionarios


@celery.task()
def getAllDisciplines(uninove_ra, uninove_senha):
    """Get all users disciplines and checks if they are on-site or online.

    :param uninove_ra: string, user RA
    :param uninove_senha:string, user AVA password
    :returns:
    :rtype:

    """
    from .engine import AVAscraper
    with AVAscraper(debug=DEBUG) as scraper:
        scraper.uninove_ra = uninove_ra
        scraper.uninove_senha = uninove_senha
        scraper.loginAva()
        materiasList = scraper.getMaterias()
        return materiasList


@celery.task()
def emailSendConfirmation(userEmail, userName, secret):
    """
    Send confirmation email that sign-up was successfull.

    :param userEmail: string with user email.
    :param userName: string with user name.
    :returns:
    :rtype:

    """

    APIKEY = os.environ.get('MAILGUN_API')
    newMail = Mailgun(APIKEY, EMAIL_DOMAIN)
    newMail.recipient = userEmail
    newMail.subject = 'Lembretes configurados com sucesso.'

    emailTemplate = current_app.jinja_env.get_template(
        "/email/confirmation.html")

    newToken = URLSafeTimedSerializer(secret, salt='user-confirmation')
    token = newToken.dumps(userEmail)

    with current_app.app_context(), current_app.test_request_context():
        newMail.content = emailTemplate.render(
            userName=userName,
            action_url=url_for('confirm', token=token, _external=True))

    response = newMail.send()

    return response.status_code


@celery.task()
def emailSendDueDates(userEmail, userName, secret, materias):
    """
    Send email with all user due dates.

    :param userEmail: string with user email.
    :param userName: string with user name.
    :returns:
    :rtype:

    """
    APIKEY = os.environ.get('MAILGUN_API')
    newMail = Mailgun(APIKEY, EMAIL_DOMAIN)
    newMail.recipient = userEmail
    newMail.subject = 'Você possui {} atividades pendentes.'.format(
        len(materias))

    emailTemplate = current_app.jinja_env.get_template(
        "/email/assignments.html")

    newToken = URLSafeSerializer(secret, salt='user-unsubscribe')
    token = newToken.dumps(userEmail)

    with current_app.app_context(), current_app.test_request_context():
        newMail.content = emailTemplate.render(
            userName=userName,
            action_url=url_for('unsubscribe', token=token, _external=True),
            materias=materias)

    response = newMail.send()

    return response.status_code


@celery.task()
def emailNoMoreAssignments(userEmail, userName):
    """
    Send email confirming there are no assignments.

    :param userEmail: string with user email.
    :param userName: string with user name.
    :returns:
    :rtype:

    """
    APIKEY = os.environ.get('MAILGUN_API')
    newMail = Mailgun(APIKEY, EMAIL_DOMAIN)
    newMail.recipient = userEmail
    newMail.subject = 'Não existem mais atividades pendentes.'

    newMail.contentFromFile('./templates/email/confirmation.html', userName)

    response = newMail.send()

    return response.status_code
