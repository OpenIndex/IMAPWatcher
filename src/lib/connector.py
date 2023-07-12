#
# Copyright 2023 OpenIndex.de.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import ssl

from imapclient import IMAPClient

from . import Encryption
from . import EncryptionCertificateCheck


class ImapConnector:
    """
    Holds IMAP configuration and provides a connection method.
    """

    def __init__(
            self,
            host: str = 'localhost',
            port: int = 143,
            username: str | None = None,
            password: str | None = None,
            encryption: Encryption = Encryption.NONE,
            encryption_hostname_check: bool = True,
            encryption_certificate_check: EncryptionCertificateCheck = EncryptionCertificateCheck.REQUIRED,
            encryption_certificate_ca_file: str | None = None,
            use_uid: bool = True,
    ):
        self.__host = host.strip()
        self.__port = port
        self.__username = username.strip() if username else None
        self.__password = password.strip() if password else None
        self.__encryption = encryption
        self.__encryption_hostname_check = encryption_hostname_check
        self.__encryption_certificate_check = encryption_certificate_check
        self.__encryption_certificate_ca_file = encryption_certificate_ca_file.strip() \
            if encryption_certificate_ca_file else None
        self.__use_uid = use_uid

    def __create_client(self) -> IMAPClient:
        """
        Creates an IMAP client.

        :return: the created IMAP client
        """

        is_ssl = self.__encryption == Encryption.SSL

        return IMAPClient(
            self.__host,
            port=self.__port,
            ssl=is_ssl,
            ssl_context=self.__create_ssl_context() if is_ssl else None,
            use_uid=self.__use_uid
        )

    def __create_ssl_context(self) -> ssl.SSLContext | None:
        """
        Creates a SSL context for encryption.
        see https://imapclient.readthedocs.io/en/2.3.1/concepts.html#tls-ssl

        :return: the created SSL context or None, if no SSL encryption is used
        """

        if self.__encryption not in (Encryption.SSL, Encryption.STARTTLS):
            return None

        ssl_context = ssl.create_default_context(cafile=self.__encryption_certificate_ca_file)
        ssl_context.check_hostname = self.__encryption_hostname_check

        if self.__encryption_certificate_check == EncryptionCertificateCheck.REQUIRED:
            ssl_context.verify_mode = ssl.CERT_REQUIRED
        elif self.__encryption_certificate_check == EncryptionCertificateCheck.OPTIONAL:
            ssl_context.verify_mode = ssl.CERT_OPTIONAL
        else:
            ssl_context.verify_mode = ssl.CERT_NONE

        return ssl_context

    def connect(self, select_folder: str | None = None, select_folder_readonly: bool = False) -> IMAPClient:
        """
        Creates an IMAP client according to the provided configuration.

        :param select_folder: if provided, a folder is automatically selected after login
        :param select_folder_readonly: if a folder is automatically selected, it might be used read only
        :return: create IMAP client
        """

        try:
            client = self.__create_client()
        except Exception as ex:
            raise Exception('Can\t create client instance.') from ex

        if self.__encryption == Encryption.STARTTLS:
            try:
                client.starttls(ssl_context=self.__create_ssl_context())
            except Exception as ex:
                raise Exception('STARTTLS encryption failed.') from ex

        if self.__username:
            try:
                client.login(self.__username, self.__password if self.__password else '')
            except Exception as ex:
                raise Exception('Login failed.') from ex

        if select_folder:
            try:
                client.select_folder(select_folder, readonly=select_folder_readonly)
            except Exception as ex:
                raise Exception('Folder selection failed.') from ex

        return client
