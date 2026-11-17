
import getpass
import mysql.connector
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

username = input("Enter admin username: ").strip()
password = getpass.getpass("Enter admin password: ")

if not username or not password:
    print("Username and password cannot be empty.")
    raise SystemExit

password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="smart_student_db",
        charset="utf8"
    )

    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO admins (username, password_hash) VALUES (%s, %s)",
        (username, password_hash)
    )
    conn.commit()
    print("Admin account created successfully!")

except mysql.connector.Error as error:
    print("Database error:", error)

finally:
    if "cursor" in locals():
        cursor.close()
    if "conn" in locals() and conn.is_connected():
        conn.close()
