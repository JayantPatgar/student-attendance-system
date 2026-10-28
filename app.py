from flask import Flask, render_template, request, redirect, url_for, session
from database import get_db_connection
from datetime import date
from werkzeug.security import check_password_hash

app = Flask(__name__)

app.secret_key = __import__("os").environ.get("SECRET_KEY", "dev-only-change-this-secret-key")


# =========================
# LOGIN
# =========================
# =========================
# LOGIN
# =========================

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT *
            FROM admin
            WHERE username = %s
            """,
            (username,)
        )

        admin = cursor.fetchone()

        cursor.close()
        connection.close()

        if admin and check_password_hash(
            admin["password"],
            password
        ):

            session["admin_id"] = admin["id"]
            session["username"] = admin["username"]

            return redirect(
                url_for("dashboard")
            )

        return render_template(
            "login.html",
            error="Invalid username or password"
        )

    return render_template("login.html")


# =========================
# DASHBOARD
# =========================

@app.route("/dashboard")
def dashboard():

    if "admin_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM students"
    )

    total_students = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM attendance
        WHERE date = CURDATE()
        AND status = 'Present'
        """
    )

    present_today = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM attendance
        WHERE date = CURDATE()
        AND status = 'Absent'
        """
    )

    absent_today = cursor.fetchone()[0]

    total_attendance = present_today + absent_today

    if total_attendance > 0:

        attendance_percentage = round(
            (present_today / total_attendance) * 100
        )

    else:

        attendance_percentage = 0

    cursor.close()
    connection.close()

    return render_template(
        "dashboard.html",
        username=session["username"],
        total_students=total_students,
        present_today=present_today,
        absent_today=absent_today,
        attendance_percentage=attendance_percentage
    )


# =========================
# ADD STUDENT
# =========================

@app.route("/add-student", methods=["GET", "POST"])
def add_student():

    if "admin_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        course = request.form["course"]
        semester = request.form["semester"]

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO students
            (name, email, phone, course, semester)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                name,
                email,
                phone,
                course,
                semester
            )
        )

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(url_for("students"))

    return render_template("add_student.html")


# =========================
# VIEW + SEARCH STUDENTS
# =========================

@app.route("/students")
def students():

    if "admin_id" not in session:
        return redirect(url_for("login"))

    search = request.args.get(
        "search",
        ""
    ).strip()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    if search:

        search_value = f"%{search}%"

        cursor.execute(
            """
            SELECT *
            FROM students

            WHERE name LIKE %s
               OR email LIKE %s
               OR phone LIKE %s
               OR course LIKE %s

            ORDER BY id ASC
            """,
            (
                search_value,
                search_value,
                search_value,
                search_value
            )
        )

    else:

        cursor.execute(
            """
            SELECT *
            FROM students
            ORDER BY id ASC
            """
        )

    students = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "students.html",
        students=students,
        search=search
    )


# =========================
# EDIT STUDENT
# =========================

@app.route(
    "/edit-student/<int:id>",
    methods=["GET", "POST"]
)
def edit_student(id):

    if "admin_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        course = request.form["course"]
        semester = request.form["semester"]

        cursor.execute(
            """
            UPDATE students

            SET
                name = %s,
                email = %s,
                phone = %s,
                course = %s,
                semester = %s

            WHERE id = %s
            """,
            (
                name,
                email,
                phone,
                course,
                semester,
                id
            )
        )

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(
            url_for("students")
        )

    cursor.execute(
        """
        SELECT *
        FROM students
        WHERE id = %s
        """,
        (id,)
    )

    student = cursor.fetchone()

    cursor.close()
    connection.close()

    if student is None:

        return "Student not found", 404

    return render_template(
        "edit_student.html",
        student=student
    )


# =========================
# DELETE STUDENT
# =========================
# =========================
# DELETE STUDENT
# =========================

@app.route("/delete-student/<int:id>")
def delete_student(id):

    if "admin_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        # Delete attendance records first
        cursor.execute(
            """
            DELETE FROM attendance
            WHERE student_id = %s
            """,
            (id,)
        )

        # Then delete the student
        cursor.execute(
            """
            DELETE FROM students
            WHERE id = %s
            """,
            (id,)
        )

        connection.commit()

    except Exception as e:

        connection.rollback()
        print("Delete error:", e)

    finally:

        cursor.close()
        connection.close()

    return redirect(
        url_for("students")
    )
# =========================
# MARK ATTENDANCE
# =========================

@app.route(
    "/attendance",
    methods=["GET", "POST"]
)
def attendance():

    if "admin_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    cursor.execute(
        """
        SELECT *
        FROM students
        ORDER BY name
        """
    )

    students = cursor.fetchall()

    if request.method == "POST":

        attendance_date = request.form["date"]

        for student in students:

            status = request.form.get(
                f"status_{student['id']}"
            )

            cursor.execute(
                """
                SELECT id
                FROM attendance

                WHERE student_id = %s
                AND date = %s
                """,
                (
                    student["id"],
                    attendance_date
                )
            )

            existing_record = cursor.fetchone()

            if existing_record:

                cursor.execute(
                    """
                    UPDATE attendance

                    SET status = %s

                    WHERE student_id = %s
                    AND date = %s
                    """,
                    (
                        status,
                        student["id"],
                        attendance_date
                    )
                )

            else:

                cursor.execute(
                    """
                    INSERT INTO attendance
                    (
                        student_id,
                        date,
                        status
                    )

                    VALUES
                    (
                        %s,
                        %s,
                        %s
                    )
                    """,
                    (
                        student["id"],
                        attendance_date,
                        status
                    )
                )

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(
            url_for("dashboard")
        )

    cursor.close()
    connection.close()

    return render_template(
        "attendance.html",
        students=students,
        today=date.today().isoformat()
    )


# =========================
# ATTENDANCE HISTORY
# =========================

@app.route("/attendance-history")
def attendance_history():

    if "admin_id" not in session:
        return redirect(url_for("login"))

    selected_date = request.args.get(
        "date",
        ""
    ).strip()

    connection = get_db_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    if selected_date:

        cursor.execute(
            """
            SELECT
                attendance.id,
                students.name,
                students.course,
                students.semester,
                attendance.date,
                attendance.status

            FROM attendance

            JOIN students
            ON attendance.student_id = students.id

            WHERE attendance.date = %s

            ORDER BY students.name
            """,
            (selected_date,)
        )

    else:

        cursor.execute(
            """
            SELECT
                attendance.id,
                students.name,
                students.course,
                students.semester,
                attendance.date,
                attendance.status

            FROM attendance

            JOIN students
            ON attendance.student_id = students.id

            ORDER BY
                attendance.date ASc,
                attendance.id ASC
            """
        )

    records = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "attendance_history.html",
        records=records,
        selected_date=selected_date
    )


# =========================
# STUDENT ATTENDANCE REPORT
# =========================
@app.route("/student-report")
def student_report():

    if "admin_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            s.id,
            s.name,
            s.course,
            s.semester,

            COUNT(a.id) AS total_classes,

            COALESCE(
                SUM(
                    CASE
                        WHEN a.status = 'Present'
                        THEN 1
                        ELSE 0
                    END
                ),
                0
            ) AS present_count,

            COALESCE(
                SUM(
                    CASE
                        WHEN a.status = 'Absent'
                        THEN 1
                        ELSE 0
                    END
                ),
                0
            ) AS absent_count

        FROM students AS s

        LEFT JOIN attendance AS a
        ON s.id = a.student_id

        GROUP BY
            s.id,
            s.name,
            s.course,
            s.semester

        ORDER BY s.id
    """)

    students = cursor.fetchall()

    cursor.close()
    connection.close()

    for student in students:

        total = int(student["total_classes"] or 0)
        present = int(student["present_count"] or 0)
        absent = int(student["absent_count"] or 0)

        student["total_classes"] = total
        student["present_count"] = present
        student["absent_count"] = absent

        if total > 0:
            student["percentage"] = round(
                (present / total) * 100,
                2
            )
        else:
            student["percentage"] = 0

    return render_template(
        "student_report.html",
        students=students
    )

