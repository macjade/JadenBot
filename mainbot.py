from flask import Flask, request
from flask_mysqldb import MySQL
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Say

from dateutil.parser import parse

account_sid = 'AC9e569179895717e9ee90661f807e836d'
auth_token = 'd20d23253b1a41aa9244c5081a4139e6'
client = Client(account_sid, auth_token)

from dateutil.relativedelta import *
from datetime import timedelta
import datetime
import shlex
import re
import time
import atexit
import mysql.connector
import time

from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'den1.mysql5.gear.host'
app.config['MYSQL_USER'] = 'bottest'
app.config['MYSQL_PASSWORD'] = 'Nt9F8umm_l_j'
app.config['MYSQL_DB'] = 'bottest'

mysqld = MySQL(app)


@app.route('/bot', methods=['POST'])
def home():
    fmt = "%Y-%m-%d %H:%M"
    now_time = datetime.datetime.now().strftime(fmt)

    incoming_msg = request.values.get('Body', "")
    user = request.values.get('From', None).replace('whatsapp:', "")
    resp = MessagingResponse()
    msg = resp.message()
    responded = False
    print(request.values)
    cur = mysqld.connection.cursor()
    cur.execute("SELECT * FROM users WHERE BINARY Number=%s", (user,))
    users = cur.fetchone()
    if users:
        if users[2]:
            if 'set reminder' in incoming_msg.lower():
                bd = incoming_msg.lower().replace('set reminder', '')
                if u'\u201c' in bd:
                    body = re.sub(u'\u201c', '"-', bd)
                    body = re.sub(u'\u201d', '-"', body)
                else:
                    body = re.sub(u'\u0022', '"-', bd)
                rsp = setreminder(shlex.split(body), users[0])
                msg.body(str(rsp))
                responded =True

            elif 'view reminders' in incoming_msg.lower():
                bd = incoming_msg.lower().replace('view reminders', '')
                rsp = viewreminder(shlex.split(bd), users[0])
                msg.body(str(rsp))
                responded = True

            elif 'delete reminder' in incoming_msg.lower():
                bd = incoming_msg.lower().replace('delete reminder', '')
                rsp = deletereminder(shlex.split(bd), users[0])
                msg.body(str(rsp))
                responded = True

            elif 'send message' in incoming_msg.lower():
                bd = incoming_msg.lower().replace('send message', '')
                if u'\u201c' in bd:
                    body = re.sub(u'\u201c', '"-', bd)
                    body = re.sub(u'\u201d', '-"', body)
                else:
                    body = re.sub(u'\u0022', '"-', bd)
                media = request.values.get('MediaContentType0', None)
                mediaUrl = request.values.get('MediaUrl0', None)
                rsp = sendmsg(media, mediaUrl, shlex.split(body), users[0])
                msg.body(str(rsp))
                responded = True

            elif "send call" in incoming_msg.lower():
                bd = incoming_msg.lower().replace('send call', '')
                if u'\u201c' in bd:
                    body = re.sub(u'\u201c', '"-', bd)
                    body = re.sub(u'\u201d', '-"', body)
                else:
                    body = re.sub(u'\u0022', '"-', bd)
                rsp = sendcall(shlex.split(body), users[0])
                msg.body(str(rsp))
                resp.message("*NOTE:* If number is not added to the sandbox, user won't receive the call. Thank you.")
                responded = True

            elif "/help" == incoming_msg.lower():
                help = jadenhelp()
                msg.body(str(help))

            else:
                msg.body("Sorry I'm not trained to respond to this message. Thanks")
                resp.message("""For Jaden assistance respond with '/help'.""")
        else:
            print(False)
    else:
        if incoming_msg.lower() == 'hello jaden':
            cur.execute("INSERT INTO users(Number, is_jaden, active_time) VALUES (%s, %s, %s)", (user, True, now_time))
            mysqld.connection.commit()
            msg.body("""
                For Jaden assistance respond with '/help'.
            """)
            responded = True
        else:
            msg.body("Jaden is inactive. Activate Jaden by responding with 'Hello Jaden'. Thank You")
            responded = True

    return str(resp)

