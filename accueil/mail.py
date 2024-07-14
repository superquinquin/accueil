from __future__ import annotations

import copy
import glob
import smtplib
from pathlib import Path
from email.mime.text import MIMEText
from attrs import define, field, validators
from jinja2 import Template

from accueil.models.shift import ShiftMember


ObjMail = BodyMail = Mail = str
StrOrPath = str | Path

@define(repr=False, frozen=True, slots=True)
class MailTemplate:
    name: str = field()
    obj: Path = field()
    body: Path = field()
    
    def __repr__(self) -> str:
        return f"<{self.name} obj: {self.obj} | body: {self.body}>"
    
    @classmethod
    def from_folder_path(cls, name: str,  folder_path: StrOrPath) -> MailTemplate:
        templates = {Path(p).stem:Path(p) for p in glob.glob(f"{folder_path}/[!_]*.html")}
        return cls(name, **templates)
    
    def render(self, name: str, **kwargs) -> str:
        template_path = getattr(self, name)
        with open(template_path, "r") as f:
            template = Template(f.read())
        return template.render(**kwargs)
    
    def to_mimeText(self, tx: str, rx: list[Mail], **kwargs) -> MIMEText:
        mail = MIMEText(self.render("body", **kwargs), 'html')
        mail['Subject'] = self.render("obj", **kwargs)
        mail['From'] = tx
        mail['To'] = ', '.join(rx)
        return mail


@define(repr=False)
class MailManager(object):
    __login: str = field(validator=[validators.instance_of(str)])
    __password: str = field(validator=[validators.instance_of(str)])
    _smtp_server: str = field(validator=[validators.instance_of(str)])
    _smtp_port: int = field(default=587, validator=[validators.instance_of(int)])
    templates: dict[str, MailTemplate] = field(default={}, validator=[validators.instance_of(dict)])
    senders: dict[str, Mail] = field(default={}, validator=[validators.instance_of(dict)])
    variables: dict[str, dict] = field(default={}, validator=[validators.instance_of(dict)])
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(server: {self._smtp_server}, port: {self._smtp_port})>"
    
    @classmethod
    def initialize(
        cls,
        *,
        login: str,
        password: str,
        smtp_server: str,
        smtp_port: int = 587,
        templates_paths: dict[str, StrOrPath],
        senders: dict[str, Mail],
        variables: dict[str, dict]
        ) -> MailManager:
        manager = cls(
            login,
            password,
            smtp_server,
            smtp_port,
            senders=senders,
            variables=variables
        )
        manager.register_templates_folders(**templates_paths)
        return manager
    
    def register_templates_folders(self, *templates_folders, **named_templates_folders) -> None:
        folders = {folder.split('/')[-1]:folder for folder in templates_folders}
        folders.update(named_templates_folders)
        for name, folder_path in folders.items():
            self.register_template(name, folder_path)
            
    def register_template(self, name: str, folder_path: list[Path]) -> None:
        self.templates.update({name:MailTemplate.from_folder_path(name, folder_path)})
        
    def register_sender(self, **kwargs: Mail) -> None:
        self.senders.update(kwargs)
        
    def format_mail(self, member: ShiftMember, template_name: str, tx: str, rx: list[Mail]) -> MIMEText:
        personalization = self._personalization_payload(member)
        template = self.get_template(template_name)
        sender = self.get_sender(tx)
        return template.to_mimeText(sender, rx, **personalization)
        

    def send(self, tx: str, rx: Mail | list[Mail], msg: MIMEText) -> None:
        with smtplib.SMTP(self._smtp_server, self._smtp_port) as smtp:
            smtp.login(self.__login, self.__password)
            smtp.starttls()
            smtp.sendmail(
                self.get_sender(tx),
                rx,
                msg.as_string()
            ) 
        
    def send_group(self, tx: str, rx: list[Mail], msg: MIMEText) -> None:
        if len(rx) > 90:
            raise ValueError("Limit the number of receivers to 90 maximum")
        
        with smtplib.SMTP(self._smtp_server, self._smtp_port) as smtp:
            smtp.login(self.__login, self.__password)
            smtp.starttls()
            smtp.sendmail(
                self.get_sender(tx),
                rx,
                msg.as_string()
            ) 
                
    def get_sender(self, tx: str) -> Mail:
        sender = self.senders.get(tx, None)
        if sender is None:
            raise KeyError("Unknown sender")
        return sender
    
    def get_template(self, template_name: str) -> MailTemplate:
        template = self.templates.get(template_name, None)
        if template is None:
            raise KeyError("template name doesn't exist")
        return template
    
    def _personalization_payload(self, member: ShiftMember) -> dict[str, str]:
        gender = getattr(member, "gender", "neutral")
        gender_variables = self.variables["on_gender"][gender]
        variables = copy.deepcopy(self.variables["variables"])
        variables.update(gender_variables)
        variables.update(member.__dict__)
        return variables
    
    def send_absence_mails(self, members: list[ShiftMember]) -> None:
        tx = self.get_sender("bdm")
        for member in members:
            if member.mail is None:
                continue
            rx = [member.mail]
            if member.cycle_type == "standard" and int(member.ftop_counter) > 0:
                template_name = "fixe_ant_abs"
            elif member.cycle_type == "standard" and int(member.ftop_counter) == 0:
                template_name = "fixe_no_ant_abs"
            elif member.cycle_type == "ftop":
                template_name = "volant_abs"

            formated_mail = self.format_mail(member, template_name, tx, rx)
            self.send(tx, rx, formated_mail)
                
                