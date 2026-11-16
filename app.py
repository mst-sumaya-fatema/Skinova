
from flask import Flask, render_template, request, redirect, url_for, session
from database_connection import create_connection
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "skinova_secret_key_2026"


# HOME
@app.route('/')
def home():
    return render_template('welcome page.html')


# USER LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():

    message = request.args.get('message', '')

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        connection = create_connection()

        if connection:
            cursor = connection.cursor()

            try:
                cursor.execute(
                    "SELECT User_ID, Name, Email, Password FROM users WHERE Email = %s",
                    (email,)
                )

                user = cursor.fetchone()

                if user and check_password_hash(user[3], password):

                    session.clear()
                    session['user_id'] = user[0]
                    session['user_name'] = user[1]

                    return redirect(url_for('dashboard'))

                else:
                    message = "Invalid email or password!"

            except Exception as error:
                print("Login Error:", error)
                message = "Something went wrong. Please try again."

            finally:
                cursor.close()
                connection.close()

        else:
            message = "Database connection failed!"

    return render_template('login.html', message=message)


# USER REGISTRATION
@app.route('/register', methods=['GET', 'POST'])
def register():

    message = ""

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            message = "Passwords do not match!"
            return render_template('register.html', message=message)

        connection = create_connection()

        if connection:
            cursor = connection.cursor()

            try:
                cursor.execute(
                    "SELECT * FROM users WHERE Email = %s",
                    (email,)
                )

                existing_user = cursor.fetchone()

                if existing_user:
                    message = "This email is already registered!"

                else:
                    hashed_password = generate_password_hash(password)

                    cursor.execute(
                        "INSERT INTO users (Name, Email, Password) VALUES (%s, %s, %s)",
                        (name, email, hashed_password)
                    )

                    new_user_id = cursor.lastrowid

                    connection.commit()

                    # AUTOMATIC LOGIN AFTER REGISTRATION
                    session.clear()
                    session['user_id'] = new_user_id
                    session['user_name'] = name

                    return redirect(url_for('dashboard'))

            except Exception as error:
                connection.rollback()
                print("Registration Error:", error)
                message = "Something went wrong. Please try again."

            finally:
                cursor.close()
                connection.close()

        else:
            message = "Database connection failed!"

    return render_template('register.html', message=message)


# USER DASHBOARD
@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    return render_template('dashboard.html')


# SKINCARE LIBRARY
@app.route('/skincare-library')
def skincare_library():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    return render_template('skincare_library.html')


# PRODUCT SUGGESTIONS
@app.route('/product-suggestions')
def product_suggestions():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    return render_template('product_suggestions.html')


