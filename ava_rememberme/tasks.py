import datetime
import json
import os

from celery import current_task
from celery.result import allow_join_result
from celery.utils.log import get_task_logger
from flask import current_app, url_for
from itsdangerous import URLSafeSerializer, URLSafeTimedSerializer

from ava_rememberme import celery

from .engine.exceptions import LoginError
from .exceptions import AssignmentExpired
from .mail import Mailgun

EMAIL_TEMPLATE_LOCATION = "/home/martin/Documentos/Programming/Python/Projetos/Uninove-RememberMe/ava_rememberme/templates/email/"
EMAIL_DOMAIN = "mg.martinmariano.com"
DEBUG = True

logger = get_task_logger(__name__)

@celery.task(ignore_result=True)
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

        # if user doesnt has any discipline
        if user.Disciplines is None or not user.Disciplines:
            continue

        onlineDisciplines = [
            discipline for discipline in user.Disciplines
            if discipline.isOnline is True
        ]

        userAssignments = getUserAssignments.apply_async(
            (user.uninove_ra, user.uninove_senha, onlineDisciplines[0].idCurso,
             onlineDisciplines[0].codCurso))

        assignmentList = None
        with allow_join_result():
            assignmentList = userAssignments.get()

        for assignment in assignmentList:
            currentAssignment = Assignments.query.filter(
                Assignments.codigo == assignment['codigo']).first()

            # caso não exista, crie um assignment
            if currentAssignment is None:
                currentAssignment = Assignments(
                    assignment['name'], assignment['codigo'],
                    onlineDisciplines[0].discipline_id, assignment['type'],
                    assignment['days_left'])

            # independente, associe à um usuário, e somente se aberta
            user.assignments.append([currentAssignment, assignment['status']])
            db_session.add(currentAssignment)
            print('inseriu')

        db_session.commit()
    return 'done'


@celery.task(ignore_result=True)
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
                                                user.uninove_senha, Users.getIDcursoList(user)))
        with allow_join_result():
            disciplineList = result.get()

        # user with error on login, or if no new disciplines are found
        if not disciplineList:
            continue

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
def databaseSendDueDates():
    """FIXME! briefly describe function

    :returns:
    :rtype:

    """

    from .database_models import Users

    allUsers = Users.get()

    for user in allUsers:

        # skip cycle if user not confirmed
        if not user.isActive():
            continue

        for assignment in user.assignments:
            print(assignment)
        print()


@celery.task()
def registerUserChecker(uninove_ra, uninove_senha):
    """Checks if given ra and password can login into uninove ava.

    :param uninove_ra: string
    :param uninove_senha: string
    :returns: tuple, [0] True or False, [1] message

    """
    from .engine import AVAscraper
    with AVAscraper(debug=DEBUG) as scraper:
        scraper.uninove_ra = uninove_ra
        scraper.uninove_senha = uninove_senha
        try:
            scraper.loginAva()
        except LoginError as e:
            return (False, e.msg)
        return (True,)


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
def getAllDisciplines(uninove_ra, uninove_senha, userDisciplines=False):
    """Get all users disciplines and checks if they are on-site or online.

    :param uninove_ra: string, user RA
    :param uninove_senha:string, user AVA password
    :returns: List with all users disciplines, False if there was a login error.
    :rtype: list

    """
    from .engine import AVAscraper
    with AVAscraper(debug=DEBUG) as scraper:
        scraper.uninove_ra = uninove_ra
        scraper.uninove_senha = uninove_senha
        try:
            scraper.loginAva()
        except LoginError as e:
            return False
        materiasList = scraper.getMaterias(userDisciplines)
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

    :param userEmail: string with user email.
    :param userName: string with user name.
    :param secret: flask config secret
    :param materias:
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
