from flask import Flask, render_template, request, redirect
from database import init_database, get_connection


app = Flask(
    __name__,
    template_folder="app/templates",
    static_folder="app/static"
)


@app.route("/")
def home():
    status_filter = request.args.get("status", "All")
    search = request.args.get("search", "").strip()

    connection = get_connection()

    query = "SELECT * FROM tickets WHERE 1=1"
    parameters = []

    if status_filter != "All":
        query += " AND status = ?"
        parameters.append(status_filter)

    if search:
        query += " AND (title LIKE ? OR description LIKE ?)"
        search_term = f"%{search}%"
        parameters.extend([search_term, search_term])

    query += " ORDER BY created_at DESC"

    tickets = connection.execute(
        query,
        parameters
    ).fetchall()

    open_count = connection.execute(
        "SELECT COUNT(*) FROM tickets WHERE status = 'Open'"
    ).fetchone()[0]

    in_progress_count = connection.execute(
        "SELECT COUNT(*) FROM tickets WHERE status = 'In Progress'"
    ).fetchone()[0]

    resolved_count = connection.execute(
        "SELECT COUNT(*) FROM tickets WHERE status = 'Resolved'"
    ).fetchone()[0]

    connection.close()

    return render_template(
        "index.html",
        tickets=tickets,
        open_count=open_count,
        in_progress_count=in_progress_count,
        resolved_count=resolved_count,
        status_filter=status_filter,
        search=search
    )


@app.route("/new-ticket", methods=["GET", "POST"])
def new_ticket():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        priority = request.form.get("priority", "")

        allowed_priorities = {
            "Low",
            "Medium",
            "High",
            "Critical"
        }

        if not title or not description:
            return "Title and description are required.", 400

        if priority not in allowed_priorities:
            return "Invalid priority.", 400

        connection = get_connection()

        connection.execute(
            """
            INSERT INTO tickets (title, description, priority)
            VALUES (?, ?, ?)
            """,
            (title, description, priority)
        )

        connection.commit()
        connection.close()

        return redirect("/")

    return render_template("new_ticket.html")


@app.route("/update-status/<int:ticket_id>", methods=["POST"])
def update_status(ticket_id):
    status = request.form.get("status", "")

    allowed_statuses = {
        "Open",
        "In Progress",
        "Resolved"
    }

    if status not in allowed_statuses:
        return "Invalid status.", 400

    connection = get_connection()

    connection.execute(
        """
        UPDATE tickets
        SET status = ?
        WHERE id = ?
        """,
        (status, ticket_id)
    )

    connection.commit()
    connection.close()

    return redirect("/")


if __name__ == "__main__":
    init_database()
    app.run(debug=True)