@app.route('/static/msg.txt', methods=['POST'])
def stat():
    message = ''
    with open('./static/msg.txt', "r") as f:
        message = f.read()

    response = VoiceResponse()
    response.say(message, voice='alice')
    print(message)
    return(str(response))

def jadenhelp():

    help = "Welcome to Jaden whatsapp bot help center. \n\n To control me use the following commands: \n\n"
    help += '*Managing Anonymous Calls*\n send call "message" phone-number \n\n'
    help += '*Managing Anonymous Messages*\n send message "message" phone-number media:images[optional] \n\n'
    help += '*Managing Reminders*\n set reminder "Event message" YYYY/MM/DD HH:MM yearly/monthly/once default:once\n'
    help += 'view reminders \n delete reminder reminder-id'

    return help

################################# Initiate call ##############################################

def sendcall(body, UserId):
    bd = {}

    if len(body) != 2:
        return "Invalid number of parameters was responded"

    for (index, i) in enumerate(body):

        if '-' in i:
            bd['message'] = str(i).replace('-', '')

        elif i[0] == '+':
            bd['phone'] = i
        else:
            bd['error'] = index
            break

    if bd.get('error', None):
        if bd['error'] == 0:
            return 'Please set a call Message'

        if bd['error'] == 1:
            return 'Invalid Phone format'

    try:

        with open('./static/msg.txt', "w") as f:
            f.write(bd['message'])

        call = client.calls.create(
            url='https://f06d4903ca3d.ngrok.io/static/msg.txt',#'http://demo.twilio.com/docs/voice.xml',
            to='+2349032885704',
            from_='+13869994478'
        )
        print(call)
        return "Call has been placed."
    except:
        return "Unable to initiate call. Please try again."

################################# End Call ###################################################

################################# Reminders #############################################333
def setreminder(body, userId):

    bd = {}

    if len(body) != 3 and len(body) != 4:
        return "Invalid number of parameters was responded"

    for (index, i) in enumerate(body):

        if '-' in i:
            bd['title'] = str(i).replace('-', '')

        elif is_date(i):
           bd['date'] = str(i).replace('/', '-')

        elif is_time(i):
            bd['time'] = i

        elif i == 'once' or i == 'monthly' or i == 'yearly':
            bd['duration'] = i
        else:
            bd['error'] = index
            break

    if bd.get('error', None):
        if bd['error'] == 0:
            return 'Please set a reminder title'

        if bd['error'] == 1:
            return 'Invalid Date format'

        if bd['error'] == 2:
            return 'Invalid Time format'

    if not bd.get('duration', None):
        bd['duration'] = "once"

    rdate = str(bd['date']) +" "+str(bd['time'])

    cur = mysqld.connection.cursor()
    cur.execute("INSERT INTO reminder(Title, RDate, Duration, UserId) VALUES (%s, %s, %s, %s)", (bd['title'], rdate, bd['duration'], userId))
    mysqld.connection.commit()
    cur.close()
    return "New reminder set. To preview pending reminders, send 'view reminders'"

def viewreminder(body, userId):

    print(body)

    cur = mysqld.connection.cursor()
    cur.execute("SELECT * FROM reminder WHERE BINARY UserId=%s", (userId,))
    reminders = cur.fetchall()

    msg = ''
    if body:
        try:
            cnt = 1 if int(body[0]) <= 1 else int(body[0])
        except:
            return "max lenght has to be an integer value"
    else:
        cnt = 10

    if reminders:
        msg += '*LIST OF PENDING REMINDERS*\n'
        for (index, i) in enumerate(reminders):
            msg += str(index+1)+") "+ str(i[0]) +" "+ str(i[1]) +" "+ str(i[2]) +" "+str(i[3])+"\n"
            if int(index+1) == cnt:
                break
    else:
        msg += 'You have no pending reminders. send "Set Reminder "title" date time occurrence" to set a reminder'

    return msg

