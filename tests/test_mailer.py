from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from mailer import load_mail_config


class MailerTests(unittest.TestCase):
    def test_load_mail_config_returns_none_when_incomplete(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(load_mail_config())

    def test_load_mail_config_reads_recipients_and_ssl(self) -> None:
        env = {
            "SMTP_HOST": "smtp.example.com",
            "SMTP_PORT": "465",
            "SMTP_USER": "sender@example.com",
            "SMTP_PASSWORD": "secret",
            "MAIL_TO": "a@example.com, b@example.com",
        }
        with patch.dict(os.environ, env, clear=True):
            config = load_mail_config()

        self.assertIsNotNone(config)
        assert config is not None
        self.assertEqual(config.recipients, ("a@example.com", "b@example.com"))
        self.assertTrue(config.use_ssl)


if __name__ == "__main__":
    unittest.main()
