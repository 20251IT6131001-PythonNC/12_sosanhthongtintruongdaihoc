import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="@Khuyen2903",
        database="universities"
    )
