# 1 . Imports
from flask import Flask,request,redirect,url_for,render_template,session
import sqlite3
import random
from flask_mail import Mail
from email.mime.multipart import MIMEMultipart
import smtplib, ssl
from email.mime.text import MIMEText
from passlib.hash import sha256_crypt



# 2. All Configurations
app=Flask(__name__)
app.config["DEBUG"] = True
app.config['SECRET_KEY'] = '1234'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
sender_email='aryanarorafreebookswdf@gmail.com'
sender_password='Freebooks123'
mail = Mail(app)

domain='https://walldorf-book-exchanger.herokuapp.com/ '
# 3. All Custom Functions
   
def sendemail( subject, recepient_email, message):
    email_message = MIMEMultipart("alternative")
    print(0,email_message)
    email_message["Subject"] = subject
    email_message["From"] = sender_email
    email_message["To"] = recepient_email

    part1 = MIMEText(message, "html")
    print(1,part1)
    #part2=MIMETEXT(html,'html')
    email_message.attach(part1)
    print(2,email_message)
    #email.message.attach(part2)

    context = ssl.create_default_context()
    print(3,context)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, sender_password  )
        server.sendmail(
         sender_email, recepient_email, email_message.as_string()
        )


# 4. All Routes

# 4a. Adding Books
@app.route('/add_books', methods=['GET', 'POST'])
def add_books(): 
    #checking whether the person is logged in or not      
    if session.get('authenticated') == None or session.get('authenticated') == False :
        return redirect(url_for('login'))
    elif request.method=='POST': 
        bookname = request.form.get('bookname')
        book_detail = request.form.get('book_detail')
        book_image=request.files.get('coverpage',False)
        numbers=[0,1,2,3,4,5,6,7,8,9]
        random_number=''
        for ran_num in range(0,4):
            num=random.choice(numbers)
            random_number+=str(num)
        if book_image==False:
            image_path=book_image
        else:
            image_path='static/media/'+ random_number + book_image.filename
        # file handling
            f=open(image_path,'wb')
            f.write(book_image.read())
            f.close()
        conn = sqlite3.connect('database/freebooks.db')
        cur=conn.cursor()
        cur.execute('INSERT INTO total_books (bookname,book_detail,book_image,user_id) \
                     VALUES (?,?,?,?);',[bookname,book_detail,image_path,session.get('user_id')])
        conn.commit()
        conn.close()
        return redirect(url_for('all_books'))
    return render_template('add_books.html')
# 4b. Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    message=''
    error_message=''
    if request.method == 'POST':
        first_name = request.form.get('fname')
        last_name = request.form.get('lname')
        email = request.form.get('email')
        contact = request.form.get('contact')
        city = request.form.get('city')
        password = request.form.get('password')
        confirm_password  = request.form.get('confirm_password')
        conn=sqlite3.connect('database/freebooks.db')
        cur = conn.cursor()
        registered_emails = cur.execute('SELECT email from users where email=?;',[email]).fetchall()
        if len(registered_emails)!=0:
            error_message = 'Email id already exists'
            return render_template('register.html',error_message=error_message)
        elif password == confirm_password:
            password=sha256_crypt.hash(password)
            print(password)
            # Password Hashing to be done using passlib and sha256
            # password=sha256_crypt.hash(password)
            cur.execute(''' INSERT INTO users(
                fname,lname,email,contact,contact,password)
                VALUES (?,?,?,?,?,?);'''
                ,(first_name,last_name,email,contact,city,password))
            conn.commit()
            conn.close()
            message = 'registration successful'
            return render_template('login.html',message=message)
        else:
            message = 'unsuccessful registration'
    return render_template('register.html',message=message)   

# 4c. Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    message=''
    error_message=''
    if request.method == 'POST':
        password=request.form.get('password')
        email = request.form.get('email')
        conn=sqlite3.connect('database/freebooks.db')
        cur=conn.cursor()
        records = cur.execute('SELECT password,id,fname FROM users WHERE email=?',[email]).fetchone()
        conn.close()
        if records == None:
            error_message = 'No user found with this Email id try again'
            
        elif sha256_crypt.verify(password,records[0]):
            session['email']=email
            session['authenticated'] =True
            session['user_id']=records[1]
            session['firstname']=records[2]
            message ='logged in successfully'
            return redirect(url_for('all_books'))
        else:
            message = 'Either email id or password is incorrect'
        
    return render_template('login.html',message=message,error_message=error_message)

# 4d. Home
@app.route('/')
@app.route('/all_books', methods=['GET', 'POST'])
def all_books():
    conn=sqlite3.connect('database/freebooks.db')
    cur=conn.cursor()
    cur.execute('SELECT * FROM total_books WHERE user_id!=? ORDER BY status;',[session.get('user_id')])
    records=cur.fetchall()
    conn.close()
    return render_template ('all_books.html',records=records)

