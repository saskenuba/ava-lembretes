import requests
import re


class Mailgun():
    "This class is responsible for creating a mailgun post request, and it"
    "assumes that you have created a subdomain to handle mailgun requests"

    def __init__(self,
                 apikey,
                 subdomain,
                 content=None,
                 subject=None,
                 recipient=None):
        "docstring"
        self.apikey = apikey
        self.subdomain = subdomain
        self.content = content
        self.subject = subject
        self.recipient = recipient

        stripDomain = re.search('(?<=\.).*', self.subdomain)
        self.domain = stripDomain.group(0)

    def contentFromFile(self, filePath, name):
        self.content = setRecipientName(fileToHTML(filePath), name)

    def send(self):
        "returns response object after posting"

        if self.content is None:
            raise Exception("Can't send a NoneType message")

        mailStatus = requests.post(
            "https://api.mailgun.net/v3/{}/messages".format(self.subdomain),
            auth=("api", "{}".format(self.apikey)),
            data={
                "from": "AVA Reminder Me <AVAreminder@{}>".format(self.domain),
                "to": ["{}".format(self.recipient)],
                "subject": "{}".format(self.subject),
                "html": self.content
            })

        return mailStatus


def fileToHTML(filePath):
    """Transforms whole HTML file into a string variable

    :param filePath: file location path.
    :returns: string

    """

    with open(filePath, 'r', encoding='utf-8') as myFile:
        html = myFile.read()

    return html


def setRecipientName(html, name):
    return re.sub('(\$\$_NAME_\$\$)', name, html)


class MailException(Exception):
    """
    Base exception for errors raised by Mail
    """

    def __init__(self, msg=None):
        "docstring"
        self.msg = msg


#class NoMessage(MailException):
