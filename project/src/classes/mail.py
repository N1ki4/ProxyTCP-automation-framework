import email
import imaplib


class Inbox:

    _server = "imap.gmail.com"

    def __init__(self, mail: str, password: str):
        self._mail = imaplib.IMAP4_SSL(self._server)
        self._mail.login(mail, password)
        self._messages = None

    def get_messages(self):
        messages = []

        self._mail.select("inbox")
        _, data = self._mail.search(None, "ALL")

        message_ids = []
        for entry in data:
            message_ids += entry.split()

        for entry in message_ids:
            mail_from = None
            mail_subject = None
            mail_content = None

            _, data = self._mail.fetch(entry, "(RFC822)")
            for response_part in data:
                if isinstance(response_part, tuple):
                    message = email.message_from_bytes(response_part[1])
                    mail_from = message["from"]
                    mail_subject = message["subject"]
                    if message.is_multipart():
                        mail_content = ""
                        for part in message.get_payload():
                            if part.get_content_type() == "text/plain":
                                mail_content += part.get_payload()
                    else:
                        mail_content = message.get_payload()
            messages.append((mail_from, mail_subject, mail_content))
        self._messages = messages
        self._messages.reverse()
        return True if self._messages else False

    def find_last_message_from(self, sender: str):
        filtered_list = list(filter(lambda x: sender in x[0], self._messages))
        if filtered_list:
            return filtered_list[0]
