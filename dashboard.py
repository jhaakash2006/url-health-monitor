import sqlite3
import streamlit as st
from pathlib import Path
from datetime import datetime


DATABASE = Path(__file__).resolve().parent / "monitor.db"


st.set_page_config(
    page_title="URL Health Monitor",
    page_icon="🌐",
    layout="wide"
)


def get_connection():
    connection = sqlite3.connect(
        str(DATABASE),
        check_same_thread=False
    )

    connection.row_factory = sqlite3.Row

    return connection


def get_urls():
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            u.id,
            u.name,
            u.url,
            u.enabled,
            u.interval,
            h.status,
            h.http_status,
            h.response_time,
            h.error,
            h.timestamp
        FROM urls u
        LEFT JOIN health_checks h
        ON h.id = (
            SELECT id
            FROM health_checks
            WHERE url_id = u.id
            ORDER BY timestamp DESC
            LIMIT 1
        )
        ORDER BY u.id
        """
    ).fetchall()

    connection.close()

    return rows


def get_statistics(url_id):
    connection = get_connection()

    statistics = connection.execute(
        """
        SELECT
            COUNT(*) AS total_checks,

            SUM(
                CASE
                    WHEN status = 'UP'
                    OR status = 'SLOW'
                    THEN 1
                    ELSE 0
                END
            ) AS successful_checks,

            SUM(
                CASE
                    WHEN status = 'FAIL'
                    OR status = 'DOWN'
                    THEN 1
                    ELSE 0
                END
            ) AS failed_checks,

            AVG(response_time) AS average_response_time,

            MIN(response_time) AS minimum_response_time,

            MAX(response_time) AS maximum_response_time

        FROM health_checks
        WHERE url_id = ?
        """,
        (url_id,)
    ).fetchone()

    connection.close()

    return statistics


def get_history(url_id):
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            timestamp,
            status,
            http_status,
            response_time,
            error
        FROM health_checks
        WHERE url_id = ?
        ORDER BY timestamp DESC
        LIMIT 20
        """,
        (url_id,)
    ).fetchall()

    connection.close()

    return rows


def add_url(name, url, interval):
    connection = get_connection()

    connection.execute(
        """
        INSERT INTO urls
        (
            name,
            url,
            enabled,
            interval
        )
        VALUES (?, ?, 1, ?)
        """,
        (
            name,
            url,
            interval
        )
    )

    connection.commit()
    connection.close()


def delete_url(url_id):
    connection = get_connection()

    connection.execute(
        """
        DELETE FROM health_checks
        WHERE url_id = ?
        """,
        (url_id,)
    )

    connection.execute(
        """
        DELETE FROM urls
        WHERE id = ?
        """,
        (url_id,)
    )

    connection.commit()
    connection.close()


def toggle_url(url_id, enabled):
    connection = get_connection()

    connection.execute(
        """
        UPDATE urls
        SET enabled = ?
        WHERE id = ?
        """,
        (
            1 if enabled else 0,
            url_id
        )
    )

    connection.commit()
    connection.close()


def get_status_text(status):
    if status == "UP":
        return "🟢 UP"

    if status == "SLOW":
        return "🟡 SLOW"

    if status == "DOWN":
        return "🔴 DOWN"

    if status == "FAIL":
        return "🔴 FAIL"

    return "⚪ UNKNOWN"


