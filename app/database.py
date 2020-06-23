#import psycopg2
#conn = psycopg2.connect(dbname='schedule', user='username', 
#                        password='password', host='localhost')

cursor = conn.cursor()

cursor.execute('SELECT * FROM student LIMIT 10')
records = cursor.fetchall()
print(records)
cursor.close()
conn.close()