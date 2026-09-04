from flask import Flask, request, jsonify

from database import get_connection


app = Flask(__name__)


@app.route("/", methods=["GET"])
def home():
    return "URL Health Monitor API is running!"


@app.route("/api/urls", methods=["GET"])
def get_urls():
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT id, name, url, enabled, interval
        FROM urls
        ORDER BY id
        """
    ).fetchall()

    connection.close()

    return jsonify([dict(row) for row in rows])


@app.route("/api/urls", methods=["POST"])
def add_url():
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "JSON body is required"
        }), 400

    name = data.get("name")
    url = data.get("url")
    interval = data.get("interval", 60)

    if not name:
        return jsonify({
            "error": "name is required"
        }), 400

    if not url:
        return jsonify({
            "error": "url is required"
        }), 400

    try:
        interval = int(interval)
    except (TypeError, ValueError):
        return jsonify({
            "error": "interval must be a number"
        }), 400

    if interval <= 0:
        return jsonify({
            "error": "interval must be greater than 0"
        }), 400

    connection = get_connection()

    cursor = connection.execute(
        """
        INSERT INTO urls
        (
            name,
            url,
            enabled,
            interval
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            name,
            url,
            1,
            interval
        )
    )

    connection.commit()

    url_id = cursor.lastrowid

    connection.close()

    return jsonify({
        "message": "URL added successfully",
        "id": url_id,
        "name": name,
        "url": url,
        "enabled": True,
        "interval": interval
    }), 201


@app.route("/api/urls/<int:url_id>", methods=["GET"])
def get_url(url_id):
    connection = get_connection()

    url = connection.execute(
        """
        SELECT id, name, url, enabled, interval
        FROM urls
        WHERE id = ?
        """,
        (url_id,)
    ).fetchone()

    if url is None:
        connection.close()

        return jsonify({
            "error": "URL not found"
        }), 404

    history = connection.execute(
        """
        SELECT
            id,
            url_id,
            timestamp,
            status,
            http_status,
            response_time,
            error
        FROM health_checks
        WHERE url_id = ?
        ORDER BY timestamp DESC
        LIMIT 10
        """,
        (url_id,)
    ).fetchall()

    connection.close()

    return jsonify({
        "id": url["id"],
        "name": url["name"],
        "url": url["url"],
        "enabled": bool(url["enabled"]),
        "interval": url["interval"],
        "history": [dict(row) for row in history]
    })


@app.route("/api/urls/<int:url_id>", methods=["DELETE"])
def delete_url(url_id):
    connection = get_connection()

    url = connection.execute(
        """
        SELECT id
        FROM urls
        WHERE id = ?
        """,
        (url_id,)
    ).fetchone()

    if url is None:
        connection.close()

        return jsonify({
            "error": "URL not found"
        }), 404

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

    return jsonify({
        "message": "URL deleted successfully",
        "url_id": url_id
    })


@app.route("/api/urls/<int:url_id>", methods=["PUT"])
def update_url(url_id):
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "JSON body is required"
        }), 400

    connection = get_connection()

    existing_url = connection.execute(
        """
        SELECT id, name, url, enabled, interval
        FROM urls
        WHERE id = ?
        """,
        (url_id,)
    ).fetchone()

    if existing_url is None:
        connection.close()

        return jsonify({
            "error": "URL not found"
        }), 404

    name = data.get("name", existing_url["name"])
    url = data.get("url", existing_url["url"])
    enabled = data.get("enabled", existing_url["enabled"])
    interval = data.get("interval", existing_url["interval"])

    try:
        interval = int(interval)
    except (TypeError, ValueError):
        connection.close()

        return jsonify({
            "error": "interval must be a number"
        }), 400

    if interval <= 0:
        connection.close()

        return jsonify({
            "error": "interval must be greater than 0"
        }), 400

    enabled = 1 if bool(enabled) else 0

    connection.execute(
        """
        UPDATE urls
        SET name = ?,
            url = ?,
            enabled = ?,
            interval = ?
        WHERE id = ?
        """,
        (
            name,
            url,
            enabled,
            interval,
            url_id
        )
    )

    connection.commit()
    connection.close()

    return jsonify({
        "message": "URL updated successfully",
        "id": url_id,
        "name": name,
        "url": url,
        "enabled": bool(enabled),
        "interval": interval
    })


@app.route("/api/urls/<int:url_id>/enable", methods=["POST"])
def enable_url(url_id):
    connection = get_connection()

    url = connection.execute(
        """
        SELECT id
        FROM urls
        WHERE id = ?
        """,
        (url_id,)
    ).fetchone()

    if url is None:
        connection.close()

        return jsonify({
            "error": "URL not found"
        }), 404

    connection.execute(
        """
        UPDATE urls
        SET enabled = 1
        WHERE id = ?
        """,
        (url_id,)
    )

    connection.commit()
    connection.close()

    return jsonify({
        "message": "URL enabled successfully",
        "url_id": url_id,
        "enabled": True
    })


