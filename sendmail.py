import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

def send(address,name,key):
    msg = MIMEMultipart()
    msg['From'] = 'csecloud356@gmail.com'
    msg['To'] = address
    msg['Subject'] = 'test email'
    message = 'Hello ' +name+' click this to verify your account on /ttt :)\n'
    message+= "130.245.168.39/verify?email="+address+"&key="+key
    msg.attach(MIMEText(message))
    mailserver = smtplib.SMTP('smtp.gmail.com',587)
    # identify ourselves to smtp gmail client
    mailserver.ehlo()
    # secure our email with tls encryption
    mailserver.starttls()
    # re-identify ourselves as an encrypted connection
    mailserver.ehlo()
    mailserver.login('csecloud356@gmail.com', 'tictactoe')
    mailserver.sendmail('csecloud356@gmail.com',address,msg.as_string())
    mailserver.quit()