# Shows all books uploaded by the current logged in user
# 4e. My Books
@app.route('/my_books', methods=['GET', 'POST'])
def my_books():
    conn=sqlite3.connect('database/freebooks.db')
    cur=conn.cursor()
    cur.execute('SELECT * FROM total_books WHERE user_id = ?;',[session.get('user_id','-1')])
    records=cur.fetchall()
    return render_template ('my_books.html',records=records)

@app.route('/request_for_rent/<book_id>')
def request_for_rent(book_id):
    conn=sqlite3.connect('database/freebooks.db')
    cur=conn.cursor()
    # 1 -available 2 -Rented 3 - Requested for rent 
    cur.execute('Update total_books set status="3", rent_user_id =? WHERE  id = ?;',[session.get('user_id'),book_id])
    conn.commit()
    userid=cur.execute('SELECT user_id,bookname from total_books where id=?;',[book_id]).fetchone()

    owner_userid=userid[0]
    bookname=userid[1]
    print(bookname)
    email_id=cur.execute('SELECT email from users where id=?;',[owner_userid]).fetchone()
    # Email Part
    print(email_id)
    owner_email_id=email_id[0]
    print(str(session.get('firstname')))
    subject='Your Book has been requested for rent'
    print(subject)
    email_mesage_to_owner=str(session.get('firstname'))+ ' has requested your book '\
        +bookname+' for rent click the link below to approve' \
        + domain + '/pending_action'
    print(email_mesage_to_owner)
    sendemail(subject, owner_email_id, email_mesage_to_owner) 
    print('mail sent')          
    #send email to the owner of the website with a link to approve 
    # if approved update the status to 2 
    # Once he returns the book again update the status to 1
    conn.close()
    return redirect(url_for('all_books'))


# This route is not in use
@app.route('/approve_for_rent/<book_id>')
def approve_for_rent(book_id):
    #add login condition
    if session.get('authenticated',False)==False:
        return redirect('/login')
    conn=sqlite3.connect('database/freebooks.db')
    cur=conn.cursor()
    # 1 -available 2 -Rented 3 - Requested for rent 
    cur.execute('Update total_books set status="2" WHERE id = ?;',[book_id])
    #get userid from book_id and get email id from users table
    userid=cur.execute('SELECT user_id,bookname from total_books where id=?;',[book_id]).fetchone()
    owner_userid=userid[0]
    bookname=userid[1]
    email_id=cur.execute('SELECT email from users where id=?;',[owner_userid]).fetchone()
    conn.commit()
    conn.close()
    owner_email_id=email_id[0]
    current_logged_in_user=session.get('firstname')
    current_logged_in_user_email=session.get('email')
    subject_owner='Request from Freebooks user'
    subjetc_current_user='Freebooks- Request Status'
    email_mesage_to_owner=current_logged_in_user + 'has requested your book ' +bookname+\
                            ' for rent click the link below to approve' + \
                            domain +' /pending_action'
    email_message_to_current_user='Your request is pending for approval from the owner.'
    sendemail(subject_owner, owner_email_id, email_mesage_to_owner) 
    sendemail(subjetc_current_user, current_logged_in_user_email, email_message_to_current_user) 
    return redirect(url_for('my_books'))

@app.route('/pending_action', methods=['GET', 'POST'])
def pending_action():
    conn=sqlite3.connect('database/freebooks.db')
    cur=conn.cursor()
    records=cur.execute('select * from total_books where user_id=? and status !=1;',[session.get('user_id')]).fetchall()
    conn.close()
    return render_template('pending_actions.html',records=records)


@app.route('/approve_request/<book_id>', methods=['GET', 'POST'])
def approve_request(book_id):
    conn=sqlite3.connect('database/freebooks.db')
    cur=conn.cursor()
    # 1 -available 2 -Rented 3 - Requested for rent 
    cur.execute('Update total_books set status="2" WHERE  id = ?;',[book_id])
    conn.commit()
    userid=cur.execute('SELECT rent_user_id,bookname from total_books where id=?;',[book_id]).fetchone()
    rent_userid=userid[0]
    bookname=userid[1]
    email_id=cur.execute('SELECT email from users where id=?;',[rent_userid]).fetchone()
    conn.close()
    rent_person_email_id=email_id[0]
    owner_email_id=session.get('email','False')
    subject='Your request to rent a book has been approved'
    # send below email to both owner and rent person
    email_mesage_to_rent_person='request to rent the ' + bookname + ' has been approved. \n' +  'contact details of book owner is ' + owner_email_id  + ' and contact details of person requested for rent is ' + rent_person_email_id + ' Please coordinate between yourself'
    sendemail(subject, rent_person_email_id, email_mesage_to_rent_person)
    sendemail(subject, owner_email_id, email_mesage_to_rent_person)
    
    return redirect(url_for('pending_action'))



