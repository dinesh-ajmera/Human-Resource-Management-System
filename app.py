from db_connection.connections import  cursor ,cnx
from flask import Flask , render_template , request ,session , redirect , url_for ,flash
import hashlib
import os

def hash_password(password, salt):
    # Combine password and salt, then hash using SHA-256
    combined = password + salt
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()

app = Flask(__name__)
app.secret_key = 'your_super_secret_key_here'
@app.route("/signup" , methods=['POST','GET'])
def signup():
    # # if session.get('role')!= 'HR':
    # #     return " you don't have admin privilages"
    # else:
        # if request.method=='POST':
            commpony_name = request.form.get("comp_name")
            first_name= request.form.get("f_name")
            last_name=request.form.get("l_name")
            email=request.form.get("email")
            passwd=request.form.get("password")
            mob_num=request.form.get("mob_num")
            
            role=request.form.get("role")
            salt = os.urandom(16).hex()
            password_hash = hash_password(passwd, salt)
            print(mob_num,passwd, commpony_name , first_name , last_name , email ,salt, len(password_hash))
            
            cursor.execute("INSERT INTO users (comp_name ,f_name ,l_name ,email , salt ,password , mob_nu , role)"
                f"VALUES ('{commpony_name}' ,'{first_name}' ,'{last_name}' ,'{email}' ,'{salt}','{password_hash}' ,'{mob_num}' ,'{role}')")
            cnx.commit()
        
            print("data insterted")
            flash(f"user is created you are an {role}")
            return redirect(url_for('admin_dashboard'))
            
                # return "user is not creaed somtion done worng"
        # else :
        #     return redirect(url_for('login'))

@app.route("/login" , methods=['POST','GET'])
def login():
    if request.method=='POST':
        email=request.form.get("email")
        passwd=request.form.get("password")
        
        role=request.form.get("role")
        cursor=cnx.cursor(dictionary=True)
        cursor.execute(f"select password , salt , role , user_id from users where email = '{email}' " )
        user=cursor.fetchone()
        # print(user['salt'])
        if not user:
            return "user is not exist "
        provided_hash = hash_password(passwd, user['salt'])
        if provided_hash == user['password']:
            if user['role']== 'HR':
                session['UID']=user['user_id']
                session['role']=user['role']
                return redirect(url_for('admin_dashboard'))
            elif user['role']== 'employee':
                session['UID']=user['user_id']
                session['role']=user['role']
                return redirect(url_for('employee_dashboard'))
            else:
                return " invalide user passwd and email "
        
    else :
        return render_template("index.html")

@app.route('/time_off')
def time_off():
    return render_template("time_off.html")

@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('role') !='HR':
        flash("your are not an admin !! alert")
        return redirect(url_for('login'))
    cursor.execute(f"select * from users where user_id = '{session.get('UID')}' " )
    profile_data = cursor.fetchone()
    cursor.execute(f"select  f_name ,email, l_name  from users  " )
    empls_data = cursor.fetchall()
    # print(empls_data[1]['comp_name'])
    # print(profile_data)

    # return f"Authentication successful! Welcome back {user['role']} your user id is {user['user_id']}."
    return render_template("HR_dashboard.html", your_data = profile_data, empls_data = empls_data)

@app.route('/employee_dashboard')
def employee_dashboard():
    cursor.execute(f"select * from users where user_id = '{session.get('UID')}' " )
    profile_data = cursor.fetchone()
    cursor.execute(f"select  f_name ,email, l_name  from users where role = 'employee' " )
    empls_data = cursor.fetchall()
    # print(empls_data[1]['comp_name'])
    # print(profile_data)

    # return f"Authentication successful! Welcome back {user['role']} your user id is {user['user_id']}."
    return render_template("employees.html", your_data = profile_data, empls_data = empls_data)


if __name__=='__main__':
    app.run(debug=True , port=5000)
    