@app.route("/api/urls/<int:url_id>/disable", methods=["POST"])
def disable_url(url_id):
    connection = get_connection()

    url = connection.execute(
        """
        SELECT id
        FROM urls
        WHERE id = ?
        """,
        (url_id,)
    ).fetchone()

    if url is None:
        connection.close()

        return jsonify({
            "error": "URL not found"
        }), 404

    connection.execute(
        """
        UPDATE urls
        SET enabled = 0
        WHERE id = ?
        """,
        (url_id,)
    )

    connection.commit()
    connection.close()

    return jsonify({
        "message": "URL disabled successfully",
        "url_id": url_id,
        "enabled": False
    })


@app.route("/api/urls/<int:url_id>/history", methods=["GET"])
def get_url_history(url_id):
    connection = get_connection()

    url = connection.execute(
        """
        SELECT id, name, url
        FROM urls
        WHERE id = ?
        """,
        (url_id,)
    ).fetchone()

    if url is None:
        connection.close()

        return jsonify({
            "error": "URL not found"
        }), 404

    history = connection.execute(
        """
        SELECT
            id,
            url_id,
            timestamp,
            status,
            http_status,
            response_time,
            error
        FROM health_checks
        WHERE url_id = ?
        ORDER BY timestamp DESC
        """,
        (url_id,)
    ).fetchall()

    connection.close()

    return jsonify({
        "url_id": url["id"],
        "name": url["name"],
        "url": url["url"],
        "history": [dict(row) for row in history]
    })


@app.route("/api/urls/<int:url_id>/health", methods=["GET"])
def get_current_health(url_id):
    connection = get_connection()

    url = connection.execute(
        """
        SELECT id, name, url
        FROM urls
        WHERE id = ?
        """,
        (url_id,)
    ).fetchone()

    if url is None:
        connection.close()

        return jsonify({
            "error": "URL not found"
        }), 404

    health = connection.execute(
        """
        SELECT
            id,
            url_id,
            timestamp,
            status,
            http_status,
            response_time,
            error
        FROM health_checks
        WHERE url_id = ?
        ORDER BY timestamp DESC
        LIMIT 1
        """,
        (url_id,)
    ).fetchone()

    connection.close()

    if health is None:
        return jsonify({
            "url_id": url["id"],
            "name": url["name"],
            "url": url["url"],
            "health": None
        })

    return jsonify({
        "url_id": url["id"],
        "name": url["name"],
        "url": url["url"],
        "health": dict(health)
    })


@app.route("/api/urls/<int:url_id>/stats", methods=["GET"])
def get_url_stats(url_id):
    connection = get_connection()

    url = connection.execute(
        """
        SELECT id, name, url
        FROM urls
        WHERE id = ?
        """,
        (url_id,)
    ).fetchone()

    if url is None:
        connection.close()

        return jsonify({
            "error": "URL not found"
        }), 404

    stats = connection.execute(
        """
        SELECT
            COUNT(*) AS total_checks,
            SUM(
                CASE
                    WHEN status IN ('UP', 'SLOW')
                    THEN 1
                    ELSE 0
                END
            ) AS successful_checks,
            SUM(
                CASE
                    WHEN status IN ('FAIL', 'DOWN')
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

    return jsonify({
        "url_id": url["id"],
        "name": url["name"],
        "url": url["url"],
        "total_checks": stats["total_checks"] or 0,
        "successful_checks": stats["successful_checks"] or 0,
        "failed_checks": stats["failed_checks"] or 0,
        "average_response_time": round(stats["average_response_time"], 2) if stats["average_response_time"] is not None else 0,
        "minimum_response_time": round(stats["minimum_response_time"], 2) if stats["minimum_response_time"] is not None else 0,
        "maximum_response_time": round(stats["maximum_response_time"], 2) if stats["maximum_response_time"] is not None else 0
    })


@app.route("/api/dashboard", methods=["GET"])
def get_dashboard():
    connection = get_connection()

    urls = connection.execute(
        """
        SELECT
            id,
            name,
            url,
            enabled,
            interval
        FROM urls
        ORDER BY id
        """
    ).fetchall()

    dashboard_urls = []

    total_urls = len(urls)
    healthy_urls = 0
    down_urls = 0

    for url in urls:
        latest = connection.execute(
            """
            SELECT
                status,
                http_status,
                response_time,
                timestamp,
                error
            FROM health_checks
            WHERE url_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            (url["id"],)
        ).fetchone()

        current_status = "UNKNOWN"
        http_status = None
        response_time = None
        timestamp = None
        error = None

        if latest is not None:
            current_status = latest["status"]
            http_status = latest["http_status"]
            response_time = latest["response_time"]
            timestamp = latest["timestamp"]
            error = latest["error"]

        if current_status in ("UP", "SLOW"):
            healthy_urls += 1

        if current_status == "DOWN":
            down_urls += 1

        dashboard_urls.append({
            "id": url["id"],
            "name": url["name"],
            "url": url["url"],
            "enabled": bool(url["enabled"]),
            "interval": url["interval"],
            "status": current_status,
            "http_status": http_status,
            "response_time": response_time,
            "timestamp": timestamp,
            "error": error
        })

    connection.close()

    return jsonify({
        "total_urls": total_urls,
        "healthy_urls": healthy_urls,
        "down_urls": down_urls,
        "urls": dashboard_urls
    })


if __name__ == "__main__":
    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )