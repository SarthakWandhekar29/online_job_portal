
import smtplib
from email.message import EmailMessage
from flask import Flask, render_template, request, redirect, session, flash
from flask_mysqldb import MySQL
import sqlite3
app = Flask(__name__)
app.secret_key = "secretkey"

# ================= DATABASE =================
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'admin123'
app.config['MYSQL_DB'] = 'workconnect'

mysql = MySQL(app)

# ================= INDEX =================
@app.route('/')
def index():
    return render_template('index.html')
# ================= LOGIN =================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        role = request.form['role']
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()

        if role == "manager":
            cur.execute("SELECT * FROM managers WHERE email=%s AND password=%s", (email, password))
            user = cur.fetchone()
            if user:
                session.clear()
                session['manager_id'] = user[0]
                session['role'] = "manager"
                return redirect('/manager_dashboard')
            else:
                flash("Invalid Manager Credentials")

        elif role == "labour":
            cur.execute("SELECT * FROM labors WHERE email=%s AND password=%s", (email, password))
            user = cur.fetchone()
            if user:
                session.clear()
                session['labour_id'] = user[0]
                session['role'] = "labour"
                return redirect('/labour_dashboard')
            else:
                flash("Invalid Labour Credentials")

    return render_template('login.html')
# ================= MANAGER DASHBOARD =================
@app.route("/manager_dashboard")
def manager_dashboard():
    if "manager_id" not in session:
        return redirect("/login")

    manager_id = session["manager_id"]
    view = request.args.get("view", "labors")  # default = labors

    search = request.args.get("search")
    sort = request.args.get("sort")

    cur = mysql.connection.cursor()

    labors = []
    requests_data = []

    # =========================
    # SHOW AVAILABLE LABOURS
    # =========================
    if view == "labors":
        query = """
            SELECT id,
                   full_name,
                   age,
                   location,
                   primary_skills,
                   experience_years,
                   avilability,
                   expected_wage
            FROM labors
            WHERE 1=1
        """

        params = []

        if search:
            query += " AND primary_skills LIKE %s"
            params.append("%" + search + "%")

        if sort == "low":
            query += " ORDER BY expected_wage ASC"
        elif sort == "high":
            query += " ORDER BY expected_wage DESC"

        cur.execute(query, tuple(params))
        labors = cur.fetchall()

    # =========================
    # SHOW REQUESTED LABOURS
    # =========================
    elif view == "requests":
        cur.execute("""
            SELECT applications.id,
                   labors.full_name,
                   labors.primary_skills,
                   applications.status
            FROM applications
            JOIN labors ON applications.labour_id = labors.id
            WHERE applications.manager_id = %s
        """, (manager_id,))

        requests_data = cur.fetchall()

    cur.close()

    return render_template(
        "manager_dashboard.html",
        labors=labors,
        requests=requests_data,
        view=view
    )
@app.route("/hire/<int:application_id>")
def hire(application_id):
    if "manager_id" not in session:
        return redirect("/login")

    cur = mysql.connection.cursor()

    cur.execute("""
        UPDATE applications
        SET status = 'Hired'
        WHERE id = %s
    """, (application_id,))

    mysql.connection.commit()
    cur.close()

    return redirect("/manager_dashboard?view=requests")


# ================= LABOUR DASHBOARD =================
@app.route('/labour_dashboard')
def labour_dashboard():
    if 'labour_id' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM managers")
    jobs = cur.fetchall()

    return render_template('labour_dashboard.html', jobs=jobs)



# ================= REGISTER =================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':

        role = request.form['role']
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()

        if role == "manager":

            company_name = request.form.get('company_name')
            company_location = request.form.get('company_location')
            job_title = request.form.get('job_title')
            working_time = request.form.get('working_time')
            job_type = request.form.get('job_type')
            required_skill = request.form.get('required_skills')
            daily_wage = request.form.get('daily_wage')

            cur.execute("""
                INSERT INTO managers 
                (company_name, company_location, job_title, working_time, job_type,
                 required_skill, daily_wage, email, password)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (company_name, company_location, job_title, working_time,
                  job_type, required_skill, daily_wage, email, password))

            mysql.connection.commit()
            flash("Manager Registered Successfully")
            return redirect('/login')

        # ===== LABOUR REGISTER =====
        elif role == "labour":
            full_name = request.form['full_name']
            age = request.form['age']
            location = request.form['location']
            primary_skills = request.form['primary_skills']
            experience_years = request.form['experience_years']
            avilability = request.form.get('avilability')
            expected_wage = request.form['expected_wage']

            cur.execute("""
                INSERT INTO labors
                (full_name, age, location, primary_skills, experience_years,
                 avilability, expected_wage, email, password)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (full_name, age, location, primary_skills,
                  experience_years, avilability,
                  expected_wage, email, password))

            mysql.connection.commit()
            flash("Labour Registered Successfully")
            return redirect('/login')

    return render_template('register.html')
@app.route('/contact/<int:labour_id>')
@app.route('/contact/<int:labour_id>', methods=['GET', 'POST'])
def contact(labour_id):

    if "manager_id" not in session:
        return redirect("/login")

    cur = mysql.connection.cursor()
    cur.execute("SELECT full_name, email FROM labors WHERE id=%s", (labour_id,))
    labour = cur.fetchone()

    if not labour:
        return "Labour not found"

    labour_name = labour[0]
    labour_email = labour[1]

    fixed_subject = "New Hiring Request from WorkConnect"

    if request.method == "POST":

        message_body = request.form['message']

        try:
            msg = EmailMessage()
            msg.set_content(message_body)

            msg["Subject"] = fixed_subject
            msg["From"] = "dnyaneshwarwandhekar732@gmail.com"
            msg["To"] = labour_email

            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login("dnyaneshwarwandhekar732@gmail.com", "iibu fepj rdpa airh")
                server.send_message(msg)

            # 👇 Instead of flash, send success flag
            return render_template("contact.html",
                                   labour_name=labour_name,
                                   labour_email=labour_email,
                                   subject=fixed_subject,
                                   success=True)

        except Exception as e:
            return f"Email Error: {e}"

    return render_template("contact.html",
                           labour_name=labour_name,
                           labour_email=labour_email,
                           subject=fixed_subject)

@app.route("/apply/<int:manager_id>", methods=["POST"])
def apply(manager_id):

    if "labour_id" not in session:
        return redirect("/login")

    labour_id = session["labour_id"]

    conn = mysql.connection
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO applications (labour_id, manager_id, job_id)
            VALUES (%s, %s, %s)
        """, (labour_id, manager_id, manager_id))

        conn.commit()

    except Exception as e:
        print(e)

    return redirect("/labour_dashboard")
# ================= LOGOUT =================
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)