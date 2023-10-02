import sqlite3
conn=sqlite3.connect('Students.db')
cur=conn.cursor()
#cur.execute('Create Table Students3(Roll_No Integer Primary Key,Student_Name Text, Age Integer);')
cur.execute('Insert Into Students3(Roll_No,Student_Name,Age)Values(1,"Johny",10);')
print("Table created")
conn.commit()