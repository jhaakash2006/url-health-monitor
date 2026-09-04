# Basic knowledge about URL Health Monitoring

## Background Processing

In this project, URL monitoring runs in the background so that the Flask application does not have to wait for URL checks to finish.

I used a separate worker file called worker.py for this purpose.

The worker gets the enabled URLs from the database and checks them according to their monitoring interval.

## Why I Used Background Processing

URL checking can take some time because a website may be slow or may not respond.

If URL checking was done directly inside the Flask request, the application could become slow while waiting for the website response.

Because of this, I kept the monitoring work separate from the Flask application.

The Flask application is mainly used for the REST APIs, while the worker handles the periodic monitoring.

## Concurrency Approach

For checking multiple URLs, I used Python's ThreadPoolExecutor from the concurrent.futures module.

ThreadPoolExecutor allows multiple URL checks to run separately.

This is useful because URL monitoring mainly waits for network responses.

For example, if one URL takes 30 seconds to respond, the other URLs do not have to wait for that URL to finish before they can be checked.

## Why I Chose ThreadPoolExecutor

I considered doing the checks one by one, but that would not be efficient when many URLs are configured.

For example, if there are 100 URLs and one URL is very slow, checking them one by one could make the complete monitoring cycle take a long time.

ThreadPoolExecutor allows multiple URLs to be checked at the same time.

I chose it because it is available in Python and is simple enough for this project.

## What Happens If One URL Fails

A failed URL should not stop the monitoring of other URLs.

The URL checking code handles timeout, connection failure and other request errors.

The result of a failed URL is saved in the database and the worker continues with the other URLs.

This means one unavailable website should not stop the complete monitoring process.

## Handling a Slow URL

The request timeout is set to 10 seconds.

If a URL does not respond within the timeout, the request is treated as a failure.

If a URL responds successfully but takes more than 2 seconds, the status is marked as SLOW.

This prevents the worker from waiting forever for a website.

## Checking Many URLs

The project uses ThreadPoolExecutor so multiple URLs can be processed separately.

If there are many configured URLs, the worker can submit their checking tasks to the thread pool instead of waiting for every URL one by one.

This makes the monitoring process more suitable for handling a larger number of URLs.

For a very large number of URLs, the thread pool size and database queries would need to be reviewed and adjusted according to the system resources.

## Why I Did Not Put Monitoring Inside Flask Routes

I did not put the periodic monitoring loop directly inside the Flask routes.

Flask routes should respond to API requests such as adding, deleting, enabling or disabling URLs and getting health information.

Periodic monitoring is a separate background task, so I kept it in worker.py.

This separation makes the project easier to understand and maintain.

## Database Storage

SQLite is used to store URL information and health-check history.

The urls table stores the configured URLs.

The health_checks table stores the result of each monitoring check.

Indexes are also created for the health-check URL ID and timestamp columns.

This helps when health-check history needs to be searched for a particular URL or ordered by time.

## Restart Behavior

The URL configuration and health-check history are stored in SQLite, so the data is not lost when the application is restarted.

After restarting the application, the worker can read the enabled URLs from the database and continue monitoring them.

The previous health-check records remain available in the database.

The worker does not depend on old in-memory data to know which URLs are configured.

## Design Summary

The main design of the project is:

Flask handles REST APIs.

SQLite stores URL configuration and health-check history.

monitor.py contains the URL checking logic.

worker.py handles periodic background monitoring.

ThreadPoolExecutor allows multiple URLs to be checked without making the checks completely sequential.

Streamlit displays the monitoring information through the dashboard.

This design keeps the main parts of the project separate and makes the application easier to manage.