@app.route('/decline_request/<book_id>', methods=['GET', 'POST'])
def decline_request(book_id):
    conn=sqlite3.connect('database/freebooks.db')
    cur=conn.cursor()
    # 1 -available 2 -Rented 3 - Requested for rent 
    userid=cur.execute('SELECT rent_user_id,bookname from total_books where id=?;',[book_id]).fetchone()
    rent_userid=userid[0]
    bookname=userid[1]
    email_id=cur.execute('SELECT email from users where id=?;',[rent_userid]).fetchone()
    print(email_id)
    rent_person_email_id=email_id[0]
    subject='Your request to rent a book has been declined'
    # send below email to rent person
    email_mesage_to_rent_person='request to rent the' + bookname + \
        'has been declined. However you can request for other books by clicking here '\
        + domain + ' /all_books'
    sendemail(subject, rent_person_email_id, email_mesage_to_rent_person)
    cur.execute('Update total_books set status="1",rent_user_id=NULL WHERE  id = ?;',[book_id])
    conn.commit()
    conn.close()
    return redirect(url_for('all_books'))

@app.route('/my_rented_books', methods=['GET', 'POST'])
def my_rented_books():
    conn=sqlite3.connect('database/freebooks.db')
    cur=conn.cursor()
    cur.execute('SELECT * FROM total_books WHERE rent_user_id = ? and (status=2 or status=3);',[session.get('user_id','-1')])
    #todo if status ==2 show a button reurn book and link it to action return rented book, if ststus ==3 show a unclickable button <waiting for approval>
    records=cur.fetchall()
    return render_template ('my_rented_books.html',records=records)

@app.route('/return_book/<book_id>', methods=['GET', 'POST'])
def return_book(book_id):
    # update status to available in all books
    subjekt='Your email has been saent fro returning your book'
    conn=sqlite3.connect('database/freebooks.db')
    cur=conn.cursor()
    user_id=cur.execute("select user_id from total_books where id=?;",[book_id]).fetchone()
    email=cur.execute("select email from users where id=?;",[user_id[0]]).fetchone()
    cur.execute('Update total_books set status="1" WHERE  id = ?;',[book_id])
    bookname=cur.execute('SELECT bookname from total_books WHERE id=?;',[book_id]).fetchone()
    bookname=bookname[0]
    rent_person_name=session.get('firstname')
    rent_person_email=session.get('email')
    message='The user %s wants to return your book %s. Please Contact him "%s" for futher action.'%(rent_person_name,bookname,rent_person_email)
    print(message)
    sendemail(subjekt, email[0],message)
    return redirect(url_for('all_books'))

@app.route('/search_books', methods=['GET', 'POST'])
def search_books():
    if request.method=='POST':
        search_books=request.form.get('search_books')
        print(search_books)
        search_books='%'+search_books+'%' 
        conn=sqlite3.connect('database/freebooks.db')
        cur=conn.cursor()
        cur.execute('SELECT * FROM total_books WHERE user_id!=? and bookname LIKE ?;',[session.get('user_id'),search_books])
        records=cur.fetchall()
        conn.close()
        print(records)
    return render_template('search_books.html',records=records)

@app.route('/logout')
def logout():
    session.clear()
    return render_template('index.html')

@app.route('/forgotpassword',methods=['GET', 'POST'])
def forgotpassword():
   if request.method=='GET':
       return render_template("forgotpassword.html")
   else:
       email=request.form.get("email")
       session["email"]=email
       subjekt="resetpassword/freebooks"
       verficationcode=random.randrange(1000,9999)
       message="Here is your verification code " + str(verficationcode) + "Please use this code to reset your password"
       session["verification"]=verficationcode
       sendemail(subjekt,email,message)
       print("emailsent")
       return render_template("resetpassword.html")
@app.route('/resetpassword',methods=['GET', 'POST'])
def resetpassword():
    if request.method=='GET':
        return render_template("resetpassword.html")
    else:
        email=session.get("email")
        vcode=request.form.get("vcode")
        vocode_session=session.get("verification")
        newpassword=request.form.get("password")
        confirmpassword=request.form.get("passwordconfirm")
        error=""
        if vcode == vocode_session:
            print('code verified')
            if newpassword==confirmpassword:
                print('verified')
                #update new password in the database
                conn=sqlite3.connect("database/freebooks.db")
                cur=conn.cursor()
                cur.execute("update users set password=? where email = ? ;",[newpassword,email])
                conn.commit()
                conn.close()
                print("Password updated")
                return redirect(url_for("login"))
            else:
                error="Password is incorrect"
                print(error)
                return render_template("resetpassword.html",error=error)
        else:
            print(error)
            error="Incorrect Verfication Code"
            return render_template("resetpassword.html",error=error)
            
            
       






if __name__ == '__main__':
    app.run(debug=True)