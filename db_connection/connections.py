import mysql.connector 
from mysql.connector import errorcode

cnx = mysql.connector.connect(user='root' , password='root', host='127.0.0.2',database='HR_system')
print("connection done")
# cnx.close()

# print('connection close ')

DB_name = 'HR_system'

TABLES ={}

TABLES['users']=(
    "create	table users("
        "user_id int   primary key auto_increment , "
        "comp_name varchar(30) not null ,"
        "f_name varchar(30) not null ,"
        "l_name VARCHAR(50) NOT NULL,"
        "email VARCHAR(100) UNIQUE NOT NULL,"
        "password VARCHAR(255) NOT NULL,"
        "salt VARCHAR(64) NOT NULL,"
        "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ,"
        "mob_nu char(12) not null , "
        "role ENUM('HR', 'employee') DEFAULT  NULL "
        
        
        ")ENGINE=InnoDB"
    )


cursor=cnx.cursor()
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



def create_database(cursor):
    try:
        cursor.execute(
            f"create database {DB_name}  "
        )
    except mysql.connector.Error as err:
        print(f"failed to create database {DB_name} : {err}")
        exit(1)

def use_database(DB_name , TABLES):
    try:
        cursor.execute(f"use {DB_name}")
        print(f"databse '{DB_name}' is in use ")
        create_tables(TABLES)
    except mysql.connector.Error as err:
        print(f"database {DB_name} dosen't exist :{err}")
        if err.errno==errorcode.ER_BAD_DB_ERROR:
            create_database(cursor)
            print(f"database {DB_name} created successfully .")
            use_database(DB_name)
            cnx.database=DB_name
        else:
            print(err)
            exit(1)
    return 0

use_database(DB_name,TABLES)

cursor = cnx.cursor()