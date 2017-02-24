import os
import smtplib
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

def sendMail(text, images):
    gmail_user = 'seanwademail@gmail.com'
    gmail_password = '***********'

    msg = MIMEMultipart()
    msg['Subject'] = 'New Van!'
    msg['From'] = 'seanwademail@gmail.com'
    msg['To'] = 'seanwademail@gmail.com'

    text = MIMEText(text)
    msg.attach(text)

    for img in images:
        img_data = open(img, 'rb').read()
        image = MIMEImage(img_data, name=os.path.basename(img))
        msg.attach(image)

    s = smtplib.SMTP('smtp.gmail.com')
    s.ehlo()
    s.starttls()
    s.ehlo()
    s.login(gmail_user, gmail_password)
    s.sendmail(msg['From'], msg['To'], msg.as_string())
    s.quit()
