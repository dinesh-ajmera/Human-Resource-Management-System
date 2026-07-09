from flask import Flask , request , render_template , redirect , url_for, session , flash
import models 
import config

app = Flask(__name__)
app.secret_key=config.secret_key

@app.route('/')
def welcome():
    if  models.cnx:
        if models.use_database():
            print('database is created  and connected ')
            session['db_status']=True
            return redirect(url_for('login'))
        else:
            return "some technical essues is there may be tables are not created is not connected "
    else: 
        session['db_status']=False
        flash("database is not connected ")
        return render_template("error.html")
    


@app.route('/signup' , methods=['POST','GET'])
def signup():
    if not session.get('db_status'):
        return redirect(url_for('welcome'))
    if session.get('role')=='employee':
        session.clear()
        return redirect(url_for('signup'))
    

    if request.method=="POST":
        first_name = request.form.get("fr_name")
        last_name = request.form.get("la_name")
        email = request.form.get("email")
        password = request.form.get("password")
        mob_nu = request.form.get("mob_num")
        role = request.form.get("role")
        # if not models.check_user_exist(email):
        #     flash("email is already available !!")
        #     return redirect(url_for('signup') , data="user exists")
        if any(not x or str(x).strip() == "" for x in [first_name , last_name , email , password, mob_nu , role]):
            flash("submited empty data !!")
            return redirect(url_for('signup'))
        try:
            password = models.generate_password_hash(password)
            query= "insert into users (f_name   , l_name  , email  , password  , mob_nu  , role ) values (%s ,%s ,%s ,%s,%s,%s)"
            values= (first_name , last_name , email , password , mob_nu , role)
            models.cursor.execute(query , values )
            models.cnx.commit()
            return redirect(url_for("login"))
        except models.mysql.connector.Error as err:
            if err.errno== 1062:
                print("error code 1062")
                return render_template("signup.html" , data="user exists")
            else:
                print(err)
                return render_template("signup.html")

    else:
        return render_template("signup.html")
   
        

@app.route('/login',methods=['POST','GET'])
def login():
    if request.method=='POST':
        email =request.form.get("email")
        password = request.form.get('password')
        result = models.authenticate_user(email, password)
        if result !=1:
            print(result[1])
            session['user_id']=result[1]
            session['role']= result[2]
            return redirect(url_for('dashboard'))
        else:
            flash("user is not exist")
            return render_template("login.html", data="Invalid email or password")
    else:
        return render_template("login.html")
    
@app.route('/dashboard')
def dashboard():
    if session.get('user_id'):

        print(session.get('user_id'))
        user_id = session.get('user_id')
        role = session.get('role')
        # models.cursor.execute("select role , f_name from users where user_id = %s", (user_id ,))
        # result = models.cursor.fetchone()
        if role=="HR":
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('employee_dashboard'))
    else:
        return redirect(url_for('login'))
@app.route('/logout', methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/employees')
def employee_dashboard():
    if session.get('role')=='employee':
        # return redirect(url_for('signup'))
        return render_template("employee_dashboard.html")
    else:
        return redirect(url_for('signup'))
    
@app.route('/leave', methods=['POST'])
def leave():
    if not session.get('user_id'):
        return redirect(url_for('login'))

    if request.method=='POST':
        start_date = request.form.get('start_date')
        print(start_date)

        end_date = request.form.get('end_date')
        employee_comment = request.form.get('employee_comment')
        if start_date and end_date:
            start_date = models.datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = models.datetime.strptime(end_date, "%Y-%m-%d").date()
        else:
            return redirect(url_for('dashboard'))
        
        today = models.date.today()
        if start_date >= today:
            if start_date >= end_date:
                print("dates are not valid")
                return "dates aer invalid start date must be lesser than end date"
            else:
                try:
                    print(start_date , end_date)
                    # query=("select start_date , end_date from leaves where employee_id =%s and status ='approved'")
                    # values=(session.get('user_id') , )
                    # models.cursor.execute(query , values)
                    # result = models.cursor.fetchone()
                    # print(result[0])
                    # if start_date<=result[0]:
                    #     if start_date==result[0] and end_date == result[1]:
                    #         return "leave for this time duration is already approved"
                    #     if start_date <= result[0] and end_date == result[1]:
                    #         return "is you want to expand your leave !! . lets check the compony police"
                    #     if start_date == result[0] and end_date >= result[1]:
                    #         return "is you want to expand your leave !! . lets check the compony police"

                        
                    # if end_date<=result[1]:
                    #     return "your privius leave is stilll not complete"


                    query=(" insert into leaves (employee_id ,start_date ,end_date ,comments_from_empl ) values (%s , %s ,%s ,%s)")
                    values=( session.get("user_id") , start_date , end_date , employee_comment)
                    models.cursor.execute(query , values)
                    models.cnx.commit()

                    return redirect(url_for('history'))
                except models.mysql.connector.Error as err:
                    print(err)
                    return "something goes wronge"
        else:
            return "you need to request atleast one day before the leave date start !! sorry"

@app.route("/leaves" , methods=["POST" , "get"])
def leaves():
    if session.get('role')=='HR':
        status_required=request.form.get("status")
        # session.get("user_id")
        query=("select leave_id , employee_id  , start_date ,end_date, comments_from_empl ,created_at   from leaves where status = %s")
        values=('pending' ,)
        models.cursor.execute(query , values)
        result = models.cursor.fetchall()
        print(result)
        if result:
            return render_template('leaves.html' , result=result)
        else:
            flash(" there is no leaves requests available . just chill bro !!!")
            return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))


