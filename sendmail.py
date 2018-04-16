import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

def send(address,name,key):
    msg = MIMEMultipart()
    msg['From'] = 'cloudcomputing356@gmail.com'
    msg['To'] = address
    msg['Subject'] = 'Welcome to Chirp!'
    #message = 'Hello ' +name+'\n Welcome to Chirp!\n Click this link to verify your account: \n'
    #message+= "http://130.245.170.79/verify?email="+address+"&key="+key
    message ="validation key: <"+key+">"
    #message +="\n Chirpchirp!"
    msg.attach(MIMEText(message))
    mailserver = smtplib.SMTP('smtp.gmail.com',587)
    # identify ourselves to smtp gmail client
    mailserver.ehlo()
    # secure our email with tls encryption
    mailserver.starttls()
    # re-identify ourselves as an encrypted connection
    mailserver.ehlo()
    mailserver.login('cloudcomputing356@gmail.com', 'tictactoe')
    mailserver.sendmail('cloudcomputing356@gmail.com',address,msg.as_string())
    mailserver.quit()


