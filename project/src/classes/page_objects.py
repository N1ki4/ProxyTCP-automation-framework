# pylint: disable=arguments-differ
import re
import logging

import polling
from selenium.common import exceptions

from src.classes.clients import Chrome
from src.classes.mail import Inbox


_log = logging.getLogger(__name__)
_log.setLevel(logging.INFO)


def check_inbox_for_code(mail: str, password: str) -> int:
    sender = "GitHub"
    box = Inbox(mail=mail, password=password)
    box.get_messages()
    message = box.find_last_message_from(sender)
    message_body = message[2]
    code = re.compile(r"Verification code: (\d+)").search(message_body)[1]
    return code


class AuthPage(Chrome):

    _service = "grafana"
    _url = "https://grafana.com/auth/sign-in?plcmt=top-nav&cta=myaccount"
    _success_partial_url = "https://grafana.com/orgs/"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._loghead = f"Chrome@{self._grid_server.name}"

    def get(self) -> None:
        host = self._url
        _log.info(f"{self._loghead} - get URL: {host}")
        try:
            self._driver.get(host)
            _log.info(f"{self._loghead} - loading complete")
        except exceptions.WebDriverException as error:
            self._exceptions.append(error)

    def login(self, mail: str, password: str) -> None:
        # fill login
        _log.info(f"{self._loghead} - {self._url}: LOGIN `{mail}`")
        mail_field = self._driver.find_element_by_name("login")
        mail_field.send_keys(mail)

        # fill password
        _log.info(f"{self._loghead} - {self._url}: PASSWORD `{password}`")
        password_field = self._driver.find_element_by_name("password")
        password_field.send_keys(password)

        # submit
        form = self._driver.find_element_by_tag_name("form")
        form.submit()
        _log.info(f"{self._loghead} - {self._url}: SUBMITED")

    def oauth_login(self, mail: str, password: str, box_password: str) -> None:
        # login via github
        _log.info(f"{self._loghead} - {self._url}: logging in with GITHUB")
        github = self._driver.find_element_by_xpath(
            '//*[@id="root"]/main/div/section/div/button[2]'
        )
        github.click()

        # fill github login
        _log.info(f"{self._loghead} - GitHub: LOGIN `{mail}`")
        mail_field = self._driver.find_element_by_name("login")
        mail_field.send_keys(mail)

        # fill github password
        _log.info(f"{self._loghead} - GitHub: PASSWORD `{password}`")
        password_field = self._driver.find_element_by_name("password")
        password_field.send_keys(password)

        # submit
        form = self._driver.find_element_by_tag_name("form")
        form.submit()
        _log.info(f"{self._loghead} - GitHub: SUBMITED")

        # confirm device if this is the first connection
        if self._service not in self._driver.current_url:
            self.conirm_device(mail, box_password)

    def conirm_device(self, mail: str, box_password: str):
        # get verification code
        _log.info(f"{self._loghead} - GitHub: Device verification code required")
        _log.info(f"{self._loghead} - GitHub: Check {mail} for code")
        code = check_inbox_for_code(mail=mail, password=box_password)

        # fill verification code field
        _log.info(f"{self._loghead} - GitHub: CODE `{code}`")
        code_field = self._driver.find_element_by_class_name("input-block")
        code_field.send_keys(code)

        # submit
        form = self._driver.find_element_by_tag_name("form")
        form.submit()
        _log.info(f"{self._loghead} - GitHub: SUBMITED")

    def check_auth(self) -> bool:
        try:
            polling.poll(
                lambda: self._success_partial_url in self._driver.current_url,
                step=3,
                timeout=30,
            )
        except polling.TimeoutException:
            return False
        return True


class PageForNavigation(Chrome):

    _url = "https://wiki.archlinux.org"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._loghead = f"Chrome@{self._grid_server.name}"

    def get(self) -> None:
        host = self._url
        _log.info(f"{self._loghead} - get URL: {host}")
        try:
            self._driver.get(host)
            _log.info(f"{self._loghead} - loading complete")
        except exceptions.WebDriverException as error:
            self._exceptions.append(error)

    def locate_element_by_xpath_and_click(self, xpath):
        _log.info(
            f"{self._loghead} - {self._driver.current_url}: go to link via `{xpath}`"
        )
        self._driver.find_element_by_xpath(xpath).click()
        _log.info(f"{self._loghead} - {self._driver.current_url}: loaded")

    def is_document_ready(self):
        if self._driver.execute_script("return document.readyState") == "complete":
            return True
        return False


# if __name__ == "__main__":
#     from pyats.topology import loader

#     testbed = loader.load('../testbed.yaml')
#     device = testbed.devices['user-2']
#     proxy = testbed.devices['proxy-vm']


#     with AuthPage(grid_server=device, proxy_server=proxy) as page:
#         page.get()
#         page.login(
#             mail='junkmail.dp.ua@gmail.com',
#             password='OtcVs114aqE'
#         )
#         print(page.check_auth())
#         page.make_screenshot('auth2')

#         # mail='junkmail.dp.ua@gmail.com'
#         # password='OtcVs114aqQ'

#         # code = check_inbox_for_code(mail, password)
#     # with Chrome(grid_server=device, proxy_server=proxy) as chrome:
#     #     chrome.get('https://grafana.com/auth/sign-in?plcmt=top-nav&cta=myaccount')
#     #     chrome.make_screenshot('shit')