@st.fragment(run_every="10s")
def live_dashboard():

    urls = get_urls()

    total_urls = len(urls)

    healthy_urls = 0
    down_urls = 0

    for url in urls:

        status = url["status"]

        if status in ("UP", "SLOW"):
            healthy_urls += 1

        elif status == "DOWN":
            down_urls += 1

    st.title("URL Health Monitor")

    st.caption(
        "Live monitoring dashboard"
    )

    st.write(
        "Last dashboard refresh:",
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Total URLs",
            total_urls
        )

    with col2:
        st.metric(
            "Healthy URLs",
            healthy_urls
        )

    with col3:
        st.metric(
            "Down URLs",
            down_urls
        )

    st.divider()

    st.subheader("URL Status")

    if not urls:

        st.info(
            "No URLs have been configured yet."
        )

    for url in urls:

        status = get_status_text(
            url["status"]
        )

        response_time = url["response_time"]

        if response_time is None:
            response_text = "-"

        else:
            response_text = (
                f"{response_time:.2f} ms"
            )

        http_status = url["http_status"]

        if http_status is None:
            http_text = "-"

        else:
            http_text = str(
                http_status
            )

        if url["enabled"]:
            monitoring = "🟢 Monitoring Enabled"
        else:
            monitoring = "⚪ Monitoring Disabled"

        with st.container(border=True):

            col1, col2, col3, col4 = st.columns(
                [2, 4, 2, 2]
            )

            with col1:

                st.write("Name")

                st.write(
                    url["name"]
                )

            with col2:

                st.write("URL")

                st.write(
                    url["url"]
                )

            with col3:

                st.write("Status")

                st.write(
                    status
                )

            with col4:

                st.write("Response Time")

                st.write(
                    response_text
                )

            col5, col6, col7 = st.columns(3)

            with col5:

                st.write(
                    f"HTTP Status: {http_text}"
                )

            with col6:

                st.write(
                    monitoring
                )

            with col7:

                st.write(
                    f"Interval: {url['interval']} seconds"
                )

            if url["error"]:

                st.error(
                    f"Error: {url['error']}"
                )

            if url["timestamp"]:

                st.caption(
                    f"Last check: {url['timestamp']}"
                )

            action1, action2, action3 = st.columns(3)

            with action1:

                if st.button(
                    "Delete",
                    key=f"delete_{url['id']}"
                ):

                    st.session_state[
                        f"confirm_delete_{url['id']}"
                    ] = True

                if st.session_state.get(
                    f"confirm_delete_{url['id']}",
                    False
                ):

                    st.warning(
                        f"Are you sure you want to delete "
                        f"'{url['name']}'?"
                    )

                    confirm_col, cancel_col = st.columns(2)

                    with confirm_col:

                        if st.button(
                            "Yes, Delete",
                            key=f"confirm_{url['id']}"
                        ):

                            delete_url(
                                url["id"]
                            )

                            st.session_state[
                                f"confirm_delete_{url['id']}"
                            ] = False

                            if st.session_state.get(
                                "selected_url"
                            ) == url["id"]:

                                st.session_state.pop(
                                    "selected_url",
                                    None
                                )

                            st.rerun()

                    with cancel_col:

                        if st.button(
                            "Cancel",
                            key=f"cancel_{url['id']}"
                        ):

                            st.session_state[
                                f"confirm_delete_{url['id']}"
                            ] = False

                            st.rerun()

            with action2:

                if url["enabled"]:

                    if st.button(
                        "Disable",
                        key=f"disable_{url['id']}"
                    ):

                        toggle_url(
                            url["id"],
                            False
                        )

                        st.success(
                            f"{url['name']} monitoring disabled."
                        )

                        st.rerun()

                else:

                    if st.button(
                        "Enable",
                        key=f"enable_{url['id']}"
                    ):

                        toggle_url(
                            url["id"],
                            True
                        )

                        st.success(
                            f"{url['name']} monitoring enabled."
                        )

                        st.rerun()

            with action3:

                if st.button(
                    "View History",
                    key=f"history_{url['id']}"
                ):

                    st.session_state[
                        "selected_url"
                    ] = url["id"]

    selected_url = st.session_state.get(
        "selected_url"
    )

    if selected_url:

        st.divider()

        selected_data = None

        for url in urls:

            if url["id"] == selected_url:

                selected_data = url
                break

        if selected_data:

            st.subheader(
                f"Statistics: {selected_data['name']}"
            )

            statistics = get_statistics(
                selected_url
            )

            if statistics:

                col1, col2, col3 = st.columns(3)

                with col1:

                    st.metric(
                        "Total Checks",
                        statistics["total_checks"] or 0
                    )

                with col2:

                    st.metric(
                        "Successful Checks",
                        statistics["successful_checks"] or 0
                    )

                with col3:

                    st.metric(
                        "Failed Checks",
                        statistics["failed_checks"] or 0
                    )

                col4, col5, col6 = st.columns(3)

                with col4:

                    average = statistics[
                        "average_response_time"
                    ]

                    if average is not None:

                        average = round(
                            average,
                            2
                        )

                    st.metric(
                        "Average Response Time",
                        f"{average} ms"
                        if average is not None
                        else "-"
                    )

                with col5:

                    minimum = statistics[
                        "minimum_response_time"
                    ]

                    if minimum is not None:

                        minimum = round(
                            minimum,
                            2
                        )

                    st.metric(
                        "Minimum Response Time",
                        f"{minimum} ms"
                        if minimum is not None
                        else "-"
                    )

                with col6:

                    maximum = statistics[
                        "maximum_response_time"
                    ]

                    if maximum is not None:

                        maximum = round(
                            maximum,
                            2
                        )

                    st.metric(
                        "Maximum Response Time",
                        f"{maximum} ms"
                        if maximum is not None
                        else "-"
                    )

            st.subheader(
                "Recent Health History"
            )

            history = get_history(
                selected_url
            )

            if history:

                history_data = []

                for row in history:

                    history_data.append(
                        {
                            "Timestamp": row["timestamp"],
                            "Status": row["status"],
                            "HTTP Status": row["http_status"],
                            "Response Time": row["response_time"],
                            "Error": row["error"]
                        }
                    )

                st.dataframe(
                    history_data,
                    use_container_width=True,
                    hide_index=True
                )

            else:

                st.info(
                    "No health history available."
                )


