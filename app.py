import os
import joblib

from flask import Flask, request, jsonify,render_template
from db import get_db_connection
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "ml_model")

performance_model = joblib.load(
    os.path.join(MODEL_DIR, "performance_model.pkl")
)

risk_model = joblib.load(
    os.path.join(MODEL_DIR, "risk_model.pkl")
)



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


@app.route("/analytics")
def dashboard_analytics():
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                COUNT(*) AS total_students,
                COALESCE(ROUND(AVG(marks), 2), 0) AS average_marks,
                COALESCE(ROUND(AVG(attendance), 2), 0) AS average_attendance,
                COALESCE(SUM(CASE WHEN attendance < 75 THEN 1 ELSE 0 END), 0)
                    AS low_attendance_students
            FROM students
        """)

        analytics = cursor.fetchone()

        return jsonify(analytics), 200

    except Exception as e:
        app.logger.exception("Analytics API failed")
        return jsonify({"error": "Analytics load nahi ho paya"}), 500

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

            
@app.route("/students/<int:student_id>/ai-prediction", methods=["GET"])
def ai_prediction(student_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT id, full_name, marks, attendance FROM students WHERE id = %s",
            (student_id,)
        )
        student = cursor.fetchone()

        if not student:
            return jsonify({"error": "Student not found"}), 404

        cursor.execute(
            """
            SELECT AVG(marks) AS assessment_average
            FROM assessment_history
            WHERE student_id = %s
            """,
            (student_id,)
        )
        result = cursor.fetchone()

        assessment_average = result["assessment_average"]
        if assessment_average is None:
            assessment_average = student["marks"]

        features = [[
            float(student["attendance"] or 0),
            float(student["marks"] or 0),
            float(assessment_average)
        ]]

        predicted_marks = float(performance_model.predict(features)[0])
        risk_level = str(risk_model.predict(features)[0])

        return jsonify({
            "student_name": student["full_name"],
            "current_marks": student["marks"],
            "attendance": student["attendance"],
            "predicted_marks": round(predicted_marks, 2),
            "risk_level": risk_level
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()










if __name__ == "__main__":
    app.run(debug=True)
