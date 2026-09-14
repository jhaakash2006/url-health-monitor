import time
from concurrent.futures import ThreadPoolExecutor

from monitor import (
    get_enabled_urls,
    monitor_single_url,
    get_latest_down_urls,
    get_latest_slow_urls
)

from email_alert import (
    send_combined_down_alert,
    send_combined_response_time_alert
)


MAX_WORKERS = 5
CHECK_INTERVAL = 1
ALERT_INTERVAL = 600


alerted_down_urls = set()
alerted_slow_urls = set()


def run_health_check(url):

    _, result, failure_count = monitor_single_url(
        url,
        send_down_alert_now=False,
        send_response_alert_now=False
    )

    print(
        f"[Monitor] {url['name']} "
        f"→ {result['status']} "
        f"({result['response_time']} ms)"
    )


def send_combined_alerts():

    global alerted_down_urls
    global alerted_slow_urls

    down_urls = get_latest_down_urls()

    slow_urls = get_latest_slow_urls()

    current_down_ids = set()

    for url in down_urls:

        current_down_ids.add(
            url["id"]
        )

    alerted_down_urls.intersection_update(
        current_down_ids
    )

    new_down_urls = []

    for url in down_urls:

        if url["id"] not in alerted_down_urls:

            new_down_urls.append(
                {
                    "name": url["name"],
                    "url": url["url"],
                    "failure_count": 3
                }
            )

            alerted_down_urls.add(
                url["id"]
            )

    if new_down_urls:

        send_combined_down_alert(
            new_down_urls
        )

    else:

        if down_urls:

            print(
                "[Email Alert] "
                "DOWN URLs already alerted."
            )

        else:

            print(
                "[Email Alert] "
                "No DOWN URLs found."
            )

    current_slow_ids = set()

    for url in slow_urls:

        current_slow_ids.add(
            url["id"]
        )

    alerted_slow_urls.intersection_update(
        current_slow_ids
    )

    new_slow_urls = []

    for url in slow_urls:

        if url["id"] not in alerted_slow_urls:

            new_slow_urls.append(
                {
                    "name": url["name"],
                    "url": url["url"],
                    "response_time": url["response_time"]
                }
            )

            alerted_slow_urls.add(
                url["id"]
            )

    if new_slow_urls:

        send_combined_response_time_alert(
            new_slow_urls
        )

    else:

        if slow_urls:

            print(
                "[Email Alert] "
                "High Response Time URLs "
                "already alerted."
            )

        else:

            print(
                "[Email Alert] "
                "No High Response Time URLs found."
            )


def start_monitoring():

    next_check_times = {}

    last_alert_time = time.time()

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:

        print(
            "Background monitoring started."
        )

        while True:

            current_time = time.time()

            urls = get_enabled_urls()

            active_url_ids = set()

            for url in urls:

                url_id = url["id"]

                active_url_ids.add(
                    url_id
                )

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

            old_ids = (
                set(next_check_times.keys())
                - active_url_ids
            )

            for url_id in old_ids:

                del next_check_times[
                    url_id
                ]

            if (
                current_time - last_alert_time
                >= ALERT_INTERVAL
            ):

                print(
                    "[Email Alert] "
                    "Preparing combined alerts..."
                )

                send_combined_alerts()

                last_alert_time = current_time

            time.sleep(
                CHECK_INTERVAL
            )


if __name__ == "__main__":

    start_monitoring()