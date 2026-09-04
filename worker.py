import time
from concurrent.futures import ThreadPoolExecutor

from monitor import (
    check_url,
    get_enabled_urls,
    get_consecutive_failures,
    save_health_check
)


MAX_WORKERS = 5
CHECK_INTERVAL = 1


def run_health_check(url):
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

    print(
        f"[Monitor] {url['name']} "
        f"→ {result['status']} "
        f"({result['response_time']} ms)"
    )


def start_monitoring():
    next_check_times = {}

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:

        print("Background monitoring started.")

        while True:
            current_time = time.time()

            urls = get_enabled_urls()

            active_url_ids = set()

            for url in urls:
                url_id = url["id"]
                active_url_ids.add(url_id)

                interval = url["interval"]

                if interval <= 0:
                    interval = 60

                if (
                    url_id not in next_check_times
                    or current_time >= next_check_times[url_id]
                ):       
                    executor.submit(
                        run_health_check,
                        url
                    )

                    next_check_times[url_id] = (
                        current_time + interval
                    )

            old_ids = set(next_check_times.keys()) - active_url_ids

            for url_id in old_ids:
                del next_check_times[url_id]

            time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    start_monitoring()