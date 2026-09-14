import unittest

from unittest.mock import patch

from monitor import check_url
from email_alert import (
    send_down_alert,
    send_response_time_alert
)


class TestURLMonitor(unittest.TestCase):

    def test_google_is_up(self):

        result = check_url(
            1,
            "https://google.com",
            2
        )

        self.assertIn(
            result["status"],
            ["UP", "SLOW"]
        )

        self.assertEqual(
            result["http_status"],
            200
        )

        self.assertIsNone(
            result["error"]
        )

    def test_invalid_url_fails(self):

        result = check_url(
            2,
            "http://127.0.0.1:59999",
            2
        )

        self.assertEqual(
            result["status"],
            "FAIL"
        )

        self.assertIsNotNone(
            result["error"]
        )

    @patch("email_alert.send_email")
    def test_down_alert(self, mock_send_email):

        mock_send_email.return_value = True

        result = send_down_alert(
            "Test URL",
            "http://test-url.com",
            3
        )

        self.assertTrue(
            result
        )

        mock_send_email.assert_called_once()

    @patch("email_alert.send_email")
    def test_response_time_alert(self, mock_send_email):

        mock_send_email.return_value = True

        result = send_response_time_alert(
            "Slow URL",
            "http://slow-url.com",
            6000
        )

        self.assertTrue(
            result
        )

        mock_send_email.assert_called_once()


if __name__ == "__main__":
    unittest.main()