# =========================
# STUDENT PROFILE
# =========================

@app.route("/student/<int:id>")
def student_profile(id):

    if "admin_id" not in session:
        return redirect(url_for("login"))

    connection = get_db_connection()

    cursor = connection.cursor(dictionary=True)

    # Get student details
    cursor.execute(
        """
        SELECT *
        FROM students
        WHERE id = %s
        """,
        (id,)
    )

    student = cursor.fetchone()

    if student is None:

        cursor.close()
        connection.close()

        return "Student not found", 404

    # Get attendance records
    cursor.execute(
        """
        SELECT
            id,
            date,
            status

        FROM attendance

        WHERE student_id = %s

        ORDER BY date ASC
        """,
        (id,)
    )

    attendance_records = cursor.fetchall()

    # Attendance counts
    total = len(attendance_records)

    present = sum(
        1
        for record in attendance_records
        if record["status"] == "Present"
    )

    absent = sum(
        1
        for record in attendance_records
        if record["status"] == "Absent"
    )

    # Attendance percentage
    if total > 0:

        percentage = round(
            (present / total) * 100,
            2
        )

    else:

        percentage = 0

    cursor.close()
    connection.close()

    return render_template(
        "student_profile.html",
        student=student,
        attendance_records=attendance_records,
        total=total,
        present=present,
        absent=absent,
        percentage=percentage
    )

