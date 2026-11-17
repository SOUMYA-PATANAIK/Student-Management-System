
from flask import Flask, request, jsonify,render_template
from db import get_db_connection

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/db-check")
def db_check():
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM students")
        count = cursor.fetchone()[0]

        return f"MySQL connected successfully! Total students: {count}"

    except Exception:
        app.logger.exception("Database check failed")
        return "Database check failed. Please check the VS Code terminal.", 500

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

            
@app.route("/students", methods=["POST"])
def add_student():
    data = request.get_json(silent=True) or {}

    roll_number = data.get("roll_number")
    full_name = data.get("full_name")
    email = data.get("email")
    course = data.get("course")

    if not roll_number or not full_name or not course:
        return jsonify({
            "error": "Roll number, full name and course are required"
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
            INSERT INTO students
            (roll_number, full_name, email, course)
            VALUES (%s, %s, %s, %s)
        """

        cursor.execute(
            query, (roll_number, full_name, email, course)
        )
        connection.commit()

        return jsonify({
            "message": "Student added successfully",
            "student_id": cursor.lastrowid
        }), 201

    except Exception:
        if connection is not None:
            connection.rollback()

        app.logger.exception("Student creation failed")
        return jsonify({"error": "Could not add student. Check terminal."}), 400

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

            
@app.route("/students", methods=["GET"])
def get_students():
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, roll_number, full_name, email,
                   course, marks, attendance
            FROM students
            ORDER BY id
        """)

        students = cursor.fetchall()
        return jsonify(students), 200

    except Exception:
        app.logger.exception("Fetching students failed")
        return jsonify({"error": "Could not fetch students"}), 500

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()

            
@app.route("/students/<int:student_id>", methods=["PUT"])
def update_student(student_id):
    data = request.get_json(silent=True) or {}

    full_name = data.get("full_name")
    email = data.get("email")
    course = data.get("course")

    if not full_name or not course:
        return jsonify({
            "error": "Full name and course are required"
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE students
            SET full_name = %s,
                email = %s,
                course = %s,
                updated_at = NOW()
            WHERE id = %s
            """,
            (full_name, email, course, student_id)
        )

        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({
                "error": "Student not found or no changes made"
            }), 404

        return jsonify({
            "message": "Student updated successfully",
            "student_id": student_id
        }), 200

    except Exception:
        if connection is not None:
            connection.rollback()

        app.logger.exception("Student update failed")
        return jsonify({
            "error": "Could not update student. Check terminal."
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()
            
@app.route("/students/<int:student_id>/assessments", methods=["POST"])
def add_assessment(student_id):
    data = request.get_json(silent=True) or {}

    assessment_name = data.get("assessment_name")
    marks = data.get("marks")
    assessment_date = data.get("assessment_date")

    if not assessment_name or marks is None or not assessment_date:
        return jsonify({
            "error": "Assessment name, marks and date are required"
        }), 400

    try:
        marks = float(marks)
    except (TypeError, ValueError):
        return jsonify({"error": "Marks must be a number"}), 400

    if not 0 <= marks <= 100:
        return jsonify({"error": "Marks must be between 0 and 100"}), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT id FROM students WHERE id = %s",
            (student_id,)
        )

        if cursor.fetchone() is None:
            return jsonify({"error": "Student not found"}), 404

        cursor.execute("""
            INSERT INTO assessment_history
                (student_id, assessment_name, marks, assessment_date)
            VALUES (%s, %s, %s, %s)
        """, (student_id, assessment_name.strip(), marks, assessment_date))

        connection.commit()

        return jsonify({
            "message": "Assessment added successfully"
        }), 201

    except Exception:
        if connection is not None:
            connection.rollback()

        app.logger.exception("Assessment creation failed")
        return jsonify({"error": "Could not save assessment"}), 500

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

            
@app.route("/students/<int:student_id>/assessments", methods=["GET"])
def get_assessments(student_id):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT id FROM students WHERE id = %s",
            (student_id,)
        )
        if cursor.fetchone() is None:
            return jsonify({"error": "Student not found"}), 404

        cursor.execute("""
            SELECT id, assessment_name, marks, assessment_date
            FROM assessment_history
            WHERE student_id = %s
            ORDER BY assessment_date DESC, id DESC
        """, (student_id,))

        assessments = cursor.fetchall()
        return jsonify(assessments), 200

    except Exception:
        app.logger.exception("Assessment history retrieval failed")
        return jsonify({"error": "Could not fetch assessment history"}), 500

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()
            
@app.route("/students/<int:student_id>/report", methods=["GET"])
def student_report(student_id):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, roll_number, full_name, email, course,
                   marks, attendance
            FROM students
            WHERE id = %s
        """, (student_id,))

        student = cursor.fetchone()

        if student is None:
            return jsonify({"error": "Student not found"}), 404

        cursor.execute("""
            SELECT assessment_name, marks, assessment_date
            FROM assessment_history
            WHERE student_id = %s
            ORDER BY assessment_date DESC, id DESC
        """, (student_id,))

        assessments = cursor.fetchall()

        average = (
            sum(float(a["marks"]) for a in assessments) / len(assessments)
            if assessments else 0
        )

        return jsonify({
            "student": student,
            "assessments": assessments,
            "assessment_count": len(assessments),
            "assessment_average": round(average, 2)
        }), 200

    except Exception:
        app.logger.exception("Student report generation failed")
        return jsonify({"error": "Could not generate report"}), 500

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()

            
@app.route("/students/<int:student_id>/attendance", methods=["POST"])
def mark_attendance(student_id):
    data = request.get_json(silent=True) or {}

    attendance_date = data.get("attendance_date")
    status = data.get("status")

    if not attendance_date or status not in ["Present", "Absent"]:
        return jsonify({
            "error": "Valid date and status (Present/Absent) are required"
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT id FROM students WHERE id = %s",
            (student_id,)
        )

        if cursor.fetchone() is None:
            return jsonify({"error": "Student not found"}), 404

        cursor.execute("""
            INSERT INTO attendance_history
                (student_id, attendance_date, status)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE status = %s
        """, (student_id, attendance_date, status, status))

        connection.commit()

        return jsonify({
            "message": "Attendance marked successfully",
            "student_id": student_id,
            "attendance_date": attendance_date,
            "status": status
        }), 200

    except Exception:
        if connection is not None:
            connection.rollback()
        app.logger.exception("Attendance marking failed")
        return jsonify({"error": "Could not save attendance"}), 500

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()




            


@app.route("/students/<int:student_id>/academic", methods=["PUT"])
def update_academic_record(student_id):
    data = request.get_json(silent=True) or {}

    marks = data.get("marks")
    attendance = data.get("attendance")

    if marks is None or attendance is None:
        return jsonify({
            "error": "Marks and attendance are required"
        }), 400

    try:
        marks = float(marks)
        attendance = float(attendance)
    except (TypeError, ValueError):
        return jsonify({
            "error": "Marks and attendance must be numbers"
        }), 400

    if not 0 <= marks <= 100 or not 0 <= attendance <= 100:
        return jsonify({
            "error": "Marks and attendance must be between 0 and 100"
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE students
            SET marks = %s,
                attendance = %s,
                updated_at = NOW()
            WHERE id = %s
            """,
            (marks, attendance, student_id)
        )

        if cursor.rowcount == 0:
            cursor.execute(
                "SELECT id FROM students WHERE id = %s",
                (student_id,)
            )
            if cursor.fetchone() is None:
                return jsonify({
                    "error": "Student not found"
                }), 404

        connection.commit()

        return jsonify({
            "message": "Marks and attendance updated successfully",
            "student_id": student_id,
            "marks": marks,
            "attendance": attendance
        }), 200

    except Exception:
        if connection is not None:
            connection.rollback()

        app.logger.exception("Academic record update failed")
        return jsonify({
            "error": "Could not update academic record"
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()



            
@app.route("/students/<int:student_id>", methods=["DELETE"])
def delete_student(student_id):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "DELETE FROM students WHERE id = %s",
            (student_id,)
        )

        if cursor.rowcount == 0:
            return jsonify({
                "error": "Student not found"
            }), 404

        connection.commit()

        return jsonify({
            "message": "Student deleted successfully",
            "student_id": student_id
        }), 200

    except Exception:
        if connection is not None:
            connection.rollback()

        app.logger.exception("Student deletion failed")
        return jsonify({
            "error": "Could not delete student"
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()
            
@app.route("/attendance")
def attendance_page():
    return render_template("attendance.html")


@app.route("/report-card/<int:student_id>")
def report_card_page(student_id):
    return render_template("report_card.html", student_id=student_id)








if __name__ == "__main__":
    app.run(debug=True)