@app.route('/admin_responce' , methods=['POST','GET'])
def admin_responce():
    if request.method=='POST':
        if session.get('role')=='HR':
            try:
                responce = request.form.get('responce')
                comment = request.form.get('comment')
                leave_id = request.form.get('leave_id')
                print(responce)
                print(comment)
                admin_id = session.get("user_id")
                query = (" update leaves set status =%s , comments_from_HR = %s , approved_by = %s  where leave_id =%s")
                value=(responce , comment ,admin_id ,   leave_id)
                models.cursor.execute(query , value)
                models.cnx.commit()
                flash(f"leave is {responce} successfully")
                return redirect(url_for('leaves'))
            
            except models.mysql.connector.Error as err:
                print(err)
                return " leave is not submit due to some technical essue"
        else:
            return redirect(url_for('login'))
    else:
            return redirect(url_for('login'))


@app.route('/admin', methods=["POST", 'GET'])
def admin_dashboard():
    
    if session.get('role')=='HR':
        
        
        # return redirect(url_for('signup'))
        return render_template("admin_dashboard.html")
    else:
        return redirect(url_for('login'))

    

@app.route('/history', methods=['POST' , 'GET'])
def history():
    # if request.method=='POST':
    if session.get("role")=='HR':
        query = (" select employee_id , approved_by ,comments_from_empl ,comments_from_HR ,last_updated_at ,start_date ,end_date , status from leaves where status != %s")
        value=('pending',)
        models.cursor.execute(query , value)
        result = models.cursor.fetchall()


        # return f"you will see all requests of all user where status is aproved or rejected {result}"
        return render_template('history_for_admin.html' , result=result)
    elif session.get("role")=='employee':
        query = (" select  approved_by ,comments_from_empl ,comments_from_HR ,last_updated_at ,start_date ,end_date , status from leaves where employee_id = %s")
        value=(session.get('user_id'),)
        models.cursor.execute(query , value)
        result = models.cursor.fetchall()
        return render_template('history_for_employee.html' , result=result)
    else:
        return redirect(url_for('dashboard'))
    
    
@app.route('/check_in' , methods=['POST' , "GET"])
def check_in():
    print(session.get("user_id"))
    if request.method=='POST':
        print(session.get("user_id"))
        if session.get("user_id"):
            try:
                query=(" select status from attendance where employee_id =%s and attendance =%s")
                value=(session.get("user_id") , models.date.today() )
                print(value)
                models.cursor.execute(query,value)
                result = models.cursor.fetchone()
                print(result)
                if  result:
                    return redirect(url_for('dashboard'))
                
                else:
                    employee_id = session.get("user_id")
                    status = 'present'
                    print(status)
                    query = (" insert into attendance (employee_id , status) values ( %s ,%s ) ")
                    value = (employee_id , status)
                    models.cursor.execute(query , value )
                    models.cnx.commit()
                    session['live_status']="live"
                    print('check in done')
                    return redirect(url_for('dashboard'))
            except models.mysql.connector.Error as err:
                print(err)
                return redirect(url_for('dashboard'))
        else:
            print("not loged in")
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))

@app.route('/check_out' , methods=['POST' , "GET"])
def check_out():
    if request.method=='POST':
        print(session.get("user_id"))
        if session.get("user_id"):
            try:
                query=(" select live_status from attendance where employee_id =%s and attendance =%s")
                value=(session.get("user_id") , models.date.today() )
                print(value)
                models.cursor.execute(query,value)
                result = models.cursor.fetchone()
                print(result)
                if  result:
                    print("alredy checked in")
                    if  result[0]=='checked_out':
                        print("checked out already")
                        return redirect(url_for('dashboard'))
                    else:
                        employee_id = session.get("user_id")
                        status = 'checked_out'
                        query = (" update attendance set live_status =%s where employee_id =%s and attendance =%s")
                        value = (status , employee_id , models.date.today() )
                        models.cursor.execute(query , value )
                        models.cnx.commit()
                        return redirect(url_for('dashboard'))
                else:
                    return redirect(url_for('dashboard'))

                    
            except models.mysql.connector.Error as err:
                print(err)
                return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))

@app.route('/attendances', methods=['POST', 'GET'])
def attendaces():
    if session.get('role')=='HR':
        query = (' select employee_id , attendance , status from attendance  ')
        models.cursor.execute(query , )
        result = models.cursor.fetchall()
        return render_template("attendance.html" , result=result)
    if session.get('role')=='employee':
        query = (' select  attendance , status from attendance where employee_id =%s  ')
        value=(session.get('user_id') ,)
        
        models.cursor.execute(query ,value)
        result = models.cursor.fetchall()
        return render_template("attendance.html" , result=result)
    else:
        return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
