from contextlib import ContextDecorator
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import WebDriverException, TimeoutException
from .exceptions import DriverInstanceError, LoginError, ScraperError, WrongPageError
from bs4 import BeautifulSoup
import re
import logging
import traceback


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
        if len(cls._values
               ) == 0 and cls._CURRENT_INSTANCES < cls._MAX_INSTANCES:
            cls._values.append(AVAscraper(debug=debug))
            cls._CURRENT_INSTANCES += 1

            if debug:
                print('instanciado!')

        return cls._values.pop()

    @classmethod
    def pushInstance(cls, instance):
        return cls._values.append(instance)


class AVAscraper(ContextDecorator):
    def __init__(self, uninove_ra=None, uninove_senha=None, debug=False):
        """
        Initialize selenium driver with simple options.
        """
        self.uninove_ra = uninove_ra
        self.uninove_senha = uninove_senha
        self.options = Options()
        self.TIMEOUT_TIME = 5
        self.TIMEOUT_TIME_LOGIN = 5
        self.debug = debug

        self.AVA_LOGIN_URL = "https://ava.uninove.br/seu/AVA/index.php"
        self.AVA_MAIN_URL = 'https://ava.uninove.br/seu/AVA/principal.php'

        if debug:
            self.options.set_headless(headless=False)
        else:
            self.options.set_headless(headless=True)

        self.driver = webdriver.Firefox(firefox_options=self.options)

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
        except TimeoutException:
            return {
                'message': self.driver.find_element_by_id('lb_conteudo').text,
                'code': False
            }

        return {'message': 'Login realizado com sucesso', 'code': True}

    def findChannel(self):
        print("Clicando em channel 9")
        channel9XPATH = "/html/body/div[7]/div[6]/div[2]/div/div[3]/div/div[3]/div[1]/div[2]"
        element = WebDriverWait(self.driver, self.TIMEOUT_TIME).until(
            EC.presence_of_element_located((By.XPATH, channel9XPATH)))

        self.driver.execute_script("arguments[0].click();", element)

        print("Clicando em Atividade")
        abaAtividade = self.driver.find_element_by_id("aba-atividade")
        atividadeChildren = abaAtividade.find_element_by_xpath(
            "/html/body/div[8]/div[6]/div[2]/div[1]/div[4]/div/div/ul/li[2]/a")
        self.driver.execute_script("arguments[0].click();", atividadeChildren)

        print("Verificando data de encerramento")
        diasRestantesXPATH = "/html/body/div[8]/div[6]/div[2]/div/div[6]/div/div/div/div/div/div/div[2]/div[4]/div/div[2]/p"
        element = WebDriverWait(self.driver, self.TIMEOUT_TIME).until(
            EC.presence_of_element_located((By.XPATH, diasRestantesXPATH)))

        return element

    def getMaterias(self):
        """Get all user disciplines IDCurso, CodCurso and Name.

        :returns: dictionary with discipline ID, Cod, and Name.
        :rtype: dict

        """

        try:
            WebDriverWait(self.driver, 5).until(
                EC.url_to_be((self.AVA_MAIN_URL)))
        except WrongPageError:
            raise WrongPageError(
                u'Localização incorreta. Certifique-se da página')

        menuTodasMaterias = WebDriverWait(
            self.driver, self.TIMEOUT_TIME).until(
                EC.presence_of_element_located((By.ID, 'menu0')))

        soup = BeautifulSoup(
            menuTodasMaterias.get_attribute('innerHTML'), "lxml")

        materiasLista = list()
        materiasSoup = soup.find_all("div", {"idcurso": re.compile(r'.*')})

        for materia in materiasSoup:
            materiasLista.append({
                'IDCurso': materia.get('idcurso'),
                'CodCurso': materia.get('codigo'),
                'Nome': materia.select('span')[1].string
            })

        return materiasLista

    def getAssignmentsAndForum(self, idCurso, codCurso):
        """Go to desired discipline assignments page and gathers ones with due dates.
        At the end, go back to main page.

        :param idCurso: ID of user discipline.
        :param codCurso: Cod of user discipline
        :returns: Due dates of user assignments, including forum.
        :rtype: dict

        """

        # start at main page
        if self.driver.current_url != self.AVA_MAIN_URL:
            try:
                self.driver.get(self.AVA_MAIN_URL)
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.ID, 'frm-principal')))
            except WebDriverException:
                pass
            except TimeoutException:
                raise WrongPageError(u'Não achou elemento "frm-principal".')

        self._fillFormAndSubmit(idCurso, codCurso)

        try:
            WebDriverWait(self.driver, 10).until(
                EC.url_contains(('ferramentas')))
        except TimeoutException:
            raise

        if self.debug:
            try:
                titulo = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.ID,
                                                    'titulo-disciplina')))
                soup = BeautifulSoup(titulo.get_attribute('innerHTML'), "lxml")
                print(soup.find('p').string)
            except TimeoutError:
                raise WrongPageError(u'Não achou elemento "titulo-disciplina".')

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


class Discipline(ContextDecorator):
    def __init__(self, idCurso, codCurso):
        "docstring"
        self.idCurso = idCurso
        self.codCurso = codCurso

    def __enter__(self):
        return self

    def __exit__(self, *args):
        """
        Closes driver.
        """
        self.driver.quit()
        return self
