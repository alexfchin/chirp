from email.mime.text import MIMEText
from subprocess import Popen, PIPE
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

def send(address,name,key):
    msg = MIMEMultipart()
    message ="validation key: <"+key+">"
    #message +="\n Chirpchirp!"
    msg.attach(MIMEText(message))
    msg["From"] = "ubuntu@cloud.chirp.com"
    msg["To"] = address
    msg["Subject"] = "Subject"
    p = Popen(["/usr/sbin/sendmail", "-t", "-oi"], stdin=PIPE, universal_newlines=True)
    p.communicate(msg.as_string())