# SKIN REQUEST SYSTEM
@app.route('/skin-request', methods=['GET', 'POST'])
def skin_request():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':

        age = request.form.get('age')

        skin_types = request.form.getlist('skin_type')
        skin_concerns = request.form.getlist('skin_concern')

        other_skin_type = request.form.get('other_skin_type', '').strip()
        other_skin_concern = request.form.get('other_skin_concern', '').strip()

        question = request.form.get('question', '').strip()
        current_routine = request.form.get('current_routine', '').strip()

        if other_skin_type:
            skin_types.append(other_skin_type)

        if other_skin_concern:
            skin_concerns.append(other_skin_concern)

        # Remove empty and duplicate values
        skin_types = list(dict.fromkeys(
            item.strip() for item in skin_types if item.strip()
        ))

        skin_concerns = list(dict.fromkeys(
            item.strip() for item in skin_concerns if item.strip()
        ))

        if not question or not current_routine:
            return "Question and Current Skincare Routine are required!"

        try:
            age = int(age) if age else None
        except ValueError:
            return "Please enter a valid age!"

        connection = create_connection()

        if connection:
            cursor = connection.cursor()

            try:
                # Save the main request
                cursor.execute(
                    """
                    INSERT INTO skin_requests
                    (User_ID, Age, Question, Current_Routine)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        session['user_id'],
                        age,
                        question,
                        current_routine
                    )
                )

                # Get the new Request ID
                request_id = cursor.lastrowid

                # Save selected skin types
                for skin_type in skin_types:

                    cursor.execute(
                        """
                        INSERT IGNORE INTO skin_types (Type_Name)
                        VALUES (%s)
                        """,
                        (skin_type,)
                    )

                    cursor.execute(
                        """
                        SELECT Skin_Type_ID
                        FROM skin_types
                        WHERE Type_Name = %s
                        """,
                        (skin_type,)
                    )

                    type_data = cursor.fetchone()

                    if type_data:
                        cursor.execute(
                            """
                            INSERT INTO request_skin_types
                            (Request_ID, Skin_Type_ID)
                            VALUES (%s, %s)
                            """,
                            (request_id, type_data[0])
                        )

                # Save selected skin concerns
                for concern in skin_concerns:

                    cursor.execute(
                        """
                        INSERT IGNORE INTO skin_concerns (Concern_Name)
                        VALUES (%s)
                        """,
                        (concern,)
                    )

                    cursor.execute(
                        """
                        SELECT Concern_ID
                        FROM skin_concerns
                        WHERE Concern_Name = %s
                        """,
                        (concern,)
                    )

                    concern_data = cursor.fetchone()

                    if concern_data:
                        cursor.execute(
                            """
                            INSERT INTO request_skin_concerns
                            (Request_ID, Concern_ID)
                            VALUES (%s, %s)
                            """,
                            (request_id, concern_data[0])
                        )

                connection.commit()

                return """
                <h2>Your Skin Request Submitted Successfully!</h2>
                <p>Your request has been saved.</p>
                <a href="/dashboard">Back to Dashboard</a>
                """

            except Exception as error:
                connection.rollback()
                print("Skin Request Error:", error)
                return "Something went wrong. Please try again."

            finally:
                cursor.close()
                connection.close()

        else:
            return "Database connection failed!"

    return render_template('skin_request.html')


# MY GUIDANCE
@app.route('/my-guidance')
def my_guidance():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    requests_list = []

    connection = create_connection()

    if connection:
        cursor = connection.cursor()

        try:
            cursor.execute(
                """
                SELECT
                    sr.Request_ID,
                    sr.Question,

                    (
                        SELECT GROUP_CONCAT(st.Type_Name SEPARATOR ', ')
                        FROM request_skin_types rst
                        JOIN skin_types st
                        ON rst.Skin_Type_ID = st.Skin_Type_ID
                        WHERE rst.Request_ID = sr.Request_ID
                    ) AS Skin_Type,

                    (
                        SELECT GROUP_CONCAT(sc.Concern_Name SEPARATOR ', ')
                        FROM request_skin_concerns rsc
                        JOIN skin_concerns sc
                        ON rsc.Concern_ID = sc.Concern_ID
                        WHERE rsc.Request_ID = sr.Request_ID
                    ) AS Skin_Concern,

                    sr.Current_Routine,
                    sr.Status,
                    r.Guidance

                FROM skin_requests sr

                JOIN recommendations r
                ON sr.Request_ID = r.Request_ID

                WHERE sr.User_ID = %s
                ORDER BY sr.Submitted_At DESC
                """,
                (session['user_id'],)
            )

            requests_list = cursor.fetchall()

        except Exception as error:
            print("My Guidance Error:", error)

        finally:
            cursor.close()
            connection.close()

    return render_template(
        'my_guidance.html',
        requests=requests_list
    )


# MY REQUESTS
@app.route('/my-requests')
def my_requests():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    requests_list = []

    connection = create_connection()

    if connection:
        cursor = connection.cursor()

        try:
            cursor.execute(
                """
                SELECT
                    sr.Request_ID,
                    sr.Age,

                    (
                        SELECT GROUP_CONCAT(st.Type_Name SEPARATOR ', ')
                        FROM request_skin_types rst
                        JOIN skin_types st
                        ON rst.Skin_Type_ID = st.Skin_Type_ID
                        WHERE rst.Request_ID = sr.Request_ID
                    ) AS Skin_Type,

                    (
                        SELECT GROUP_CONCAT(sc.Concern_Name SEPARATOR ', ')
                        FROM request_skin_concerns rsc
                        JOIN skin_concerns sc
                        ON rsc.Concern_ID = sc.Concern_ID
                        WHERE rsc.Request_ID = sr.Request_ID
                    ) AS Skin_Concern,

                    sr.Question,
                    sr.Current_Routine,
                    sr.Status,
                    sr.Submitted_At

                FROM skin_requests sr

                WHERE sr.User_ID = %s
                ORDER BY sr.Submitted_At DESC
                """,
                (session['user_id'],)
            )

            requests_list = cursor.fetchall()

        except Exception as error:
            print("My Requests Error:", error)

        finally:
            cursor.close()
            connection.close()

    return render_template(
        'my_requests.html',
        requests=requests_list
    )


# ADMIN LOGIN
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():

    message = ""

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        connection = create_connection()

        if connection:
            cursor = connection.cursor()

            try:
                cursor.execute(
                    "SELECT Admin_ID, Admin_Name, Password FROM admins WHERE Email = %s",
                    (email,)
                )

                admin = cursor.fetchone()

                if admin and check_password_hash(admin[2], password):

                    session.clear()
                    session['admin_id'] = admin[0]
                    session['admin_name'] = admin[1]

                    return redirect(url_for('admin_dashboard'))

                else:
                    message = "Invalid admin email or password!"

            except Exception as error:
                print("Admin Login Error:", error)
                message = "Something went wrong. Please try again."

            finally:
                cursor.close()
                connection.close()

        else:
            message = "Database connection failed!"

    return render_template('admin_login.html', message=message)


# ADMIN DASHBOARD
@app.route('/admin-dashboard')
def admin_dashboard():

    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    requests_list = []

    connection = create_connection()

    if connection:
        cursor = connection.cursor()

        try:
            cursor.execute(
                """
                SELECT
                    sr.Request_ID,
                    u.Name,
                    u.Email,
                    sr.Age,

                    (
                        SELECT GROUP_CONCAT(st.Type_Name SEPARATOR ', ')
                        FROM request_skin_types rst
                        JOIN skin_types st
                        ON rst.Skin_Type_ID = st.Skin_Type_ID
                        WHERE rst.Request_ID = sr.Request_ID
                    ) AS Skin_Type,

                    (
                        SELECT GROUP_CONCAT(sc.Concern_Name SEPARATOR ', ')
                        FROM request_skin_concerns rsc
                        JOIN skin_concerns sc
                        ON rsc.Concern_ID = sc.Concern_ID
                        WHERE rsc.Request_ID = sr.Request_ID
                    ) AS Skin_Concern,

                    sr.Question,
                    sr.Current_Routine,
                    sr.Status,
                    sr.Submitted_At

                FROM skin_requests sr

                JOIN users u
                ON sr.User_ID = u.User_ID

                ORDER BY sr.Submitted_At DESC
                """
            )

            requests_list = cursor.fetchall()

        except Exception as error:
            print("Admin Dashboard Error:", error)

        finally:
            cursor.close()
            connection.close()

    return render_template(
        'admin_dashboard.html',
        requests=requests_list
    )


# ADMIN GIVE GUIDANCE
@app.route('/give-guidance', methods=['POST'])
def give_guidance():

    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    request_id = request.form.get('request_id')
    guidance = request.form.get('guidance', '').strip()

    if not request_id or not guidance:
        return "Request ID and Guidance are required!"

    connection = create_connection()

    if connection:
        cursor = connection.cursor()

        try:
            cursor.execute(
                "SELECT Request_ID FROM skin_requests WHERE Request_ID = %s",
                (request_id,)
            )

            skin_request_data = cursor.fetchone()

            if not skin_request_data:
                return "Skin Request not found!"

            cursor.execute(
                "SELECT Recommendation_ID FROM recommendations WHERE Request_ID = %s",
                (request_id,)
            )

            existing_guidance = cursor.fetchone()

            if existing_guidance:
                return "Guidance has already been submitted for this request!"

            cursor.execute(
                """
                INSERT INTO recommendations
                (Request_ID, Admin_ID, Guidance)
                VALUES (%s, %s, %s)
                """,
                (
                    request_id,
                    session['admin_id'],
                    guidance
                )
            )

            cursor.execute(
                """
                UPDATE skin_requests
                SET Status = 'Completed'
                WHERE Request_ID = %s
                """,
                (request_id,)
            )

            connection.commit()

            return redirect(url_for('admin_dashboard'))

        except Exception as error:
            connection.rollback()
            print("Guidance Error:", error)
            return "Could not submit guidance. Please try again."

        finally:
            cursor.close()
            connection.close()

    else:
        return "Database connection failed!"


# ADMIN LOGOUT
@app.route('/admin-logout')
def admin_logout():

    session.clear()

    return redirect(url_for('admin_login'))


# USER LOGOUT
@app.route('/logout')
def logout():

    session.clear()

    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
