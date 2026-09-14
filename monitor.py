import time
import requests

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from database import get_connection
from email_alert import (
    HIGH_RESPONSE_TIME,
    send_down_alert,
    send_response_time_alert
)


MAX_WORKERS = 10
REQUEST_TIMEOUT = 10


def check_url(url_id, url, slow_threshold):

    start_time = time.perf_counter()

    try:

        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT
        )

        end_time = time.perf_counter()

        response_time = (
            end_time - start_time
        ) * 1000

        if response_time > slow_threshold * 1000:
            status = "SLOW"
        else:
            status = "UP"

        return {
            "url_id": url_id,
            "status": status,
            "http_status": response.status_code,
            "response_time": round(
                response_time,
                2
            ),
            "error": None
        }

    except requests.exceptions.Timeout:

        end_time = time.perf_counter()

        response_time = (
            end_time - start_time
        ) * 1000

        return {
            "url_id": url_id,
            "status": "FAIL",
            "http_status": None,
            "response_time": round(
                response_time,
                2
            ),
            "error": "Request timed out"
        }

    except requests.exceptions.ConnectionError:

        end_time = time.perf_counter()

        response_time = (
            end_time - start_time
        ) * 1000

        return {
            "url_id": url_id,
            "status": "FAIL",
            "http_status": None,
            "response_time": round(
                response_time,
                2
            ),
            "error": "Connection failed"
        }

    except requests.exceptions.RequestException as error:

        end_time = time.perf_counter()

        response_time = (
            end_time - start_time
        ) * 1000

        return {
            "url_id": url_id,
            "status": "FAIL",
            "http_status": None,
            "response_time": round(
                response_time,
                2
            ),
            "error": str(error)
        }

    except Exception as error:

        end_time = time.perf_counter()

        response_time = (
            end_time - start_time
        ) * 1000

        return {
            "url_id": url_id,
            "status": "FAIL",
            "http_status": None,
            "response_time": round(
                response_time,
                2
            ),
            "error": str(error)
        }


def get_consecutive_failures(url_id):

    connection = get_connection()

    rows = connection.execute(
        """
        SELECT status
        FROM health_checks
        WHERE url_id = ?
        ORDER BY timestamp DESC, id DESC
        LIMIT 3
        """,
        (url_id,)
    ).fetchall()

    connection.close()

    failure_count = 0

    for row in rows:

        if row["status"] in (
            "FAIL",
            "DOWN"
        ):

            failure_count += 1

        else:

            break

    return failure_count


def get_last_status(url_id):

    connection = get_connection()

    row = connection.execute(
        """
        SELECT status
        FROM health_checks
        WHERE url_id = ?
        ORDER BY timestamp DESC, id DESC
        LIMIT 1
        """,
        (url_id,)
    ).fetchone()

    connection.close()

    if row:

        return row["status"]

    return None


def save_health_check(result):

    connection = get_connection()

    connection.execute(
        """
        INSERT INTO health_checks
        (
            url_id,
            timestamp,
            status,
            http_status,
            response_time,
            error
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            result["url_id"],
            datetime.now().isoformat(),
            result["status"],
            result["http_status"],
            result["response_time"],
            result["error"]
        )
    )

    connection.commit()

    connection.close()


def get_enabled_urls():

    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            id,
            url,
            name,
            interval,
            slow_threshold
        FROM urls
        WHERE enabled = 1
        ORDER BY id
        """
    ).fetchall()

    connection.close()

    return rows


def get_latest_down_urls():

    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            u.id,
            u.name,
            u.url,
            h.status,
            h.timestamp
        FROM urls u
        JOIN health_checks h
            ON h.id = (
                SELECT h2.id
                FROM health_checks h2
                WHERE h2.url_id = u.id
                ORDER BY h2.timestamp DESC, h2.id DESC
                LIMIT 1
            )
        WHERE u.enabled = 1
          AND h.status = 'DOWN'
        ORDER BY u.id
        """
    ).fetchall()

    connection.close()

    return rows


def get_latest_slow_urls():

    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            u.id,
            u.name,
            u.url,
            h.status,
            h.response_time,
            h.timestamp
        FROM urls u
        JOIN health_checks h
            ON h.id = (
                SELECT h2.id
                FROM health_checks h2
                WHERE h2.url_id = u.id
                ORDER BY h2.timestamp DESC, h2.id DESC
                LIMIT 1
            )
        WHERE u.enabled = 1
          AND h.status = 'SLOW'
          AND h.response_time > ?
        ORDER BY u.id
        """,
        (
            HIGH_RESPONSE_TIME * 1000,
        )
    ).fetchall()

    connection.close()

    return rows


def send_alerts(
    url,
    result,
    failure_count,
    previous_status,
    send_down_alert_now=True,
    send_response_alert_now=True
):

    if result["status"] == "DOWN":

        if (
            send_down_alert_now
            and failure_count == 3
            and previous_status != "DOWN"
        ):

            send_down_alert(
                url["name"],
                url["url"],
                3
            )

    elif (
        result["response_time"] is not None
        and result["response_time"]
        > HIGH_RESPONSE_TIME * 1000
    ):

        if (
            send_response_alert_now
            and previous_status != "SLOW"
        ):

            send_response_time_alert(
                url["name"],
                url["url"],
                result["response_time"]
            )


def monitor_single_url(
    url,
    send_down_alert_now=True,
    send_response_alert_now=True
):

    previous_status = get_last_status(
        url["id"]
    )

    result = check_url(
        url["id"],
        url["url"],
        url["slow_threshold"]
    )

    failure_count = 0

    if result["status"] == "FAIL":

        failure_count = get_consecutive_failures(
            url["id"]
        )

        if failure_count >= 2:

            result["status"] = "DOWN"

            failure_count += 1

        else:

            failure_count += 1

    send_alerts(
        url,
        result,
        failure_count,
        previous_status,
        send_down_alert_now,
        send_response_alert_now
    )

    save_health_check(
        result
    )

    return (
        url,
        result,
        failure_count
    )


def run_monitoring_cycle():

    urls = get_enabled_urls()

    if not urls:

        print(
            "No enabled URLs found."
        )

        return

    print(
        f"Checking {len(urls)} URLs..."
    )

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:

        future_to_url = {
            executor.submit(
                monitor_single_url,
                url
            ): url
            for url in urls
        }

        for future in as_completed(
            future_to_url
        ):

            url = future_to_url[
                future
            ]

            try:

                _, result, failure_count = (
                    future.result()
                )

                print(
                    f"[Monitor] "
                    f"{url['name']} → "
                    f"{result['status']} "
                    f"({result['response_time']} ms)"
                )

            except Exception as error:

                print(
                    f"[Monitor] "
                    f"{url['name']} → "
                    f"ERROR: {error}"
                )


if __name__ == "__main__":

    run_monitoring_cycle()

    print(
        "Health checks completed successfully."
    )