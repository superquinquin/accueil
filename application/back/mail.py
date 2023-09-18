import smtplib
from email.mime.text import MIMEText
from typing import List, Dict, Any

from application.back.member import Member

from application.back.mail_parts import *



class Mail(object):

    def __init__(
        self,
        user: str,
        pw: str, 
        port: int, 
        server: str, 
        tx: str, 
        rx: List[str]
        ) -> None:

        self.user = user
        self.pw = pw
        self.port = port
        self.server = server
        self.tx = tx
        self.rx = rx


    def write(self, context: Dict[str, Any]) -> MIMEText:
        # writer = getattr(self, context['mail_type'])
        # msg = MIMEText(writer(context))
        msg = MIMEText(context["body"], 'html')
        msg['Subject'] = context['subject']
        msg['From'] = self.tx
        msg['To'] = ', '.join(self.rx)

        return msg

    def send(self, msg: MIMEText):
        with smtplib.SMTP(self.server, self.port) as smtp:
            smtp.login(self.user, self.pw)
            smtp.starttls()
            smtp.sendmail(
                self.tx,
                self.rx,
                msg.as_string()
            ) 
        
    def send_abs_mail(self, member: Member, end_of_cycle: bool = False) -> None:
        payload = self.generate_abs_mail_payload(member)
        start_greetings = START_GREETINGS.format(**payload)
        qa = BODY_QA.format(**payload)
        if member.cycle_type == "standard" and int(member.ftop_counter) > 0:
            body_fixe = BODY_FIXE_ANTICIPATION.format(**payload)
            obj = OBJECT_ABS_FIXE.format(**payload)
            body_payload = {
                "start_greetings": start_greetings, 
                "main": body_fixe, 
                "incentive": INCENTIVE, 
                "qa": qa, 
                "end_greetings": END_GREETINGS, 
                "signature": SIGNATURE
            }  
            
        elif member.cycle_type == "standard" and int(member.ftop_counter) == 0:
            body_fixe = BODY_FIXE_NO_ANTICIPATION.format(**payload)
            obj = OBJECT_ABS_FIXE.format(**payload)
            body_payload = {
                "start_greetings": start_greetings, 
                "main": body_fixe, 
                "incentive": INCENTIVE, 
                "qa": qa, 
                "end_greetings": END_GREETINGS, 
                "signature": SIGNATURE
            }  
            
        elif member.cycle_type != "standard" and end_of_cycle is False:
            body_ftop = BODY_VOLANT_ABS.format(**payload)
            obj = OBJECT_ABS_VOLANT.format(**payload)
            body_payload = {
                "start_greetings": start_greetings, 
                "main": body_ftop, 
                "incentive": INCENTIVE, 
                "qa": qa, 
                "end_greetings": END_GREETINGS, 
                "signature": SIGNATURE
            }  
            
        elif member.cycle_type != "standard" and end_of_cycle:
            body_ftop = BODY_VOLANT_NO_ACTIVE.format(**payload)
            obj = OBJECT_ABS_VOLANT.format(**payload)
            body_payload = {
                "start_greetings": start_greetings, 
                "main": body_ftop, 
                "incentive": INCENTIVE, 
                "qa": qa, 
                "end_greetings": END_GREETINGS, 
                "signature": SIGNATURE
            }  
        else:
            print('!!!!!!!!!! WARNING !!!!!!!!!!!!!')
            print('this member payload cannot be constructed --->', member.display_name)
            return
    
        body = MAIL_BODY.format(**body_payload)
        msg = self.write({"body": body, "subject": obj})
        try:
            self.send(msg)
        except Exception as e:
            print(e)
            
        
    def generate_abs_mail_payload(self, member: Member) -> Dict[str, Any]:
        payload = {}
        payload.update(member.__dict__)
        payload.update(VAR_PAYLOAD)
        if member.gender == "female":
            payload.update(FEMALE)
        if member.gender == "male":
            payload.update(MALE)
        else:
            payload.update(NEUTRAL)
        
        return payload
