from twilio.rest import Client
import creds as l
import json

def send_notif(stk, signal, indvalue, closeprice):
    print('sending notification')
    print(f"stock: {stk} + signal: {signal} +  value: {indvalue} + closeprice: {closeprice}")
    from_ph = l.from_ph
    to_whatsapp = 'whatsapp:' + l.to_ph
    messaging_service_sid=l.messaging_service_sid
    content_template_sid=l.content_template_sid
    client = Client(l.account_sid, l.auth_token)
    try:
        message = client.messages.create(
            from_='whatsapp:' + from_ph,
            #body= "Alert Generated for {{1}}. There is a {{2}} cross.Please check.",  # Use the dynamic message here
            messaging_service_sid = messaging_service_sid,
            content_sid=content_template_sid,
            content_variables =json.dumps({"1":stk,"2":signal,"3":str(indvalue),"4":str(closeprice)}),
            to=to_whatsapp
        )   
        print(f'Message sent to {to_whatsapp} with SID: {message.sid}')
    except Exception as e:
        print(f'Error sending message: {e}')
