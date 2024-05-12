import random
import string
import requests
import logging

logging.basicConfig(
    filename="stdout.log",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filemode="a",
    level=logging.DEBUG,
)
logger = logging.getLogger()


def generate_random_string(length, all_letters=False):
    letters = string.ascii_letters
    if all_letters:
        letters += string.digits + string.punctuation
    random_string = "".join(random.choice(letters) for _ in range(length))
    return random_string


provider_endpoints = {"mail.tm": "https://api.mail.tm"}


class TempMail:
    """Base class for creating and woriking with temporary email accounts

    Args:
        provider (str, optional): what provider to use for creating accounts. Defaults to "mail.tm".
    """

    def __init__(self, provider="mail.tm") -> None:
        self.provider = provider
        self.session = requests.Session()
        self.base_url = provider_endpoints[provider]
        self.session.headers = {"Content-Type": "application/json"}

    def create(self, number_of_accounts=1):
        accs = []
        if self.provider == "mail.tm":
            accs = self.create_from_mail_tm(number_of_accounts)

        return accs

    def create_from_mail_tm(self, number_of_accounts=1):
        domain_endpoint = self.base_url + "/domains"
        domains_res = self.session.get(domain_endpoint)
        domains_res_json = domains_res.json()
        domain = domains_res_json["hydra:member"][0]["domain"]

        create_endpoint = self.base_url + "/accounts"
        accs = []
        for i in range(number_of_accounts):
            username = generate_random_string(10) + "@" + domain
            password = generate_random_string(10, all_letters=True)

            data = {"address": username, "password": password}

            res = self.session.post(create_endpoint, json=data)
            res_json = res.json()

            if res.status_code in [200, 201]:
                data["id"] = res_json["id"]
                accs.append(data)

        return accs
