import os
import smtplib

from datetime import datetime
from dotenv import load_dotenv
from email.message import EmailMessage

from database import get_connection


load_dotenv()


SMTP_SERVER = os.getenv(
    "EMAIL_SMTP_SERVER",
    "smtp.gmail.com"
)

SMTP_PORT = int(
    os.getenv(
        "EMAIL_SMTP_PORT",
        "587"
    )
)

EMAIL_SENDER = os.getenv(
    "EMAIL_SENDER"
)

EMAIL_PASSWORD = os.getenv(
    "EMAIL_PASSWORD"
)

EMAIL_RECEIVER = os.getenv(
    "EMAIL_RECEIVER"
)

HIGH_RESPONSE_TIME = float(
    os.getenv(
        "EMAIL_ALERT_RESPONSE_TIME",
        "5"
    )
)


def email_is_configured():

    return bool(
        EMAIL_SENDER
        and EMAIL_PASSWORD
        and EMAIL_RECEIVER
    )


def save_email_alert(
    alert_type,
    url_name,
    url,
    message
):

    connection = get_connection()

    connection.execute(
        """
        INSERT INTO email_alerts
        (
            timestamp,
            alert_type,
            url_name,
            url,
            message
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            datetime.now().isoformat(),
            alert_type,
            url_name,
            url,
            message
        )
    )

    connection.commit()

    connection.close()


def send_email(
    subject,
    message,
    html_message=None,
    alert_type=None,
    url_name=None,
    url=None
):

    if not email_is_configured():

        print(
            "[Email Alert] Email is not configured."
        )

        return False

    email = EmailMessage()

    email["Subject"] = subject
    email["From"] = EMAIL_SENDER
    email["To"] = EMAIL_RECEIVER

    email.set_content(
        message
    )

    if html_message:

        email.add_alternative(
            html_message,
            subtype="html"
        )

    try:

        with smtplib.SMTP(
            SMTP_SERVER,
            SMTP_PORT
        ) as server:

            server.starttls()

            server.login(
                EMAIL_SENDER,
                EMAIL_PASSWORD
            )

            server.send_message(
                email
            )

        if (
            alert_type
            and url_name
            and url
        ):

            save_email_alert(
                alert_type,
                url_name,
                url,
                message
            )

        print(
            "[Email Alert] Email sent successfully."
        )

        return True

    except Exception as error:

        print(
            f"[Email Alert] Failed to send email: {error}"
        )

        return False


def send_down_alert(
    url_name,
    url,
    failure_count
):

    subject = (
        "🚨 URL Health Alert - DOWN"
    )

    message = (
        "URL Health Alert\n\n"
        f"URL Name: {url_name}\n"
        f"URL: {url}\n"
        "Status: DOWN\n"
        f"Consecutive Failures: {failure_count}\n\n"
        "The URL has failed 3 consecutive health checks."
    )

    return send_email(
        subject,
        message,
        None,
        "DOWN",
        url_name,
        url
    )


def send_combined_down_alert(
    down_urls
):

    if not down_urls:

        return False

    subject = (
        "🚨 URL Health Monitor - Combined DOWN Alert"
    )

    message = (
        "URL Health Monitor\n\n"
        f"Total DOWN URLs: {len(down_urls)}\n\n"
    )

    html_rows = ""

    for index, item in enumerate(
        down_urls,
        start=1
    ):

        message += (
            f"{index}. {item['name']}\n"
            f"URL: {item['url']}\n"
            "Status: DOWN\n"
            f"Consecutive Failures: "
            f"{item['failure_count']}\n\n"
        )

        html_rows += f"""
        <p>
        <b>{index}. {item['name']}</b><br>
        URL: {item['url']}<br>
        Status: 🔴 DOWN<br>
        Consecutive Failures: {item['failure_count']}
        </p>
        <hr>
        """

    alert_time = datetime.now().strftime(
        "%d %b %Y, %I:%M:%S %p"
    )

    message += (
        f"Alert Time: {alert_time}\n\n"
        "This combined alert was generated automatically "
        "by the URL Health Monitoring System."
    )

    html_message = f"""
<html>
<body>

<h2>URL HEALTH MONITOR</h2>

<h3>🚨 COMBINED DOWN ALERT</h3>

<p>
<b>Total DOWN URLs:</b> {len(down_urls)}
</p>

{html_rows}

<p>
<b>Alert Time:</b> {alert_time}
</p>

<p>
This combined alert was generated automatically
by the URL Health Monitoring System.
</p>

</body>
</html>
"""

    url_names = ", ".join(
        item["name"]
        for item in down_urls
    )

    return send_email(
        subject,
        message,
        html_message,
        "DOWN",
        url_names,
        "Combined DOWN Alert"
    )


def send_combined_response_time_alert(
    slow_urls
):

    if not slow_urls:

        return False

    subject = (
        "⚠️ URL Health Monitor - "
        "Combined High Response Time Alert"
    )

    message = (
        "URL Health Monitor\n\n"
        f"Total High Response Time URLs: "
        f"{len(slow_urls)}\n\n"
    )

    html_rows = ""

    for index, item in enumerate(
        slow_urls,
        start=1
    ):

        response_seconds = (
            item["response_time"] / 1000
        )

        message += (
            f"{index}. {item['name']}\n"
            f"URL: {item['url']}\n"
            "Status: HIGH RESPONSE TIME\n"
            f"Response Time: "
            f"{response_seconds:.2f} seconds\n"
            f"Alert Threshold: "
            f"{HIGH_RESPONSE_TIME:.2f} seconds\n\n"
        )

        html_rows += f"""
        <p>
        <b>{index}. {item['name']}</b><br>
        URL: {item['url']}<br>
        Status: 🟠 HIGH RESPONSE TIME<br>
        Response Time: {response_seconds:.2f} seconds<br>
        Alert Threshold: {HIGH_RESPONSE_TIME:.2f} seconds
        </p>
        <hr>
        """

    alert_time = datetime.now().strftime(
        "%d %b %Y, %I:%M:%S %p"
    )

    message += (
        f"Alert Time: {alert_time}\n\n"
        "This combined alert was generated automatically "
        "by the URL Health Monitoring System."
    )

    html_message = f"""
<html>
<body>

<h2>URL HEALTH MONITOR</h2>

<h3>⚠️ COMBINED HIGH RESPONSE TIME ALERT</h3>

<p>
<b>Total High Response Time URLs:</b>
{len(slow_urls)}
</p>

{html_rows}

<p>
<b>Alert Time:</b> {alert_time}
</p>

<p>
This combined alert was generated automatically
by the URL Health Monitoring System.
</p>

</body>
</html>
"""

    url_names = ", ".join(
        item["name"]
        for item in slow_urls
    )

    return send_email(
        subject,
        message,
        html_message,
        "HIGH_RESPONSE_TIME",
        url_names,
        "Combined High Response Time Alert"
    )


def send_response_time_alert(
    url_name,
    url,
    response_time
):

    response_seconds = (
        response_time / 1000
    )

    subject = (
        "⚠️ URL Health Alert - High Response Time"
    )

    message = (
        "URL Health Alert\n\n"
        f"URL Name: {url_name}\n"
        f"URL: {url}\n"
        "Status: HIGH RESPONSE TIME\n"
        f"Response Time: {response_seconds:.2f} seconds\n"
        f"Alert Threshold: {HIGH_RESPONSE_TIME:.2f} seconds\n\n"
        "The URL response time is higher than the configured alert threshold."
    )

    return send_email(
        subject,
        message,
        None,
        "HIGH_RESPONSE_TIME",
        url_name,
        url
    )