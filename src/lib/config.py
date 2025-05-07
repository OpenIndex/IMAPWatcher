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

import logging
import os
import sys
from configparser import ConfigParser

from . import Encryption, EncryptionCertificateCheck
from .callback import CallbackHandler
from .connector import ImapConnector
from .idle import ImapIdleHandler


def get_config(logger: logging.Logger) -> ConfigParser | None:
    if len(sys.argv) < 2:
        logger.error('Please provide a config file as first argument!')
        return None

    config_path = sys.argv[1]
    if not os.path.isfile(config_path):
        logger.error('Can\'t find config file at "%s"!' % config_path)
        return None

    config = ConfigParser()
    config.read(config_path)
    return config


def get_imap_folder(
        config: ConfigParser,
        section: str
) -> str:
    return config.get(
        section, 'folder',
        fallback='INBOX',
    )


def create_callback_handler(
        config: ConfigParser,
        section: str
) -> CallbackHandler:
    env = {}
    for option in config.options(section):
        if not option.upper().startswith('ENV_'):
            continue
        env[option[4:].upper().strip()] = config.get(section, option).strip()

    return CallbackHandler(
        name=section,
        on_new_message=config.get(
            section, 'on_new_message',
            fallback=None,
        ),
        additional_env=env,
    )


def create_imap_connector(
        config: ConfigParser,
        section: str,
        use_uid=False
) -> ImapConnector:
    try:
        port: int = int(config.get(
            section, 'port',
            fallback='143',
        ).strip())
    except ValueError:
        raise Exception('Can\'t read port number "%s".' % config.get(section, 'port'))

    return ImapConnector(
        host=config.get(
            section, 'host',
            fallback='localhost',
        ),
        port=port,
        username=config.get(
            section, 'username',
            fallback=None,
        ),
        password=config.get(
            section, 'password',
            fallback=None,
        ),
        encryption=config.get(
            section, 'encryption',
            fallback=Encryption.NONE,
        ),
        encryption_hostname_check=config.get(
            section, 'encryption_hostname_check',
            fallback='1',
        ).strip().lower() in ('1', 'true'),
        encryption_certificate_check=config.get(
            section, 'encryption_certificate_check',
            fallback=EncryptionCertificateCheck.REQUIRED,
        ),
        encryption_certificate_ca_file=config.get(
            section, 'encryption_certificate_ca_file',
            fallback=None,
        ),
        use_uid=use_uid,
    )


def create_imap_idle_handler(
        config: ConfigParser,
        section: str,
        connector: ImapConnector,
        callback: CallbackHandler
) -> ImapIdleHandler:
    return ImapIdleHandler(
        name=section,
        connector=connector,
        callback=callback,
        folder=get_imap_folder(config=config, section=section),
        ignoreRecentFlag=config.get(section, 'ignore_recent_flag', fallback='0').strip().lower() in ('1', 'true'),
    )
