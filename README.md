# URL Health Monitoring Tool

## About the Project

This is a Python and Flask based URL Health Monitoring Tool that I made to check the health of websites and APIs.

The application checks URLs at regular intervals and stores the results in a SQLite database. It records information such as HTTP status code, response time, current status, errors and previous health-check results.

I used Streamlit to create the dashboard so that the monitoring results can be viewed easily.

The project also uses a background worker so that URL monitoring does not block the Flask application.

## Features

The main features of this project are:

- Add website or API URLs
- Delete URLs
- Enable or disable URL monitoring
- Set a monitoring interval for each URL
- Check URL availability
- Check HTTP status codes
- Measure response time
- Detect slow URLs
- Handle timeout and connection errors
- Mark a URL as DOWN after 3 continuous failures
- Store health-check history
- Calculate average, minimum and maximum response time
- Track successful and failed checks
- Monitor URLs in the background
- Check multiple URLs using ThreadPoolExecutor
- Prevent one slow or failed URL from stopping other URL checks
- Provide REST APIs
- Display monitoring results using Streamlit
- Add multiple URLs using bulk add
- Automatically refresh the dashboard
- View recent health-check history
- View response-time statistics
- View response-time graph
- Compare response times of multiple URLs
- Show actual check time on the graph
- Show execution time in seconds on the graph
- Show check details when viewing graph points
- Run automated tests
- Store monitoring data in SQLite
- Use database indexes for health-check queries
- Support restarting the background worker without losing stored history

## Technologies Used

I used the following technologies in this project:

- Python
- Flask
- SQLite
- Requests
- Streamlit
- ThreadPoolExecutor
- unittest
- Git
- GitHub

## Project Files

### app.py

This file contains the Flask application.

It also contains the REST API routes used for URL management and health information.

The APIs can be used to add, delete and manage URLs and to view current and historical health information.

### database.py

This file creates and initializes the SQLite database.

It creates the required tables and indexes used by the application.

The database is created locally as `monitor.db`.

### monitor.py

This file contains the main URL checking functions.

It sends requests to the URLs, measures response time and handles different request errors.

It also stores health-check results in the database.

The monitoring logic also checks consecutive failures so that a URL can be marked as DOWN after 3 continuous failures.

### worker.py

This file runs the URL monitoring in the background.

It checks enabled URLs according to their configured monitoring interval.

It uses ThreadPoolExecutor to check multiple URLs separately.

### dashboard.py

This file contains the Streamlit dashboard.

It displays the current URL status, response time, HTTP status, errors, monitoring status and last check time.

It also provides options to add, delete, enable, disable and bulk add URLs.

The dashboard automatically refreshes so that updated monitoring information can be seen without manually refreshing the page.

The dashboard also contains monitoring history, response-time statistics and graphs.

### test_monitor.py

This file contains the automated tests for the monitoring functions.

The tests check both a working URL and a failed URL.

### monitor.db

This is the SQLite database file.

It stores the configured URLs and the health-check history.

### Some_Basic_facts.md

This file contains the main engineering and design decisions of the project.

It explains why a separate background worker was used, why ThreadPoolExecutor was selected and how the application handles slow or failed URLs.

It also explains database indexing, restart behavior and handling multiple URLs.

### requirements.txt

This file contains the external Python packages required by the project.

The main packages are:

- Flask
- Requests
- Streamlit

Python built-in modules such as sqlite3, unittest, datetime and concurrent.futures do not need to be added to this file.

### .gitignore

This file contains files and folders that should not be uploaded to GitHub.

For example, the virtual environment and local SQLite database are ignored.

## Database

I used SQLite because the project is running locally and SQLite is simple to set up without requiring a separate database server.

The database contains two main tables.

### urls

This table stores the URLs that are being monitored.

The main fields are:

- id
- url
- name
- enabled
- interval

### health_checks

This table stores the result of every health check.

The main fields are:

- id
- url_id
- timestamp
- status
- http_status
- response_time
- error

I also added indexes for the URL ID and timestamp columns in the `health_checks` table.

These indexes can help when health-check history needs to be searched for a particular URL or time.

## URL Status

The application uses different statuses based on the result of a health check.

### UP

The URL responded successfully and the response time was 2 seconds or less.

### SLOW

The URL responded successfully but took more than 2 seconds.

### FAIL

The URL could not be checked because of a timeout, connection problem or another request error.

### DOWN

If a URL fails 3 times continuously, the application marks it as DOWN.

## Background Monitoring

I used a separate background worker for URL monitoring so that the Flask application does not have to wait for health checks to finish.

The background monitoring code is present in `worker.py`.

For checking multiple URLs, I used Python's ThreadPoolExecutor.

This allows multiple URL checks to run separately. Because of this, one slow or unavailable URL should not stop the monitoring of the other URLs.

The worker only checks URLs that are enabled and uses the monitoring interval stored for each URL.

A request timeout is also used so that the worker does not wait forever for a URL that is not responding.

More details about this design are explained in `Some_Basic_facts.md`.

## Error Handling

The application handles common problems that can happen while checking a URL.

These include:

- Request timeout
- Connection failure
- Request errors
- Unexpected errors

If one URL fails, the error is saved in the database and the monitoring process continues with the other URLs.

The application uses a request timeout so that a slow or unavailable website does not block the monitoring process for an unlimited amount of time.

## Dashboard

I used Streamlit for the dashboard.

The dashboard shows information such as:

- Total number of URLs
- Healthy URLs
- Down URLs
- URL name
- URL address
- Current status
- HTTP status
- Response time
- Monitoring status
- Monitoring interval
- Error information
- Last check time
- Health-check history
- Average response time
- Minimum response time
- Maximum response time
- Successful checks
- Failed checks

The dashboard also allows URLs to be:

- Added
- Deleted
- Enabled
- Disabled
- Added in bulk

The dashboard automatically refreshes every 10 seconds so that new monitoring results can be displayed.

## Monitoring Analytics

The dashboard provides monitoring analytics for a selected URL.

It shows response-time information and health-check history.

The response-time graph shows:

- Actual Check Time on the X axis
- Execution Time in seconds on the Y axis
- A continuous response-time line
- Individual check points

When a graph point is selected or hovered over, information such as the following can be viewed:

- Check Time
- Status
- Execution Time
- HTTP Status
- Error

The dashboard also provides different time ranges for viewing history.

These include:

- Last 1 hour
- Last 6 hours
- Last 24 hours
- All history

A URL comparison graph is also available to compare response times between multiple monitored URLs.

## REST API

The project also provides REST APIs using Flask.

The APIs are used for managing URLs and viewing current and previous health-check information.

The API can be used to:

- Add URLs
- Delete URLs
- Enable or disable URLs
- View configured URLs
- View current health information
- View health-check history
- View monitoring statistics

They can be tested using a browser, curl or another API testing tool.

## Automated Testing

I added automated tests using Python's unittest module.

I run the tests using:

```powershell
python -m unittest test_monitor.py