st.title("URL Management")

st.caption(
    "Add and manage monitored URLs"
)


with st.expander(
    "Add New URL"
):

    with st.form(
        "add_url_form"
    ):

        name = st.text_input(
            "URL Name",
            placeholder="Example: Google"
        )

        url = st.text_input(
            "URL",
            placeholder="https://google.com"
        )

        interval = st.number_input(
            "Monitoring Interval (seconds)",
            min_value=5,
            value=60,
            step=5
        )

        submitted = st.form_submit_button(
            "Add URL"
        )

        if submitted:

            if not name.strip():

                st.error(
                    "Please enter a URL name."
                )

            elif not url.strip():

                st.error(
                    "Please enter a URL."
                )

            elif not (
                url.startswith("http://")
                or url.startswith("https://")
            ):

                st.error(
                    "URL must start with http:// or https://"
                )

            else:

                try:

                    add_url(
                        name.strip(),
                        url.strip(),
                        interval
                    )

                    st.success(
                        f"{name.strip()} added successfully."
                    )

                    st.rerun()

                except Exception as error:

                    st.error(
                        f"Unable to add URL: {error}"
                    )


with st.expander(
    "Bulk Add URLs"
):

    st.write(
        "Add multiple URLs at once."
    )

    st.write(
        "Enter one URL per line:"
    )

    st.code(
        "Google,https://google.com\n"
        "GitHub,https://github.com\n"
        "Local API,http://127.0.0.1:5000"
    )

    bulk_input = st.text_area(
        "URLs",
        height=180,
        placeholder=(
            "Google,https://google.com\n"
            "GitHub,https://github.com\n"
            "Local API,http://127.0.0.1:5000"
        )
    )

    bulk_interval = st.number_input(
        "Monitoring Interval (seconds)",
        min_value=5,
        value=60,
        step=5,
        key="bulk_interval"
    )

    if st.button(
        "Add All URLs"
    ):

        if not bulk_input.strip():

            st.error(
                "Please enter at least one URL."
            )

        else:

            lines = bulk_input.strip().splitlines()

            added_count = 0
            skipped_count = 0

            for line in lines:

                parts = line.split(",", 1)

                if len(parts) != 2:

                    skipped_count += 1
                    continue

                bulk_name = parts[0].strip()
                bulk_url = parts[1].strip()

                if not bulk_name:

                    skipped_count += 1
                    continue

                if not (
                    bulk_url.startswith("http://")
                    or bulk_url.startswith("https://")
                ):

                    skipped_count += 1
                    continue

                try:

                    add_url(
                        bulk_name,
                        bulk_url,
                        bulk_interval
                    )

                    added_count += 1

                except Exception:

                    skipped_count += 1

            if added_count > 0:

                st.success(
                    f"{added_count} URL(s) added successfully."
                )

            if skipped_count > 0:

                st.warning(
                    f"{skipped_count} URL(s) skipped."
                )

            if added_count > 0:

                st.rerun()


st.divider()

live_dashboard()