def deletereminder(body, userId):
    cur = mysqld.connection.cursor()
    if body and len(body) == 1:
        if 'all' in body:
            cur.execute("DELETE FROM reminder WHERE UserId=%s", (userId,))
            mysqld.connection.commit()
            cur.close()
            return "All reminders has been deleted successfully"

        try:
            rId = int(body[0])

            cur.execute("SELECT * FROM reminder WHERE BINARY ReminderId=%s", (rId,))
            rds = cur.fetchone()
            if rds:
                cur.execute("DELETE FROM reminder WHERE ReminderId=%s", (rId,))
                mysqld.connection.commit()
                cur.close()
                return "Reminder with ID "+str(rId)+" has been deleted successfully"
            else:
                return "Reminder with ID "+str(rId)+" doesn't exists in our records"
        except:
            return "Only positive integers are allowed or use 'all' (without quotes) to delete all reminders"
    else:
        return "delete reminder takes only one parameter"

def sendreminder():
    conn = mysql.connector.connect(
        host="den1.mysql5.gear.host",
        user="bottest",
        password='Nt9F8umm_l_j',
        database="bottest"
    )
    fmt = "%Y-%m-%d %H:%M:%S"
    cur = conn.cursor()
    cur.execute("SELECT * FROM reminder")
    reminders = cur.fetchall()

    if reminders:
        for i in reminders:
            now_time = datetime.datetime.now()
            reminder_date = datetime.datetime.strptime(str(i[2]), fmt)

            if now_time >= reminder_date:
                cur.execute("SELECT Number FROM users WHERE BINARY UsersId=%s", (i[-1],))
                to_number = cur.fetchone()

                from_whatsapp_number = 'whatsapp:+14155238886'

                to_whatsapp_number = 'whatsapp:'+str(to_number[0])

                client.messages.create(body='*REMINDER*: '+i[1],
                                       from_=from_whatsapp_number,
                                       to=to_whatsapp_number)
                if i[3] == 'once':
                    cur.execute("DELETE FROM reminder WHERE ReminderId=%s", (i[0],))
                    conn.commit()
                elif i[3] == 'monthly':
                    month = str(datetime.datetime.strptime('2021-01-31 19:30:00', '%Y-%m-%d %H:%M:%S') + relativedelta(months=1)+timedelta(days=1))
                    cur.execute("UPDATE reminder SET RDate=%s WHERE ReminderId=%s", (month, i[0]))
                    conn.commit()
                else:
                    year = str(datetime.datetime.strptime('2021-01-31 19:30:00', '%Y-%m-%d %H:%M:%S') + relativedelta(years=1)+timedelta(days=1))
                    cur.execute("UPDATE reminder SET RDate=%s WHERE ReminderId=%s", (year, i[0]))
                    conn.commit()

################################### End Reminders ###############################################3333333

#################################### Send Message ###################################################

def sendmsg(media, mediaUrl, body, userId):

    bd = {}
    print(body)
    for (index, i) in enumerate(body):
        if '-' in i:
            bd['message'] = str(i).replace('-', '')

        elif i[0] == '+':
            bd['phone'] = i

        elif i == "anon":
            bd['anon'] = True
        else:
            bd['error'] = index
            break
    print(bd)
    if bd.get('error', None):
        if bd['error'] == 0:
            return 'Invalid Phone format'

    if not bd.get('message', None):
        bd['message'] = ""

    if not bd.get('anon', None):
        bd['anon'] = False

    if media:
        bd['media'] = True
        bd['mediaUrl'] = mediaUrl

    from_whatsapp_number = 'whatsapp:+14155238886'

    to_whatsapp_number = 'whatsapp:' + str(bd['phone'])

    message = client.messages.create(
        media_url=bd['mediaUrl'] if media else None,
        body=bd['message'],
        from_=from_whatsapp_number,
        to=to_whatsapp_number)
    print(message)
    return 'Sent'

#################################### End Message ########################################################

############### check if it a date ####################3

def is_time(string):
    try:
        time.strptime(string, '%H:%M')
        return True
    except:
        return False

def is_date(string):
    try:
        string = str(string).replace('/', '-')
        if datetime.datetime.strptime(string, '%Y-%m-%d'):
            return True
        else:
            return False
    except:
        return False

######################End check date ########################
scheduler = BackgroundScheduler()
scheduler.add_job(func=sendreminder, trigger="interval", misfire_grace_time=10, max_instances=1, seconds=60)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

if __name__=='__main__':
    app.run(debug=True)