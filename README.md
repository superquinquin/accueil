# Accueil
A minimalistic app to automatically orchestrate your shifts. Handle registrations, attendancies, shifts closure and absence emailing.

## Prerequisites
* Running odoo v12
* Using `Coop - Membership` module. [More...](https://trobz.com/blog/case-studies-3/post/la-louve-co-op-retail-grows-with-odoo-4)

## Setup
```bash
git clone https://github.com/superquinquin/accueil.git
```

### Configuration
`./configs/configs.yaml`


### Environment
It is recommended to set all your credentials inside your env. The configuration system make sure to parse en retrieve them.
Most importantly you must at least set `CONFIG_FILEPATH` which indicate to the application which config file to bind with. Knowing that the basic components of the apps are based on a scheduler, it is interesting to set `TZ`. Lastly, you must set your Odoo credentials to access the shifts data. Optionnaly, if you want to setup a mailing system you can reference your SMTP credentials.

```bash
#Base
ENV
CONFIG_FILEPATH
TZ

#Odoo
ERP_URL
ERP_DB
ERP_USERNAME
ERP_PASSWORD

#Mailing
EMAIL_LOGIN
EMAIL_PASSWORD
SMTP_SERVER
EMAIL_BDM
```

### Mails Templates
on root folder:
```bash
mkdir mail_templates
```
a mail template is a folder that must contain an `obj.html` and a `body.html`. 
```
mail_templates
    |-- template_name
    |    |-- body.html 
    |    |-- obj.html
    |
   ...
```

#### Templates
Templates are powered with Jinja2. You can inject dynamically any variables you needs `{{ variable_name }}`.
Every variables can be set via the `configs.yaml` file.
* `variables.variables` can store all variables you need.
* `variables.on_gender` can store all words variations relatives to the gender of the receivers (neutral for gender inclusive wording).

```yaml
mail:
    variables:
        variables:
            key: value
            ...
        on_gender:
            male:
                key: value
                ...
            female:
                key: value
                ...            
            neutral:
                key: value
                ...
```

### Logging
The base logging configs provides by default a StreamHandler and a Filehandler for each loggers. By default, all the logs are written in a `./volume` folder. Make sure to create the `volume` folder or to reconfigurate the handlers.

on root folder:
```bash
mkdir volume
```

### Options
The App comes with multiples configurations options that can be enabled.
* `accept_early_entrance` (DateTimeKwargs) determine how long before a shift appear in the application before it's effective start.
By default `accept_early_entrance` is set to 15 minutes, so a shift will appear on the app 15min before the shift really begins.
* `accept_late_entrance` (DateTimeKwargs) determine how long the shift will appear in the app after the effective end of the shift.
By default `accept_early_entrance` is set to 0 minutes, so that the shift doesn't remain on the application after it's effective end.
* `auto_absence_notation` (bool) Determine wether or not the app update the status of the absents members in Odoo at the end of the day.
By default `auto_absence_notation` is set to False.
* `auto_close_shifts` (bool) Determine if the app does close the shifts at the end of the day.
By default `auto_close_shifts` is set to False. `auto_absence_notation` must be True to be effective.
* `auto_close_ftop_shift` (bool) Determine if the FTOP shifts are automatically close by the app.
By default `auto_close_ftop_shift` is set to False. 
* `auto_absence_mails` (bool) Determine wether the app does send absence email to the members at the end of the day.
By default `auto_absence_mails` is set to False. `auto_absence_notation` must be True to be effective.