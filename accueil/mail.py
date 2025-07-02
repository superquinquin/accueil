from __future__ import annotations

import copy
import glob
import logging
import smtplib
import operator
from pathlib import Path
from erppeek import Record
from email.mime.text import MIMEText
from attrs import define, field, validators
from jinja2 import Template, StrictUndefined

from typing import Callable, Any

from accueil.models.shift import ShiftMember, Shift
from accueil.exceptions import TooManyReceivers, UnknownSender, UnknownMailTemplate
from accueil.utils import into_batches



ObjMail = BodyMail = Mail = str
StrOrPath = str | Path

logger = logging.getLogger("mail")

@define(frozen=True)
class SendingConditions:
    target: str = field()
    conditions: list[tuple[str, Callable, Any]] = field()

    @classmethod
    def from_configs(cls, target: str, conditions: dict[str, Any]) -> SendingConditions:
        parsed_conditions = [(k, getattr(operator, v[0]), v[1]) for k,v in conditions.items()]
        return cls(target, parsed_conditions)

    def test_member(self, member: ShiftMember) -> bool:
        tests = []
        for key, op, value in self.conditions:
            if value == "*":
                tests.append(True)
            else:
                member_value = getattr(member, key)
                tests.append(op(member_value, value))
        return all(tests)
    


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
            template = Template(f.read(), undefined=StrictUndefined)
        return template.render(**kwargs)

    def to_mimeText(self, tx: str, rx: list[Mail], **kwargs) -> MIMEText:
        mail = MIMEText(self.render("body", **kwargs), 'html')
        mail['Subject'] = self.render("obj", **kwargs)
        mail['From'] = tx
        mail['To'] = ', '.join(rx)
        return mail


@define(repr=False)
class MailManager(object):
    __login: str = field(validator=[validators.instance_of(str)]) # type: ignore
    __password: str = field(validator=[validators.instance_of(str)]) # type: ignore
    _smtp_server: str = field(validator=[validators.instance_of(str)])
    _smtp_port: int = field(default=587, validator=[validators.instance_of(int)])
    templates: dict[str, MailTemplate] = field(default={}, validator=[validators.instance_of(dict)])
    conditions: list[SendingConditions] = field(default=[], validator=[validators.instance_of(list)])
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
        conditions: dict[str, Any],
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
        manager.register_conditions(conditions)
        return manager

    def register_templates_folders(self, *templates_folders, **named_templates_folders) -> None:
        folders = {folder.split('/')[-1]:folder for folder in templates_folders}
        folders.update(named_templates_folders)
        for name, folder_path in folders.items():
            self.register_template(name, folder_path)

    def register_conditions(self, conditions: dict[str, Any]) -> None:
        self.conditions = []
        for key, key_conditions in conditions.items():
            self.conditions.append(SendingConditions.from_configs(key, key_conditions))

    def register_template(self, name: str, folder_path: Path) -> None:
        self.templates.update({name:MailTemplate.from_folder_path(name, folder_path)})

    def register_sender(self, **kwargs: Mail) -> None:
        self.senders.update(kwargs)

    def format_mail(self, shift: Shift,  member: ShiftMember, template_name: str, tx: str, rx: list[Mail]) -> MIMEText:
        personalization = self._personalization_payload(shift, member)
        template = self.get_template(template_name)
        sender = self.get_sender(tx)
        return template.to_mimeText(sender, rx, **personalization)


    def send(self, tx: str, rx: Mail | list[Mail], msg: MIMEText) -> None:
        if len(rx) > 50:
            raise TooManyReceivers()
        with smtplib.SMTP(self._smtp_server, self._smtp_port) as smtp:
            smtp.login(self.__login, self.__password)
            # smtp.starttls()
            smtp.sendmail(
                self.get_sender(tx),
                rx,
                msg.as_string()
            )

    def send_group(self, tx: str, rx: list[Mail], msg: MIMEText) -> None:
        for batch in into_batches(rx, 50):
            with smtplib.SMTP(self._smtp_server, self._smtp_port) as smtp:
                smtp.login(self.__login, self.__password)
                # smtp.starttls()
                smtp.sendmail(
                    self.get_sender(tx),
                    batch,
                    msg.as_string()
                )

    def get_sender(self, tx: str) -> Mail:
        sender = self.senders.get(tx, None)
        if sender is None:
            raise UnknownSender()
        return sender

    def get_template(self, template_name: str) -> MailTemplate:
        template = self.templates.get(template_name, None)
        if template is None:
            raise UnknownMailTemplate()
        return template

    def _personalization_payload(self, shift: Shift, member: ShiftMember) -> dict[str, str]:
        gender = getattr(member, "gender", "neutral")
        gender_variables = self.variables["on_gender"][gender]
        variables = copy.deepcopy(self.variables["variables"])
        variables.update(gender_variables)
        variables.update(member.mail_payload)
        variables.update(shift.mail_payload)
        return variables

    def send_absence_mails(self, shift: Shift) -> None:
        for member in shift.absent_members:
            if member.mail is None:
                logger.warning(f"ABORTED abs mailing for {member.name} ({member.partner_id})")
                continue

            rx = [member.mail]
            # Counters always int for main members. Mailing operation always use main member.
            template_name = "fixe_ant_abs"
            for condition in self.conditions:
                if condition.test_member(member):
                    template_name = condition.target
                    break
                
            try:
                formated_mail = self.format_mail(shift, member, template_name, "bdm", rx)
                self.send("bdm", rx, formated_mail)
                logger.info(f"SENDING abs mailing for {member.name} ({member.partner_id})")
            except Exception as e:
                logger.error(f"Failed abs mailing for {member.name} ({member.partner_id}): {str(e)}")
