
import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", ""),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "smart_student_db"),
        charset="utf8",
        connection_timeout=5
    )


if __name__ == "__main__":
    connection = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES")

        print("MySQL connected successfully!")
        print("Tables in smart_student_db:")

        for table in cursor.fetchall():
            print(table[0])

        cursor.close()

    except mysql.connector.Error as error:
        print("Connection failed:", error)

    finally:
        if connection is not None and connection.is_connected():
            connection.close()
