from database_connection import create_connection

connection = create_connection()

if connection:
    print("Skinova Database Connected Successfully!")
    connection.close()
else:
    print("Database Connection Failed!")