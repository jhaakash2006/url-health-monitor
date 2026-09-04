import unittest
from monitor import check_url


class TestURLMonitor(unittest.TestCase):

    def test_google_is_up(self):
        result = check_url(
            1,
            "https://google.com"
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
            "http://127.0.0.1:59999"
        )

        self.assertIn(
            result["status"],
            ["FAIL", "DOWN"]
        )

        self.assertIsNotNone(
            result["error"]
        )


if __name__ == "__main__":
    unittest.main()