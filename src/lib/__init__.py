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
import sys
from datetime import datetime
from enum import Enum

from imapclient.response_types import Address, Envelope


class Encryption(Enum):
    NONE = 'none'
    SSL = 'ssl'
    STARTTLS = 'starttls'


class EncryptionCertificateCheck(Enum):
    NONE = 'none'
    OPTIONAL = 'optional'
    REQUIRED = 'required'


__LOGGERS: dict[str, logging.Logger] = {}


def create_logger(name: str = 'app', level: int = logging.INFO) -> logging.Logger:
    if name in __LOGGERS:
        return __LOGGERS[name]

    logger: logging.Logger = logging.getLogger(name)
    logger.setLevel(level)

    # noinspection SpellCheckingInspection
    logger_format = '[%(levelname)s] %(asctime)s | %(message)s' if name == 'app' \
        else '[%(levelname)s:%(name)s] %(asctime)s | %(message)s'
    formatter: logging.Formatter = logging.Formatter(
        fmt=logger_format,
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    handler: logging.StreamHandler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    __LOGGERS[name] = logger
    return logger


def get_address_mail(address: Address, charset='utf-8') -> str | None:
    """
    Extracts mail address from an address.

    :param address: address
    :param charset: charset used to decode the address value
    :return: mail address or None, if invalid
    """

    if address.host is None or address.mailbox is None:
        return None

    return '%s@%s' % (
        address.mailbox.decode(charset).strip(),
        address.host.decode(charset).strip()
    )


def get_address_name(address: Address, charset='utf-8') -> str | None:
    """
    Extracts mail name from an address.

    :param address: address
    :param charset: charset used to decode the address value
    :return: mail name or None, if invalid
    """

    if not address.name:
        return None

    return address.name.decode(charset).strip()


def get_envelope_date(envelope: Envelope) -> datetime | None:
    """
    Get "Date" value from an envelope.

    :param envelope: envelope
    :return: first "Date" value or None, if not available
    """

    value: datetime | None = envelope.date
    return value if value else None


def get_envelope_subject(envelope: Envelope, charset='utf-8') -> str | None:
    """
    Get "Subject" value from an envelope.

    :param envelope: envelope
    :param charset: charset used to decode the header value
    :return: "Subject" value or None, if not available
    """

    values: bytes | None = envelope.subject
    return values.decode(charset) if values else None


def get_envelope_message_id(envelope: Envelope, charset='utf-8') -> str | None:
    """
    Get "Message-Id" value from an envelope.

    :param envelope: envelope
    :param charset: charset used to decode the header value
    :return: "Message-Id" value or None, if not available
    """

    values: bytes | None = envelope.message_id
    return values.decode(charset) if values else None


def get_envelope_in_reply_to(envelope: Envelope, charset='utf-8') -> str | None:
    """
    Get "In-Reply-To" value from an envelope.

    :param envelope: envelope
    :param charset: charset used to decode the header value
    :return: "In-Reply-To" value or None, if not available
    """

    values: bytes | None = envelope.in_reply_to
    return values.decode(charset) if values else None


def get_envelope_from(envelope: Envelope) -> tuple[Address]:
    """
    Get "From" addresses from an envelope.

    :param envelope: envelope
    :return: all "From" addresses
    """

    values: tuple[Address] | None = envelope.from_
    return values if values else ()


def get_envelope_from_first(envelope: Envelope) -> Address | None:
    """
    Get first "From" address from an envelope.

    :param envelope: envelope
    :return: first "From" address or None, if not available
    """

    values: tuple[Address] = get_envelope_from(envelope)
    return values[0] if len(values) > 0 else None


def get_envelope_sender(envelope: Envelope) -> tuple[Address]:
    """
    Get "Sender" addresses from an envelope.

    :param envelope: envelope
    :return: all "Sender" addresses
    """

    values: tuple[Address] | None = envelope.sender
    return values if values else ()


def get_envelope_sender_first(envelope: Envelope) -> Address | None:
    """
    Get first "Sender" address from an envelope.

    :param envelope: envelope
    :return: first "Sender" address or None, if not available
    """

    values: tuple[Address] = get_envelope_sender(envelope)
    return values[0] if values and len(values) > 0 else None


def get_envelope_reply_to(envelope: Envelope) -> tuple[Address]:
    """
    Get "Reply-To" addresses from an envelope.

    :param envelope: envelope
    :return: all "Reply-To" addresses
    """

    values: tuple[Address] | None = envelope.reply_to
    return values if values else ()


def get_envelope_reply_to_first(envelope: Envelope) -> Address | None:
    """
    Get first "Reply-To" address from an envelope.

    :param envelope: envelope
    :return: first "Reply-To" address or None, if not available
    """

    values: tuple[Address] = get_envelope_reply_to(envelope)
    return values[0] if values and len(values) > 0 else None


def get_envelope_to(envelope: Envelope) -> tuple[Address]:
    """
    Get "To" addresses from an envelope.

    :param envelope: envelope
    :return: all "To" addresses
    """

    values: tuple[Address] | None = envelope.to
    return values if values else ()


def get_envelope_to_first(envelope: Envelope) -> Address | None:
    """
    Get first "To" address from an envelope.

    :param envelope: envelope
    :return: first "To" address or None, if not available
    """

    values: tuple[Address] = get_envelope_to(envelope)
    return values[0] if values and len(values) > 0 else None


def get_envelope_cc(envelope: Envelope) -> tuple[Address]:
    """
    Get "Cc" addresses from an envelope.

    :param envelope: envelope
    :return: all "Cc" addresses
    """

    values: tuple[Address] | None = envelope.to
    return values if values else ()


def get_envelope_cc_first(envelope: Envelope) -> Address | None:
    """
    Get first "Cc" address from an envelope.

    :param envelope: envelope
    :return: first "Cc" address or None, if not available
    """

    values: tuple[Address] = get_envelope_cc(envelope)
    return values[0] if values and len(values) > 0 else None


def get_envelope_bcc(envelope: Envelope) -> tuple[Address]:
    """
    Get "Bcc" addresses from an envelope.

    :param envelope: envelope
    :return: all "Bcc" addresses
    """

    values: tuple[Address] | None = envelope.to
    return values if values else ()


def get_envelope_bcc_first(envelope: Envelope) -> Address | None:
    """
    Get first "Bcc" address from an envelope.

    :param envelope: envelope
    :return: first "Bcc" address or None, if not available
    """

    values: tuple[Address] = get_envelope_bcc(envelope)
    return values[0] if values and len(values) > 0 else None
