import random
import string
import sys
import requests
import logging
import json
from datetime import datetime
from time import sleep


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
    handlers=[logging.FileHandler("stdout.log"), logging.StreamHandler(sys.stdout)],
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

    accounts = []
    seen_messages = []
    watch = False

    def __init__(self, provider="mail.tm") -> None:
        self.provider = provider
        self.session = requests.Session()
        self.base_url = provider_endpoints[provider]
        self.session.headers = {"Content-Type": "application/json"}

        logger.info("TempMail instantiated, provider: %s", provider)

    def create(self, number_of_accounts=1):
        accs = []
        if self.provider == "mail.tm":
            logger.info("calling create_from_mail_tm method")
            accs = self.create_from_mail_tm(number_of_accounts)
        else:
            raise NotImplementedError(
                f"Provider {self.provider} is not implemented yet."
            )

        return accs

    def create_from_mail_tm(self, number_of_accounts=1):
        domain_endpoint = self.base_url + "/domains"
        domains_res = self.session.get(domain_endpoint)
        domains_res_json = domains_res.json()
        domain = domains_res_json["hydra:member"][0]["domain"]
        logger.info("fetched domain for mail.tm: %s", domain)

        create_endpoint = self.base_url + "/accounts"
        accs = []
        for i in range(number_of_accounts):
            username = generate_random_string(10) + "@" + domain
            password = generate_random_string(10, all_letters=True)

            data = {"address": username.lower(), "password": password}
            logger.info("creating account with the credentials: %s", data)

            res = self.session.post(create_endpoint, json=data)
            res_json = res.json()
            logger.info(
                "json response of creating account for address %s: %s",
                username,
                res_json,
            )

            if res.status_code in [200, 201]:
                data["id"] = res_json["id"]
                accs.append(data)

            logger.info("sleeping 10s for prevent rate limit")
            sleep(10)

        logger.info(
            "creating mail.tm accounts for %s number is done", number_of_accounts
        )
        logger.info("trying to save accounts details in a file")
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        file_name = f"accounts/{timestamp}.json"
        with open(file_name, "w") as file:
            json.dump(accs, file)

        logger.info("accounts details are saved in file: %s", file_name)
        self.accounts = accs
        return accs

    def watch_for_mails(self, interval=10):
        if self.provider == "mail.tm":
            logger.info("calling watch_for_mail_tm method")
            return self.watch_for_mail_tm(interval)
        else:
            raise NotImplementedError(
                f"Provider {self.provider} is not implemented yet."
            )

    def get_mail_tm_token(self, account):
        assert isinstance(account, dict), "Account must be a dictionary"
        assert len(account) >= 2, "Account dictionary must have at least two keys"

        assert "address" in account, "Address key is missing in the Account"
        assert "password" in account, "Password key is missing in the Account"

        token_endpoint = self.base_url + "/token"
        logger.info("requesting auth token for account: %s", account)
        token_res = self.session.post(token_endpoint, json=account)
        try:
            token_res_json = token_res.json()
            token = token_res_json["token"]
            logger.info("token %s is generated for account: %s", token, account)
            return token
        except Exception as e:
            logger.error("couldn't generate token for account: %s", account)
            logger.error("error was: %s", repr(e))
            return None

    def get_mail_tm_message(self, message_id, token):
        message_endpoint = self.base_url + "/messages/" + message_id
        headers = {"Authorization": "Bearer " + token}
        logger.info("fetching message id: %s", message_id)
        message_res = self.session.get(message_endpoint, headers=headers)
        message_res.raise_for_status()

        message_res_json = message_res.json()
        logger.info(
            "fetch successfully message id: %s, with data: %s",
            message_id,
            message_res_json,
        )
        return message_res_json

    def get_mail_tm_messages(self, token):
        messages_endpoint = self.base_url + "/messages"
        logger.info("requesting messages list for token: %s", token)
        headers = {"Authorization": "Bearer " + token}
        messages_list_res = self.session.get(messages_endpoint, headers=headers)
        messages_list_res.raise_for_status()

        messages_list_res_json = messages_list_res.json()

        messages_list = [
            msg
            for i, msg in enumerate(messages_list_res_json["hydra:member"])
            if messages_list_res_json["hydra:member"][i]["id"] not in self.seen_messages
        ]

        logger.info("checking for new messages...")
        new_messages = []
        for message in messages_list:
            message_id = message["id"]
            self.seen_messages.append(message_id)
            new_messages.append(
                self.get_mail_tm_message(message_id=message_id, token=token)
            )
        return new_messages

    def watch_for_mail_tm(self, interval=10):
        if len(self.accounts) == 0:
            logger.error("no accounts found, run create() or add_account() first.")
            raise Exception("no accounts found, run create() or add_account() first.")

        logger.info("setting watch flag to True (starting watch process)")
        self.watch = True
        while self.watch:
            for account in self.accounts:
                mail_tm_token = self.get_mail_tm_token(account=account)

                new_messages = self.get_mail_tm_messages(token=mail_tm_token)

                data_to_yield = {"account": account, "new_messages": new_messages}
                logger.info("yielding message data: %s", data_to_yield)
                yield data_to_yield

                logger.info("sleeping %ss before fetching next messages", interval)
                sleep(interval)

    def stop_watch_for_mails(self):
        logger.info("setting watch flag to False (stopping watch process).")
        self.watch = False
