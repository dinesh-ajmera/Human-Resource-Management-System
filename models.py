import config 
import mysql.connector 
from mysql.connector import errorcode
from datetime import datetime ,date
from werkzeug.security import generate_password_hash , check_password_hash
DB_name=config.DB_name
cnx = mysql.connector.connect(user='root' , password='root', host='127.0.0.2' )
cursor=cnx.cursor()
# def create_db():

#     try:
        
#         cursor.execute(f"crete database {DB_name}")
#         print("database is created")
       
#         return True

#     except mysql.connector.Error as err:
        
#             print("database is not creted")
#             print(err)
#             return False
        

TABLES ={}

TABLES['users']=(
    "create	table users("
        "user_id int   primary key NOT NULL auto_increment, "
        "f_name varchar(30) not null ,"
        "l_name VARCHAR(50) NOT NULL,"
        "email VARCHAR(100) UNIQUE NOT NULL,"
        "password VARCHAR(255) NOT NULL,"
        "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ,"
        "mob_nu char(12) not null , "
        "role ENUM('HR', 'employee') DEFAULT  NULL "
        
        
        ")ENGINE=InnoDB"
    )



TABLES['leaves']=(
    "create	table leaves("
        "leave_id int   primary key auto_increment , "
        "employee_id int not null ,"
        "approved_by int default null ,"
        "start_date date not null ,"
        "end_date date not null,"
        "comments_from_empl varchar(200) NOT NULL,"
        "comments_from_HR varchar(200) default NULL,"
        "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ,"
        "last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,"
        "status ENUM('pending', 'approved','rejected') DEFAULT  'pending', "
        "foreign key(approved_by) references users(user_id) ,"        
        "foreign key(employee_id) references users(user_id)"
        
        ")ENGINE=InnoDB"
    )


TABLES['attendance']=(
    "create	table attendance("
        "attandance_id int   primary key auto_increment , "
        "employee_id int not null ,"
        "check_in TIMESTAMP DEFAULT CURRENT_TIMESTAMP  ,"
        "check_out TIMESTAMP NULL DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP ,"
        "attendance date default (CURRENT_DATE),"
        "live_status ENUM('live', 'checked_out') DEFAULT  'live', "
        "status ENUM('absent', 'present','half_day','leave') DEFAULT  'absent', "
        "foreign key(employee_id) references users(user_id)"
        
        ")ENGINE=InnoDB"
    )




def create_database(cursor):
    try:
        cursor.execute(
            f"create database {DB_name}  "
        )
    except mysql.connector.Error as err:
        print(f"failed to create database {DB_name} : {err}")
        exit(1)


def create_tables(TABLES):
    for table_name in TABLES:
        table_discription=TABLES[table_name]
        try:
            print(f"creating table {table_name}")
            cursor.execute(table_discription)
        except mysql.connector.Error as err:
            if err.errno==errorcode.ER_TABLE_EXISTS_ERROR:
                print(f"table {table_name} alredy exist")
            else:
                print(err)
        else:
            print("ok")
    return 0

# def use_database(DB_name , TABLES):
def use_database():
    try:
        cursor.execute(f"use {DB_name}")
        print(f"databse '{DB_name}' is in use ")
        create_tables(TABLES)
        return True
    except mysql.connector.Error as err:
        print(f"database {DB_name} dosen't exist :{err}")
        if err.errno==errorcode.ER_BAD_DB_ERROR:
            create_database(cursor)
            print(f"database {DB_name} created successfully .")
            use_database()
            cnx.database=DB_name
            return True
        else:
            print(err)
            return False
    



def authenticate_user(email,password):
    try:
        query = ("select password ,user_id ,role from users where email = %s ")
        values=(email ,)
        print(values)
        cursor.execute(query , values)
        result = cursor.fetchone()
        if result == None:
            print("user not excists")
            return 1
        else:
            print(type(result[0]))
            print(password)
            print(type(password))
            print(check_password_hash( result[0],password))
            print("user exists")
            if check_password_hash( result[0],password):
                print('authentication is done')
                return result
            else:
                print("unautherized user")
                return 1

            
    except mysql.connector.Error as err:
        print(err)
        return 1
 


# def database_setup():
    # try:
    #     use_database()
    #     print("done")
    #     return True
    # except :
    #     print("not done")
    #     return False

if __name__ == "__main__":
    use_database()
    # database_setup()
    # check_users("dines231h@gmail.com" ,'123')