# =========================
# MONTHLY ATTENDANCE REPORT
# =========================

@app.route("/monthly-report")
def monthly_report():

    if "admin_id" not in session:
        return redirect(url_for("login"))

    selected_month = request.args.get(
        "month",
        ""
    ).strip()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    if selected_month:

        cursor.execute(
            """
            SELECT
                s.id,
                s.name,
                s.course,
                s.semester,

                COUNT(a.id) AS total_classes,

                COALESCE(
                    SUM(
                        CASE
                            WHEN a.status = 'Present'
                            THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS present_count,

                COALESCE(
                    SUM(
                        CASE
                            WHEN a.status = 'Absent'
                            THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS absent_count

            FROM students s

            LEFT JOIN attendance a
            ON s.id = a.student_id
            AND DATE_FORMAT(a.date, '%Y-%m') = %s

            GROUP BY
                s.id,
                s.name,
                s.course,
                s.semester

            ORDER BY s.name
            """,
            (selected_month,)
        )

    else:

        cursor.execute(
            """
            SELECT
                s.id,
                s.name,
                s.course,
                s.semester,

                COUNT(a.id) AS total_classes,

                COALESCE(
                    SUM(
                        CASE
                            WHEN a.status = 'Present'
                            THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS present_count,

                COALESCE(
                    SUM(
                        CASE
                            WHEN a.status = 'Absent'
                            THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS absent_count

            FROM students s

            LEFT JOIN attendance a
            ON s.id = a.student_id

            GROUP BY
                s.id,
                s.name,
                s.course,
                s.semester

            ORDER BY s.name
            """
        )

    students = cursor.fetchall()

    cursor.close()
    connection.close()


    # Calculate percentage

    for student in students:

        total = int(
            student["total_classes"] or 0
        )

        present = int(
            student["present_count"] or 0
        )

        absent = int(
            student["absent_count"] or 0
        )

        student["total_classes"] = total
        student["present_count"] = present
        student["absent_count"] = absent

        if total > 0:

            student["percentage"] = round(
                (present / total) * 100,
                2
            )

        else:

            student["percentage"] = 0


    return render_template(
        "monthly_report.html",
        students=students,
        selected_month=selected_month
    )

# =========================
# EXPORT ATTENDANCE TO EXCEL
# =========================

@app.route("/export-attendance")
def export_attendance():

    if "admin_id" not in session:
        return redirect(url_for("login"))

    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment
    from io import BytesIO
    from flask import send_file

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            s.id,
            s.name,
            s.email,
            s.phone,
            s.course,
            s.semester,
            a.date,
            a.status

        FROM attendance a

        JOIN students s
        ON a.student_id = s.id

        ORDER BY a.date ASC, s.name
    """)

    records = cursor.fetchall()

    cursor.close()
    connection.close()

    # Create Excel workbook
    workbook = Workbook()

    sheet = workbook.active
    sheet.title = "Attendance Report"

    # Headers
    headers = [
        "Student ID",
        "Student Name",
        "Email",
        "Phone",
        "Course",
        "Semester",
        "Date",
        "Status"
    ]

    sheet.append(headers)

    # Style headers
    for cell in sheet[1]:

        cell.font = Font(bold=True)

        cell.alignment = Alignment(
            horizontal="center"
        )

    # Add records
    for record in records:

        sheet.append([
            record["id"],
            record["name"],
            record["email"],
            record["phone"],
            record["course"],
            record["semester"],
            record["date"],
            record["status"]
        ])

    # Column widths
    widths = {
        "A": 12,
        "B": 20,
        "C": 30,
        "D": 15,
        "E": 15,
        "F": 12,
        "G": 15,
        "H": 15
    }

    for column, width in widths.items():

        sheet.column_dimensions[
            column
        ].width = width

    # Save in memory
    output = BytesIO()

    workbook.save(output)

    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="attendance_report.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# =========================
# RUN APPLICATION
# =========================

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=int(__import__("os").environ.get("PORT", "5000")), debug=False)