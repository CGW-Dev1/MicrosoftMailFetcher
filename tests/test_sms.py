from __future__ import annotations

import unittest
from unittest import mock

import requests

from mail_fetcher.models import PhoneRecord
from mail_fetcher.services import SmsService


class FakeResponse:
    def __init__(self, payload: object, status_code: int = 200) -> None:
        self.payload = payload
        self.status_code = status_code
        self.text = ""
        self.headers: dict[str, str] = {}

    def json(self) -> object:
        return self.payload


class SmsServiceTests(unittest.TestCase):
    def test_sms8_payload_extracts_code_and_dates(self) -> None:
        response = FakeResponse(
            {
                "code": 1,
                "msg": "ok",
                "data": {
                    "code": "Your OTP is 845538",
                    "code_time": "2026-07-16 18:30:00",
                    "expired_date": "2026-08-25 00:00:00",
                },
            }
        )
        service = SmsService()
        with mock.patch.object(service, "_request", return_value=response):
            row = service.fetch_phone_row(
                PhoneRecord(phone="+6287763590795", api_url="https://api.sms8.net/api/record?token=test", emails=[]),
                concise_mode=False,
            )

        self.assertEqual(row["code"], "845538")
        self.assertEqual(row["code_time"], "2026-07-16 18:30:00")
        self.assertEqual(row["expired_date"], "2026-08-25 00:00:00")
        self.assertEqual(row["sms_content"], "Your OTP is 845538")

    def test_connection_failure_retries_without_environment_proxy(self) -> None:
        primary = mock.Mock()
        primary.get.side_effect = requests.exceptions.ConnectionError("primary failed")
        direct = mock.Mock()
        direct.get.return_value = FakeResponse({"code": 1, "msg": "ok", "data": {"code": "123456"}})

        with mock.patch(
            "mail_fetcher.services.sms_http_session",
            side_effect=lambda direct=False: direct_session if direct else primary,
        ):
            direct_session = direct
            response = SmsService()._request("https://api.sms8.net/api/record?token=secret")

        self.assertEqual(response.status_code, 200)
        primary.get.assert_called_once()
        direct.get.assert_called_once()

    def test_connection_failure_hides_token_and_low_level_error(self) -> None:
        primary = mock.Mock()
        direct = mock.Mock()
        primary.get.side_effect = requests.exceptions.ConnectionError("token=secret Max retries exceeded")
        direct.get.side_effect = requests.exceptions.ConnectionError("token=secret Max retries exceeded")

        with mock.patch(
            "mail_fetcher.services.sms_http_session",
            side_effect=lambda direct=False: direct_session if direct else primary,
        ):
            direct_session = direct
            with self.assertRaises(RuntimeError) as context:
                SmsService()._request("https://api.sms8.net/api/record?token=secret")

        message = str(context.exception)
        self.assertIn("无法连接短信 API", message)
        self.assertNotIn("secret", message)
        self.assertNotIn("Max retries exceeded", message)

    def test_invalid_api_url_is_rejected_before_request(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "地址无效"):
            SmsService()._request("api.sms8.net/api/record")


if __name__ == "__main__":
    unittest.main()
