"-*- coding: utf-8 -*-"

import datetime
import logging
import re
import traceback
from contextlib import ContextDecorator

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .exceptions import (LoginError, ScraperError, WrongPageError)


class AVAscraperFactory:
    """
    Factory with pool of free to work AVAscraper instances.
    """
    _values = list()
    _CURRENT_INSTANCES = 0
    _MAX_INSTANCES = 1

    @classmethod
    def getInstance(cls, debug=False):
        """Returns instance of AVAscraper.

        :returns: AVAscraper instance.

        """
        if len(cls.
               _values) == 0 and cls._CURRENT_INSTANCES < cls._MAX_INSTANCES:
            cls._values.append(AVAscraper(debug=debug))
            cls._CURRENT_INSTANCES += 1

            if debug:
                print('instanciado!')

        return cls._values.pop()

    @classmethod
    def pushInstance(cls, instance):
        return cls._values.append(instance)


class AVAscraper(ContextDecorator):
    def __init__(self,
                 uninove_ra=None,
                 uninove_senha=None,
                 debug=False,
                 engine="chrome"):
        """
        Initialize selenium driver with simple options.
        """
        self.uninove_ra = uninove_ra
        self.uninove_senha = uninove_senha
        self.TIMEOUT_TIME = 5
        self.TIMEOUT_TIME_LOGIN = 5
        self.TIMEOUT_TIME_MENUTAB = 4
        self.debug = debug
        self.engine = engine
        self.options = None
        self.driver = None

        self.AVA_LOGIN_URL = "https://ava.uninove.br/seu/AVA/index.php"
        self.AVA_MAIN_URL = 'https://ava.uninove.br/seu/AVA/principal.php'
        self.AVA_ATIVIDADE_URL = 'https://ava.uninove.br/seu/AVA/ferramentas/atividade.php'

        if self.engine == "firefox":
            self.options = webdriver.FirefoxOptions()

            if not self.debug:
                self.options.add_argument("headless")

            self.driver = webdriver.Firefox(firefox_options=self.options)

        elif self.engine == "chrome":
            self.options = webdriver.ChromeOptions()

            if not self.debug:
                self.options.add_argument("--headless")
                self.options.add_argument("--disable-gpu")
                self.options.add_argument("--no-sandbox")

            self.driver = webdriver.Chrome(chrome_options=self.options)
        else:
            raise Exception("You need to choose an engine for the webdriver.")

    def loginAva(self):
        """Login into AVA website with user's RA and AVA password.

        :param user: SQLAlchemy User
        :returns: dict
        """

        try:
            self.driver.get(self.AVA_LOGIN_URL)
        except WebDriverException:
            logging.error(traceback.format_exc())
            raise ScraperError(u"Não foi possível entrar no site do AVA")

        username = self.driver.find_element_by_name('user')
        username.send_keys(self.uninove_ra)
        password = self.driver.find_element_by_name('Password')
        password.send_keys(self.uninove_senha)
        password.send_keys(Keys.RETURN)

        try:
            WebDriverWait(self.driver, self.TIMEOUT_TIME_LOGIN).until(
                EC.url_contains(('principal')))
        # something wrong happened on AVA platform
        except TimeoutException:
            raise LoginError(
                self.driver.find_element_by_id('lb_conteudo').text)

    def getMaterias(self, userDisciplines=False):
        """Get all user disciplines IDCurso, CodCurso, Name and if
        it is online or on-site.

        :param userDisciplines: dictionary if user already has disciplines.
        :returns: dictionary with discipline ID, Cod, Name and isOnline.
        :rtype: dict

        """
        if self.debug:
            print(userDisciplines)

        try:
            menuTodasMaterias = WebDriverWait(
                self.driver, self.TIMEOUT_TIME).until(
                    EC.presence_of_element_located((By.ID, 'menu0')))
        except Exception as e:
            raise Exception(e)

        try:
            soup = BeautifulSoup(
                menuTodasMaterias.get_attribute('innerHTML'), "lxml")
        except Exception as e:
            raise Exception(e)

        materiasLista = []
        materiasSoup = soup.find_all("div", {"idcurso": re.compile(r'.*')})

        # Pickle CAN'T handle HTML parser.
        # We need(should) to cast all to primitives.
        for materia in materiasSoup:
            idCurso = int(materia.get('idcurso'))
            codCurso = int(materia.get('codigo'))
            disciplineName = str(materia.select('span.md')[0].string)

            if self.debug:
                print(idCurso)
                print(userDisciplines)
                print(idCurso in userDisciplines)

            if idCurso not in userDisciplines:
                materiasLista.append({
                    'IDCurso': idCurso,
                    'CodCurso': codCurso,
                    'Name': disciplineName
                })

        if self.debug:
            print(materiasLista)

        for materia in materiasLista:
            if self.disciplineIsOnline(materia['IDCurso'],
                                       materia['CodCurso']):
                if self.debug:
                    print("State: Assignment is online.")
                materia.update({'isOnline': True})
            else:
                if self.debug:
                    print("State: Assignment is not online.")
                materia.update({'isOnline': False})

        if self.debug:
            print(materiasLista)
        return materiasLista

    def disciplineIsOnline(self, idCurso, codCurso):
        """Enters inside discipline page, and checks if it has a Atividade tab.

        :param idCurso: ID of user discipline.
        :param codCurso: Cod of user discipline
        :returns: True if discipline has Atividade tab, False if not.
        :rtype: dict

        """
        if self.debug:
            print("Function: disciplineIsOnline")

        # start at main page
        if self.driver.current_url != self.AVA_MAIN_URL:
            try:
                if self.debug:
                    print("Action: Trocando de URL.")

                self.driver.get(self.AVA_MAIN_URL)
                WebDriverWait(self.driver, self.TIMEOUT_TIME).until(
                    EC.presence_of_element_located((By.ID, 'frm-principal')))
            except WebDriverException:
                raise WebDriverException(u'Algo deu errado.')
            except TimeoutException:
                raise WrongPageError(u'Não achou elemento "frm-principal".')

        if self.debug:
            print("Action: preenchendo form.")

        self._fillFormAndSubmit(idCurso, codCurso)

        # checks if it is a discipline page
        try:
            WebDriverWait(self.driver, self.TIMEOUT_TIME).until(
                EC.url_contains(('ferramentas')))
        except TimeoutException:
            raise

        if self.debug:
            try:
                print("State: Trocou de página.")
                print("Action: Imprimindo titulo da disciplina.")
                titulo = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.ID,
                                                    'titulo-disciplina')))
                soup = BeautifulSoup(titulo.get_attribute('innerHTML'), "lxml")
                print(f"Título da matéria: {soup.find('p').string}")
            except TimeoutError:
                raise WrongPageError(
                    u'Não achou elemento "titulo-disciplina".')

        # checks if there is an Atividade tab to choose
        try:
            WebDriverWait(self.driver, self.TIMEOUT_TIME_MENUTAB).until(
                EC.presence_of_element_located((By.ID, 'aba-atividade')))
        except TimeoutException:
            return False
        return True

    def getQuestionarios(self, idCurso, codCurso):
        """Returns user assignments.
        # TODO: foruns

        :returns: name, status, days_left, type
        :rtype: dictionary

        """

        if self.debug:
            print('Página principal..')

        # start at main page
        try:
            self.driver.get(self.AVA_MAIN_URL)
            WebDriverWait(self.driver, self.TIMEOUT_TIME).until(
                EC.presence_of_element_located((By.ID, 'frm-principal')))
        except WebDriverException as e:
            print(e)
            pass
        except TimeoutException:
            raise WrongPageError(u'Não achou elemento "frm-principal".')

        self._fillFormAndSubmit(idCurso, codCurso)

        if self.debug:
            print('Página de matéria EAD')

        # checks if there is an Atividade tab to choose, and then clicks it
        try:
            WebDriverWait(self.driver, self.TIMEOUT_TIME_MENUTAB).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, '#aba-atividade > a:nth-child(1)')))
        except TimeoutException:
            pass

        try:
            atividadeTab = self.driver.find_element_by_css_selector(
                '#aba-atividade > a:nth-child(1)')
            self.driver.execute_script("arguments[0].click();", atividadeTab)

            WebDriverWait(self.driver, 5).until(
                EC.url_to_be((self.AVA_ATIVIDADE_URL)))
        except TimeoutException:
            print(u'Não entrou na TAB de atividade.')
            raise WrongPageError(u'Não entrou na TAB de atividade.')
        except Exception as e:
            print(e)
            print(self.driver.current_url)

        # WebDriverWait(self.driver, 10).until(
        #    EC.url_to_be((self.AVA_LOGIN_URL)))

        if self.debug:
            print('TAB de atividade')

        # checar todos os filtro-conteudo e retirar as atividades abertas
        todosQuestionarios = None
        try:
            todosQuestionarios = WebDriverWait(
                self.driver, self.TIMEOUT_TIME_MENUTAB).until(
                    EC.presence_of_element_located((By.ID, 'div-conteudo')))
        except TimeoutException:
            pass

        atividadesSoup = BeautifulSoup(
            todosQuestionarios.get_attribute('innerHTML'), "lxml")

        # parsing questionaries and forums
        questionarios = atividadesSoup.find_all(
            'div', class_='filtro-conteudo')
        # foruns = atividadesSoup.find_all('div', {'tipo': '003'})

        questionariosList = []
        for questionario in questionarios:

            name = questionario.select('span.marginLeft10')[0].text
            codigo = questionario.find("div",
                                       {"codigo": re.compile(r'.*')})['codigo']
            status = questionario.select('p.sm2.white')[0].text
            datas = re.findall(r'(\d+\/\d+\/\d+)+',
                               questionario.select('div.bloco-data')[0].string)
            daysLeft = datas[1]

            questionariosList.append({
                'name':
                name,
                'codigo':
                codigo,
                'status':
                status,
                'days_left':
                self._formatDateString(daysLeft),
                'type':
                u'Questionário'
            })

        if self.debug:
            print('Questionarios: ')
            print(questionariosList)

        return questionariosList
        # depois pegar seu nome, peso e data de termino

    def _formatDateString(self, assignmentDate):
        """Formats date string to datetime object.

        :param assignmentList: assignmentDate in string format of xx/xx/xxxx.
        :returns: end date of assignment
        :rtype: datetime

        """
        day, month, year = re.findall(r'(\d+)+', assignmentDate)
        finaldate = datetime.datetime(
            int(year), int(month), int(day), 23, 59, 59)
        return finaldate

    def _fillFormAndSubmit(self, idCurso, codCurso):
        """Fill main page form and submits it.

        :param idCurso: int idCurso
        :param codCurso: int codCurso
        :returns:

        """

        form = self.driver.find_element_by_id('frm-principal')
        self.driver.execute_script(
            "arguments[0].setAttribute('action', 'ferramentas/principal.php');",
            form)

        elementIDCurso = self.driver.find_element_by_css_selector(
            '#frm-principal > input:nth-child(1)')
        self.driver.execute_script(
            "arguments[0].setAttribute('value', '{}');".format(idCurso),
            elementIDCurso)

        elementCodCurso = self.driver.find_element_by_css_selector(
            '#frm-principal > input:nth-child(2)')
        self.driver.execute_script(
            "arguments[0].setAttribute('value', '{}');".format(codCurso),
            elementCodCurso)

        form.submit()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        """
        Closes driver.
        """
        # AVAscraperFactory.pushInstance(self)
        self.driver.quit()
        return self
