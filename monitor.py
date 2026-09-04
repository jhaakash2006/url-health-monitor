import time
import requests

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from database import get_connection


MAX_WORKERS = 10
REQUEST_TIMEOUT = 10


def check_url(url_id, url):
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

        if response_time > 2000:
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
        ORDER BY timestamp DESC
        LIMIT 3
        """,
        (url_id,)
    ).fetchall()

    connection.close()

    failure_count = 0

    for row in rows:

        if row["status"] == "FAIL":
            failure_count += 1
        else:
            break

    return failure_count


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
        SELECT id, url, name, interval
        FROM urls
        WHERE enabled = 1
        ORDER BY id
        """
    ).fetchall()

    connection.close()

    return rows


def monitor_single_url(url):
    result = check_url(
        url["id"],
        url["url"]
    )

    if result["status"] == "FAIL":

        failure_count = get_consecutive_failures(
            url["id"]
        )

        if failure_count >= 2:
            result["status"] = "DOWN"

    save_health_check(result)

    return url, result


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

                _, result = future.result()

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