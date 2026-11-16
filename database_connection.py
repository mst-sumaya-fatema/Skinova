import mysql.connector

def create_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Theclicks2024",
            database="skinova_database",
            port=3306
        )

        return connection

    except mysql.connector.Error as error:
        print("Database Connection Error:", error)
        return None