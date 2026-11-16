
from database_connection import create_connection
from werkzeug.security import generate_password_hash
from getpass import getpass

print("Create Skinova Main Admin Account")

admin_name = "Skinova Admin"
email = "mstsumayafatema24@gmail.com"

password = getpass("Create Admin Password: ")
confirm_password = getpass("Confirm Admin Password: ")

if password != confirm_password:
    print("Passwords do not match!")

else:
    connection = create_connection()

    if connection:
        cursor = connection.cursor()

        try:
            cursor.execute(
                "SELECT Admin_ID FROM admins WHERE Email = %s",
                (email,)
            )

            existing_admin = cursor.fetchone()

            if existing_admin:
                print("This Admin account already exists!")

            else:
                hashed_password = generate_password_hash(password)

                cursor.execute(
                    """
                    INSERT INTO admins
                    (Admin_Name, Email, Password)
                    VALUES (%s, %s, %s)
                    """,
                    (admin_name, email, hashed_password)
                )

                connection.commit()

                print("Main Admin Account Created Successfully!")

        except Exception as error:
            print("Error:", error)

        finally:
            cursor.close()
            connection.close()

    else:
        print("Database connection failed!")
