from django.core.mail import send_mail
import africastalking
from django.conf import settings

def sendmail(subject,message,fromEmail='info@austino.online', toEmails=[]):
    print(subject,message,fromEmail, toEmails)
    
    try:
        mm= send_mail(
            subject,
            message,
            'info@austino.online',  # From email
            toEmails,
            fail_silently=False
        )

        print('mm',mm)
        if(mm==1):
            return('Success')
    
        return ('Failed')
        
    except Exception as e:
        print("Failed to send admin email:", e)
        return(f'Failed')
        return e
    

def sendText(phone_number,message):
    try:
        # username='sandbox'
        # api_key=""
        username=settings.AFRICASTALKING_USERNAME
        api_key=settings.AFRICASTALKING_API_KEY
        print(username)
        print(api_key)
        africastalking.initialize(username,api_key)
        sms = africastalking.SMS
        # blacklisted = sms.fetch_blacklist()
        # print(blacklisted)
        res= sms.send(message, [phone_number,])
        recepients= res['SMSMessageData']['Recipients'][0]
        print(recepients)
        if(recepients['status']=='Success'):
             return(recepients['status']) 
        return f"Failed-{recepients['status']}"
    except Exception as e:
        print("Failed to send SMS:", e)
        return(f"Failed-{str(e)}")