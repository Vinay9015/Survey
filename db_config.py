import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='Kongcanyouhearme1?',
        database='student_survay'
    )
