#python 3.9.0
#pip install flask pillow opencv-python imutils pandas google-generativeai tensorflow==2.13

from flask import Flask, render_template, url_for, request, session, redirect, jsonify
import sqlite3
import os
import secrets
from PIL import Image
import qrcode
from pyzbar.pyzbar import decode
import time
import cv2
import base64
import requests
import numpy as np
qr = qrcode.QRCode(
    version =1,
    box_size =10,
    border=6)

connection = sqlite3.connect('user_data.db')
cursor = connection.cursor()

command = """CREATE TABLE IF NOT EXISTS user(name TEXT, password TEXT, mobile TEXT, email TEXT)"""
cursor.execute(command)

command = """CREATE TABLE IF NOT EXISTS details(Id INTEGER PRIMARY KEY AUTOINCREMENT, Type TEXT, breed TEXT, name TEXT, age TEXT, phone TEXT, color TEXT, weight TEXT, Description TEXT, email TEXT, image TEXT)"""
cursor.execute(command)

command = """CREATE TABLE IF NOT EXISTS adapts(Id INTEGER PRIMARY KEY AUTOINCREMENT, Type TEXT, breed TEXT, name TEXT, age TEXT, phone TEXT, color TEXT, weight TEXT, Description TEXT, email TEXT, image TEXT, aname TEXT, aphone TEXT, aemail TEXT )"""
cursor.execute(command)

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
chat_history = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/addpage')
def addpage():
    return render_template('add.html')

@app.route('/getpage')
def getpage():
    return render_template('get.html')

@app.route('/userlog', methods=['GET', 'POST'])
def userlog():
    if request.method == 'POST':

        connection = sqlite3.connect('user_data.db')
        cursor = connection.cursor()

        name = request.form['name']
        password = request.form['password']

        query = "SELECT * FROM user WHERE name = '"+name+"' AND password= '"+password+"'"
        cursor.execute(query)

        result = cursor.fetchone()

        if result:
            session['user'] = result[0]
            session['phone'] = result[2]
            session['email'] = result[3]
            return render_template('add.html')
        else:
            return render_template('login.html', msg='Sorry, Incorrect Credentials Provided,  Try Again')

    return render_template('login.html')

@app.route('/notification')
def notification():
    connection = sqlite3.connect('user_data.db')
    cursor =connection.cursor()
    cursor.execute("select * from adapts where phone = '"+session['phone']+"'")
    result = cursor.fetchall()
    print(session['phone'])
    return render_template('notification.html', result=result)

@app.route('/userreg', methods=['GET', 'POST'])
def userreg():
    if request.method == 'POST':

        connection = sqlite3.connect('user_data.db')
        cursor = connection.cursor()

        name = request.form['name']
        password = request.form['password']
        mobile = request.form['phone']
        email = request.form['email']
        
        print(name, mobile, email, password)

        cursor.execute("INSERT INTO user VALUES ('"+name+"', '"+password+"', '"+mobile+"', '"+email+"')")
        connection.commit()

        return render_template('login.html', msg='Successfully Registered')
    
    return render_template('login.html')

@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        data = request.form
        print(data)
        values = []
        keys = []
        for key in data:
            values.append(data[key])
            keys.append(key)
        print(keys)
        print(values)

        file = request.files['image']
        filename = file.filename
        file_content = file.read()
        my_string1 = base64.b64encode(file_content).decode('utf-8')
        values.append(my_string1)

        connection = sqlite3.connect('user_data.db')
        cursor = connection.cursor()
        cursor.execute("INSERT INTO details VALUES (NULL,?,?,?,?,?,?,?,?,?,?)", values)
        connection.commit()

        cursor.execute("select * from details")
        result = cursor.fetchall()

        Id = result[-1][0]
        print('id', Id)
        qr.add_data(Id)
        qr.make(fit=True)
        image = qr.make_image(fill_color="black", back_color= "white")
        image.save('static/qrcodes/'+str(Id)+".png")
        print("QR code has been generated successfully!")

        return render_template('add.html', msg = "Successfully added", img = 'http://127.0.0.1:5000/static/qrcodes/'+str(Id)+".png")
    return render_template('add.html')

@app.route('/get')
def get():
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()

    vs = cv2.VideoCapture(0)

    while True:
        ret, img = vs.read()
        detectedBarcodes = decode(img)
        d=''
        t=''
        for barcode in detectedBarcodes:
            (x, y, w, h) = barcode.rect
            cv2.rectangle(img, (x-10, y-10),
                        (x + w+10, y + h+10),
                        (255, 0, 0), 2)
            
            d = barcode.data
            t = barcode.type
            
        if d != "":
            cv2.putText(img, str(d), (50, 50) , cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0) , 2)

        cv2.imshow("Image", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        if d != "":
            time.sleep(1)
            break

    cv2.destroyAllWindows()

    d = d.decode('utf-8', 'ignore')
    print(d)

    c.execute("select * from details where Id = '"+str(d)+"'")
    result = c.fetchone()
    if result:
        return render_template('get.html', result = result)
    else:
        return render_template('get.html', msg = 'QR code not detected')

@app.route('/adapt')
def adapt():
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute("select * from details")
    result = c.fetchall()
    if result:
        return render_template('adapt.html', result = result)
    else:
        return render_template('adapt.html')

@app.route('/adaption/<Id>')
def adaption(Id):
    print('id is', Id)
    connection = sqlite3.connect('user_data.db')
    cursor =connection.cursor()
    cursor.execute("select * from details where Id = '"+str(Id)+"'")
    row = list(cursor.fetchone())
    row.append(session['user'])
    row.append(session['phone'])
    row.append(session['email'])
    cursor.execute("insert into adapts values(NULL,?,?,?,?,?,?,?,?,?,?,?,?)", row)
    connection.commit()
    return redirect(url_for('adapt'))

@app.route('/logout')
def logout():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)