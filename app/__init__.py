from flask import Flask
import psycopg2

app = Flask(__name__)
conn = psycopg2.connect(dbname='schedule', user='username', 
                    password='password', host='localhost')
app.secret_key = 'some_secret'
# cursor = conn.cursor()
# cursor.execute("INSERT INTO reg_info (login, pass) VALUES ('login'," + str(hash('password') % 10000) + ");")
is_admin = True
# cursor.close()

from app import routes

