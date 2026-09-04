# URL Health Monitoring Tool

## About the Project

This is a Python and Flask based URL Health Monitoring Tool that I made to check the health of websites and APIs.

The application checks URLs at regular intervals and stores the results in a SQLite database. It records information such as HTTP status code, response time, current status and errors.

I used Streamlit to create the dashboard so that the monitoring results can be viewed easily.

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
- Provide REST APIs
- Display monitoring results using Streamlit
- Add multiple URLs using bulk add
- Automatically refresh the dashboard
- Run automated tests

## Technologies Used

I used the following technologies in this project:

- Python
- Flask
- SQLite
- Requests
- Streamlit
- ThreadPoolExecutor
- unittest

## Project Files

### app.py

This file contains the Flask application.

It also contains the REST API routes used for URL management and health information.

### database.py

This file creates and initializes the SQLite database.

It creates the required tables and indexes used by the application.

### monitor.py

This file contains the main URL checking functions.

It sends requests to the URLs, measures response time and handles different request errors.

### worker.py

This file runs the URL monitoring in the background.

It checks enabled URLs according to their configured monitoring interval.

### dashboard.py

This file contains the Streamlit dashboard.

It displays the current URL status, response time, HTTP status, errors, history and statistics.

It also provides options to manage URLs.

### test_monitor.py

This file contains the automated tests for the monitoring functions.

### monitor.db

This is the SQLite database file.

It stores the configured URLs and the health-check history.

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

I also added indexes for the URL ID and timestamp columns in the health_checks table. This will help when health-check history needs to be searched for a particular URL or time.

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

The background monitoring code is present in worker.py.

For checking multiple URLs, I used Python's ThreadPoolExecutor.

This allows multiple URL checks to run separately. Because of this, one slow or unavailable URL should not stop the monitoring of the other URLs.

The worker only checks URLs that are enabled and uses the monitoring interval stored for each URL.

More details about this design are explained in DESIGN.md.

## Error Handling

The application handles common problems that can happen while checking a URL.

These include:

- Request timeout
- Connection failure
- Request errors
- Unexpected errors

If one URL fails, the error is saved in the database and the monitoring process continues with the other URLs.

A timeout is also used so that the worker does not wait forever for a URL that is not responding.

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

The dashboard also allows URLs to be added, deleted, enabled, disabled and added in bulk.

## REST API

The project also provides REST APIs using Flask.

The APIs are used for managing URLs and viewing current and previous health-check information.

They can be tested using a browser, curl or another API testing tool.

## How to Run the Project

First, open PowerShell in the project folder.

Then activate the virtual environment:

```powershell
.venv\Scripts\Activate.ps1