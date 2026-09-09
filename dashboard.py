import sqlite3
import streamlit as st
from pathlib import Path
from datetime import datetime, timedelta


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


def get_graph_history(url_id, hours):
    connection = get_connection()

    if hours is None:

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
            ORDER BY timestamp
            """,
            (url_id,)
        ).fetchall()

    else:

        start_time = datetime.now() - timedelta(
            hours=hours
        )

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
            AND timestamp >= ?
            ORDER BY timestamp
            """,
            (
                url_id,
                start_time.isoformat()
            )
        ).fetchall()

    connection.close()

    return rows


def get_comparison_history(url_ids, hours):
    if not url_ids:
        return []

    connection = get_connection()

    placeholders = ",".join(
        "?" for _ in url_ids
    )

    if hours is None:

        query = f"""
            SELECT
                h.timestamp,
                h.url_id,
                u.name,
                u.url,
                h.status,
                h.response_time
            FROM health_checks h
            JOIN urls u
            ON u.id = h.url_id
            WHERE h.url_id IN ({placeholders})
            ORDER BY h.timestamp
        """

        parameters = tuple(url_ids)

    else:

        start_time = datetime.now() - timedelta(
            hours=hours
        )

        query = f"""
            SELECT
                h.timestamp,
                h.url_id,
                u.name,
                u.url,
                h.status,
                h.response_time
            FROM health_checks h
            JOIN urls u
            ON u.id = h.url_id
            WHERE h.url_id IN ({placeholders})
            AND h.timestamp >= ?
            ORDER BY h.timestamp
        """

        parameters = tuple(url_ids) + (
            start_time.isoformat(),
        )

    rows = connection.execute(
        query,
        parameters
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


def url_exists(url):
    connection = get_connection()

    row = connection.execute(
        """
        SELECT id
        FROM urls
        WHERE url = ?
        LIMIT 1
        """,
        (url,)
    ).fetchone()

    connection.close()

    return row is not None


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


def update_interval(url_id, interval):
    connection = get_connection()

    connection.execute(
        """
        UPDATE urls
        SET interval = ?
        WHERE id = ?
        """,
        (
            interval,
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


def format_response_time(value):
    if value is None:
        return "-"

    return (
        f"{value:.2f} ms "
        f"({value / 1000:.2f} sec)"
    )


def show_statistics(selected_data):

    selected_url = selected_data["id"]

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

            st.metric(
                "Average Response Time",
                format_response_time(
                    statistics["average_response_time"]
                )
            )

        with col5:

            st.metric(
                "Minimum Response Time",
                format_response_time(
                    statistics["minimum_response_time"]
                )
            )

        with col6:

            st.metric(
                "Maximum Response Time",
                format_response_time(
                    statistics["maximum_response_time"]
                )
            )


def show_history_table(selected_url, hours):

    history = get_graph_history(
        selected_url["id"],
        hours
    )

    if not history:

        st.info(
            "No health history available."
        )

        return

    history_data = []

    for row in reversed(history):

        history_data.append(
            {
                "Time": row["timestamp"],
                "Status": row["status"],
                "HTTP": (
                    row["http_status"]
                    if row["http_status"] is not None
                    else "-"
                ),
                "Response Time": format_response_time(
                    row["response_time"]
                ),
                "Error": row["error"] or "-"
            }
        )

    st.dataframe(
        history_data,
        use_container_width=True,
        hide_index=True
    )


def show_response_time_chart(selected_url, hours):

    rows = get_graph_history(
        selected_url["id"],
        hours
    )

    chart_data = []

    for row in rows:

        if row["response_time"] is None:
            continue

        chart_data.append(
            {
                "time": row["timestamp"],
                "response_time": round(
                    row["response_time"] / 1000,
                    3
                ),
                "status": row["status"],
                "http_status": (
                    row["http_status"]
                    if row["http_status"] is not None
                    else "-"
                ),
                "error": row["error"] or "-"
            }
        )

    if not chart_data:

        st.info(
            "No response-time data available."
        )

        return

    st.markdown(
        "### Response Time"
    )

    st.caption(
        "Execution time is shown in seconds. "
        "Each point represents one actual check."
    )

    response_chart = {
        "data": {
            "values": chart_data
        },
        "width": "container",
        "height": 320,
        "mark": {
            "type": "line",
            "strokeWidth": 3,
            "point": {
                "filled": True,
                "size": 110
            }
        },
        "encoding": {
            "x": {
                "field": "time",
                "type": "temporal",
                "title": "Actual Check Time"
            },
            "y": {
                "field": "response_time",
                "type": "quantitative",
                "title": "Execution Time (seconds)"
            },
            "tooltip": [
                {
                    "field": "time",
                    "type": "temporal",
                    "title": "Check Time",
                    "format": "%d-%m-%Y %H:%M:%S"
                },
                {
                    "field": "status",
                    "type": "nominal",
                    "title": "Status"
                },
                {
                    "field": "response_time",
                    "type": "quantitative",
                    "title": "Execution Time (sec)",
                    "format": ".3f"
                },
                {
                    "field": "http_status",
                    "type": "nominal",
                    "title": "HTTP Status"
                },
                {
                    "field": "error",
                    "type": "nominal",
                    "title": "Error"
                }
            ]
        }
    }

    st.vega_lite_chart(
        response_chart,
        use_container_width=True
    )


def show_url_comparison(urls, hours):

    st.subheader(
        "Compare URLs"
    )

    st.caption(
        "Select URLs to compare their response times."
    )

    url_options = {}

    for url in urls:

        url_options[
            f"{url['name']} - {url['url']}"
        ] = url["id"]

    selected_labels = st.multiselect(
        "Select URLs",
        list(url_options.keys()),
        max_selections=5,
        key="comparison_urls"
    )

    if not selected_labels:

        st.info(
            "Select two or more URLs to see the comparison graph."
        )

        return

    selected_ids = []

    for label in selected_labels:

        selected_ids.append(
            url_options[label]
        )

    rows = get_comparison_history(
        selected_ids,
        hours
    )

    if not rows:

        st.info(
            "No comparison data available."
        )

        return

    chart_data = []

    for row in rows:

        if row["response_time"] is None:
            continue

        chart_data.append(
            {
                "time": row["timestamp"],
                "url": row["name"],
                "response_time": round(
                    row["response_time"] / 1000,
                    3
                ),
                "status": row["status"]
            }
        )

    if not chart_data:

        st.info(
            "No response-time data available."
        )

        return

    comparison_chart = {
        "data": {
            "values": chart_data
        },
        "width": "container",
        "height": 350,
        "mark": {
            "type": "line",
            "strokeWidth": 3,
            "point": {
                "filled": True,
                "size": 80
            }
        },
        "encoding": {
            "x": {
                "field": "time",
                "type": "temporal",
                "title": "Actual Check Time"
            },
            "y": {
                "field": "response_time",
                "type": "quantitative",
                "title": "Execution Time (seconds)"
            },
            "color": {
                "field": "url",
                "type": "nominal",
                "title": "URL"
            },
            "detail": {
                "field": "url"
            },
            "tooltip": [
                {
                    "field": "time",
                    "type": "temporal",
                    "title": "Check Time",
                    "format": "%d-%m-%Y %H:%M:%S"
                },
                {
                    "field": "url",
                    "type": "nominal",
                    "title": "URL"
                },
                {
                    "field": "status",
                    "type": "nominal",
                    "title": "Status"
                },
                {
                    "field": "response_time",
                    "type": "quantitative",
                    "title": "Execution Time (sec)",
                    "format": ".3f"
                }
            ]
        }
    }

    st.vega_lite_chart(
        comparison_chart,
        use_container_width=True
    )


def show_graph_history(selected_url, urls):

    st.divider()

    st.subheader(
        f"Monitoring Analytics - {selected_url['name']}"
    )

    range_options = {
        "Last 1 hour": 1,
        "Last 6 hours": 6,
        "Last 24 hours": 24,
        "All history": None
    }

    selected_range = st.selectbox(
        "Time Range",
        list(range_options.keys()),
        index=2,
        key=f"graph_range_{selected_url['id']}"
    )

    hours = range_options[
        selected_range
    ]

    show_response_time_chart(
        selected_url,
        hours
    )

    st.divider()

    show_url_comparison(
        urls,
        hours
    )

    st.divider()

    with st.expander(
        "View Detailed Health Checks"
    ):

        show_history_table(
            selected_url,
            hours
        )

    st.divider()

    show_statistics(
        selected_url
    )


@st.fragment(run_every="10s")
def live_dashboard():

    urls = get_urls()

    total_urls = len(urls)

    healthy_urls = 0
    down_urls = 0

    for url in urls:

        status = url["status"]

        if status in (
            "UP",
            "SLOW"
        ):

            healthy_urls += 1

        elif status == "DOWN":

            down_urls += 1

    st.title(
        "URL Health Monitor"
    )

    st.caption(
        "Live monitoring dashboard"
    )

    st.write(
        "Last refresh:",
        datetime.now().strftime(
            "%H:%M:%S"
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

    st.subheader(
        "URL Status"
    )

    if not urls:

        st.info(
            "No URLs have been configured yet."
        )

    else:

        header_col1, header_col2, header_col3, header_col4, header_col5, header_col6 = st.columns(
            [2.2, 3.5, 1.2, 1.2, 1.5, 2]
        )

        with header_col1:

            st.caption("NAME")

        with header_col2:

            st.caption("URL")

        with header_col3:

            st.caption("STATUS")

        with header_col4:

            st.caption("HTTP")

        with header_col5:

            st.caption("TIME")

        with header_col6:

            st.caption("MONITORING / LAST CHECK")

        for url in urls:

            status = get_status_text(
                url["status"]
            )

            response_time = url[
                "response_time"
            ]

            if response_time is None:

                response_text = "-"

            else:

                response_text = (
                    f"{response_time:.2f} ms "
                    f"({response_time / 1000:.2f} sec)"
                )

            http_status = url[
                "http_status"
            ]

            if http_status is None:

                http_text = "-"

            else:

                http_text = str(
                    http_status
                )

            if url["enabled"]:

                monitoring = "🟢 On"

            else:

                monitoring = "⚪ Off"

            last_check = "-"

            if url["timestamp"]:

                try:

                    timestamp = datetime.fromisoformat(
                        url["timestamp"]
                    )

                    last_check = timestamp.strftime(
                        "%H:%M:%S"
                    )

                except ValueError:

                    last_check = url[
                        "timestamp"
                    ]

            row_col1, row_col2, row_col3, row_col4, row_col5, row_col6 = st.columns(
                [2.2, 3.5, 1.2, 1.2, 1.5, 2]
            )

            with row_col1:

                st.write(
                    f"**{url['name']}**"
                )

            with row_col2:

                st.caption(
                    url["url"]
                )

            with row_col3:

                st.write(
                    status
                )

            with row_col4:

                st.write(
                    http_text
                )

            with row_col5:

                st.write(
                    response_text
                )

            with row_col6:

                st.write(
                    f"{monitoring}  {last_check}"
                )

            if url["error"]:

                st.caption(
                    f"Error: {url['error']}"
                )

            st.divider()

    st.subheader(
        "URL Management"
    )

    if urls:

        url_options = {}

        for url in urls:

            url_options[
                f"{url['name']} - {url['url']}"
            ] = url["id"]

        selected_name = st.selectbox(
            "Select URL",
            list(url_options.keys()),
            key="manage_url"
        )

        selected_url_id = url_options[
            selected_name
        ]

        selected_data = None

        for url in urls:

            if url["id"] == selected_url_id:

                selected_data = url

                break

        if selected_data:

            st.write(
                f"Selected URL: **{selected_data['name']}**"
            )

            manage_col1, manage_col2, manage_col3 = st.columns(
                3
            )

            with manage_col1:

                new_interval = st.number_input(
                    "Monitoring Interval (seconds)",
                    min_value=5,
                    value=int(
                        selected_data["interval"]
                    ),
                    step=5,
                    key=f"interval_{selected_url_id}"
                )

                if st.button(
                    "Update Interval",
                    key=f"update_interval_{selected_url_id}"
                ):

                    update_interval(
                        selected_url_id,
                        new_interval
                    )

                    st.success(
                        "Monitoring interval updated."
                    )

                    st.rerun()

            with manage_col2:

                if selected_data["enabled"]:

                    if st.button(
                        "Disable Monitoring",
                        key=f"disable_manage_{selected_url_id}"
                    ):

                        toggle_url(
                            selected_url_id,
                            False
                        )

                        st.success(
                            f"{selected_data['name']} "
                            f"monitoring disabled."
                        )

                        st.rerun()

                else:

                    if st.button(
                        "Enable Monitoring",
                        key=f"enable_manage_{selected_url_id}"
                    ):

                        toggle_url(
                            selected_url_id,
                            True
                        )

                        st.success(
                            f"{selected_data['name']} "
                            f"monitoring enabled."
                        )

                        st.rerun()

            with manage_col3:

                if st.button(
                    "View History",
                    key=f"history_manage_{selected_url_id}"
                ):

                    st.session_state[
                        "selected_history_url"
                    ] = selected_url_id

                    st.rerun()

            st.write("")

            if st.button(
                "Delete Selected URL",
                key=f"delete_manage_{selected_url_id}"
            ):

                st.session_state[
                    "confirm_delete_url"
                ] = selected_url_id

            if st.session_state.get(
                "confirm_delete_url"
            ) == selected_url_id:

                st.warning(
                    f"Are you sure you want to delete "
                    f"'{selected_data['name']}'?"
                )

                confirm_col, cancel_col = st.columns(2)

                with confirm_col:

                    if st.button(
                        "Yes, Delete",
                        key=f"confirm_delete_manage_{selected_url_id}"
                    ):

                        delete_url(
                            selected_url_id
                        )

                        st.session_state.pop(
                            "confirm_delete_url",
                            None
                        )

                        st.session_state.pop(
                            "selected_history_url",
                            None
                        )

                        st.rerun()

                with cancel_col:

                    if st.button(
                        "Cancel",
                        key=f"cancel_delete_manage_{selected_url_id}"
                    ):

                        st.session_state.pop(
                            "confirm_delete_url",
                            None
                        )

                        st.rerun()

            selected_history_url = st.session_state.get(
                "selected_history_url"
            )

            if selected_history_url == selected_url_id:

                show_graph_history(
                    selected_data,
                    urls
                )

    else:

        st.info(
            "No URLs available for management."
        )


st.title(
    "URL Management"
)

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
                    "URL must start with "
                    "http:// or https://"
                )

            elif url_exists(
                url.strip()
            ):

                st.error(
                    "This URL is already being monitored."
                )

            else:

                try:

                    add_url(
                        name.strip(),
                        url.strip(),
                        interval
                    )

                    st.success(
                        f"{name.strip()} "
                        f"added successfully."
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
        "You can enter either Name,URL or just URL."
    )

    st.code(
        "Google,https://google.com\n"
        "GitHub,https://github.com\n"
        "https://youtube.com\n"
        "https://stackoverflow.com"
    )

    bulk_input = st.text_area(
        "URLs",
        height=180,
        placeholder=(
            "Google,https://google.com\n"
            "GitHub,https://github.com\n"
            "https://youtube.com\n"
            "https://stackoverflow.com"
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

            lines = (
                bulk_input
                .strip()
                .splitlines()
            )

            added_count = 0
            skipped_count = 0
            skipped_lines = []

            for line_number, line in enumerate(
                lines,
                start=1
            ):

                line = line.strip()

                if not line:

                    skipped_count += 1

                    skipped_lines.append(
                        f"Line {line_number}: Empty line"
                    )

                    continue

                if "," in line:

                    parts = line.split(
                        ",",
                        1
                    )

                    bulk_name = parts[0].strip()
                    bulk_url = parts[1].strip()

                    if not bulk_name:

                        skipped_count += 1

                        skipped_lines.append(
                            f"Line {line_number}: "
                            f"URL name is missing"
                        )

                        continue

                else:

                    bulk_url = line

                    bulk_name = (
                        bulk_url
                        .replace(
                            "https://",
                            ""
                        )
                        .replace(
                            "http://",
                            ""
                        )
                        .split(
                            "/"
                        )[0]
                    )

                if not (
                    bulk_url.startswith(
                        "http://"
                    )
                    or bulk_url.startswith(
                        "https://"
                    )
                ):

                    skipped_count += 1

                    skipped_lines.append(
                        f"Line {line_number}: "
                        f"Invalid URL"
                    )

                    continue

                if url_exists(
                    bulk_url
                ):

                    skipped_count += 1

                    skipped_lines.append(
                        f"Line {line_number}: "
                        f"URL already exists"
                    )

                    continue

                try:

                    add_url(
                        bulk_name,
                        bulk_url,
                        bulk_interval
                    )

                    added_count += 1

                except Exception as error:

                    skipped_count += 1

                    skipped_lines.append(
                        f"Line {line_number}: {error}"
                    )

            if added_count > 0:

                st.success(
                    f"{added_count} URL(s) "
                    f"added successfully."
                )

            if skipped_count > 0:

                st.warning(
                    f"{skipped_count} URL(s) skipped."
                )

                for skipped_line in skipped_lines:

                    st.write(
                        skipped_line
                    )

            if added_count > 0:

                st.rerun()


st.divider()

live_dashboard()   