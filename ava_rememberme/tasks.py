from ava_rememberme import celery
from ava_rememberme.mail import Mailgun
from celery.result import allow_join_result
import os
import json

EMAIL_DOMAIN = "mg.martinmariano.com"
EMAIL_TEMPLATE_LOCATION = "/home/martin/Documentos/Programming/Python/Projetos/Uninove-RememberMe/ava_rememberme/templates/email/"


@celery.task()
def refreshAllUsers():
    """Refresh the whole database, logging in each user on AVA Platform,
    gathers all disciplines with any assignment or forum with a due date,
    then updates the database.
    """

    from .database_models import Users

    allUsers = Users.get()

    for user in allUsers:
        result = getAllAssignments.apply_async((user.uninove_ra,
                                                user.uninove_senha))
        with allow_join_result():
            materiasList = result.get()

        print('recebeu lista de materias do user')
        print(json.dumps(materiasList))

    return 'done'


@celery.task()
def registerUserChecker(uninove_ra, uninove_senha):
    """Checks if given ra and password can login into uninove ava.

    :param uninove_ra: string
    :param uninove_senha: string
    :returns: dict

    """
    from .engine import AVAscraperFactory
    with AVAscraperFactory.getInstance(debug=True) as scraper:
        scraper.uninove_ra = uninove_ra
        scraper.uninove_senha = uninove_senha
        result = scraper.loginAva()
        return result


@celery.task()
def getAllAssignments(uninove_ra, uninove_senha):
    """Get list of all user disciplines, idCurso and codCurso.

    :param uninove_ra: string
    :param uninove_senha: string
    :returns: dict

    """
    from .engine import AVAscraper
    with AVAscraper(debug=True) as scraper:
        scraper.uninove_ra = uninove_ra
        scraper.uninove_senha = uninove_senha
        scraper.loginAva()
        materiasList = scraper.getMaterias()
        # return materiasList
        for materia in materiasList:
            scraper.getAssignmentsAndForum(materia['IDCurso'],
                                           materia['CodCurso'])


@celery.task()
def emailSendConfirmation(userEmail, userName):
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
    newMail.contentFromFile(EMAIL_TEMPLATE_LOCATION + 'confirmation.html',
                            userName)

    response = newMail.send()

    return response.status_code


@celery.task()
def emailSendDueDates(userEmail, userName, materias):
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
    newMail.subject = 'Você possui {} atividades pendentes.'

    newMail.contentFromFile(EMAIL_TEMPLATE_LOCATION + 'confirmation.html',
                            userName)

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
