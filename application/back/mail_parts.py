"""
BASED CONDITIONS

------- FIXE
--> NO_ANTICIPATION
compteur volant > 0 and compteur fixe == 0

--> ANTICIPATION
compteur volant >= 0

------- VOLANT
--> ABS

--> NOT ACTIVE DURING CYCLE ( NOT EVEN REGISTERED FOR A SHIFT)


"""



# -- VARIABLES

EXCHANGE_VIDEO = "https://www.youtube.com/watch?v=YcNOjvzw8rs"
PREVIOUS_AG_DATE = "30/03/2023"
PREVIOUS_AG_CR = "https://drive.google.com/file/d/1naGlOSkjbVRqWKw45tafjOjEMQ9sheC2/view"
CURRENT_COOP_MANUAL = "https://drive.google.com/file/d/1PwNQt4gQYkRGOPDP5LtGaqMvOTNUPJPX/view"
DEFICITED_SHIFTS_CALENDAR = "https://docs.google.com/spreadsheets/d/1_VYoIyIYMTr6P1YJXzbkuQ48sVgKIco67xmiTGORYwo/edit#gid=0"

VAR_PAYLOAD = {
    "EXCHANGE_VIDEO":EXCHANGE_VIDEO,
    "PREVIOUS_AG_DATE":PREVIOUS_AG_DATE,
    "PREVIOUS_AG_CR":PREVIOUS_AG_CR,
    "CURRENT_COOP_MANUAL":CURRENT_COOP_MANUAL,
    "DEFICITED_SHIFTS_CALENDAR":DEFICITED_SHIFTS_CALENDAR
}

MALE = {
    "arg0": "considéré",
    "arg1": "absent",
    "arg2": "blessé"
}

FEMALE = {
    "arg0": "considérée",
    "arg1": "absente",
    "arg2": "blessée"
}

NEUTRAL = {
    "arg0": "considéré.e",
    "arg1": "absent.e",
    "arg2": "blessé.e" 
}

# -- MAILS

MAIL_BODY = """\
{start_greetings}
{main}
{incentive}
{qa}
{end_greetings}
{signature}
"""

OBJECT_ABS_FIXE = "SQQ coop’ fixe : absence au service du {date} à {start_hours}"
OBJECT_ABS_VOLANT = "SQQ coop’ volant.e : absence au service du {date} à {start_hours}"

BODY_FIXE_NO_ANTICIPATION = """\
<p>
    <strong>Ta présence (ou celle de ton associé.e) lors du service du {date} de {start_hours} à {end_hours} n’a pas été enregistrée :</strong>
    tu es donc {arg0} {arg1} à ce service.
    <br>Ton compteur de services fixes en est impacté : il affiche à ce jour {std_counter} (1 absence = -1*). Ton compteur de services anticipés affiche de son côté : {ftop_counter}.
</p>
<p>
    Afin d’être de nouveau à jour, tu dois effectuer le nombre de services de rattrapage nécessaires** (1 rattrapage = +1) :
    il te suffit faire ton service de 2h45 et participer au fonctionnement du magasin. 
    Tu peux faire ce service en t’inscrivant sur ton espace membre comme pour un service anticipé,
    ce qui est le plus pratique pour l’organisation du magasin, ou bien sans t’inscrire.
</p>
"""

BODY_FIXE_ANTICIPATION = """\
<p>
    <strong>Ta présence (ou celle de ton associé.e) lors du service du {date} de {start_hours} à {end_hours} n’a pas été enregistrée :</strong>
    tu es donc {arg0} {arg1} à ce service.
    <br>Tes compteurs de service en sont impactés, notre logiciel a «régulé»
    ta situation en utilisant un service de ton compteur de services anticipés pour compenser ton absence sur ton compteur de services fixes.
    Ce dernier affiche à ce jour {std_counter} (1 absence = -1*). Ton compteur de services anticipés affiche de son côté : {ftop_counter}.
</p>
<p>
    Afin de faire à nouveau des services anticipés : il te suffit de t’inscrire sur ton espace membre
    puis faire ton service de 2h45 et participer au fonctionnement du magasin.
</p>
"""

BODY_VOLANT_ABS = """\
<p>
    <strong>Tu étais inscrit.e au service du {date} de {start_hours} à {end_hours}. Ta présence lors de ce service n’a pas été enregistrée :</strong>
    tu es donc {arg0} {arg1}.
    <br>Ton compteur de services en est impacté : il affiche à ce jour {ftop_counter} (1 absence = -1)
</p>
<p>
    Afin d’être à jour et de le rester à la fin de ton cycle {cycle_type} qui aura lieu le samedi {end_cycle_date},
    tu dois effectuer le nombre de services nécessaires** (1 rattrapage = +1) pour avoir un compteur positif (1 ou plus). 
    Il te suffit de t’inscrire sur ton espace membre
    puis faire ton service de 2h45 et participer au fonctionnement du magasin.
</p>
"""

BODY_VOLANT_NO_ACTIVE = """\
<p>
    <strong>Le dernier cycle {cycle_type} s’est terminé le samedi {end_cycle_date}.</strong>
</p>
<p>
    Pour information, ton compteur de services affiche à ce jour {ftop_counter} ( 1 service = +1 ; 1 absence = -1* ; la fin de ton cycle =-1) )
    <br>
</p>


Afin d’être à jour et de le rester à la fin de ton cycle {cycle_type} actuel qui aura lieu le samedi {end_cycle_date},
tu dois effectuer le nombre de services nécessaires**) pour avoir un compteur positif (1 ou plus).
Il te suffit de t’inscrire sur ton espace membre
(puis faire ton service de 2h45 et participer au fonctionnement du magasin.
"""

# -- COMMON SECTION
BODY_START_GREETINGS = """\
<p>
    Bonjour {mail_name},
</p>
<p>
    Nous espérons que tout va bien pour toi et ton entourage.
</p>    
"""


BODY_INCENTIVE_LIST = """\
<ul>
    <li>
        Dans la mesure du possible, viens pendant un service où nous manquons de coopérateurs pour un fonctionnement optimal du magasin, 
        <a href= "{DEFICITED_SHIFTS_CALENDAR}" target="_blank">voici le calendrier des services «déficitaires».</a>
    </li>
    <li>N’oublie pas de faire tes services fixes habituels en plus de ton ou tes rattrapages.</li>
    <li>
        Si tu en as un.e, ton associé.e peut aussi faire un ou plusieurs services de rattrapage. 
        Cependant, ne venez pas ensemble au même service : 1 seul service pourrait alors être comptabilisé.
    </li>
</ul>
"""

BODY_QA = """\
<p>
    <strong>Ø Ta situation évolue ou a déjà changé ?</strong> 
    Tu es malade ou {arg2} (arrêt de plus de 15 jours), tu es enceinte, tu deviens parent, 
    tu prévois de t’absenter 2 mois ou plus, tu changes radicalement d’emploi du temps, 
    ta santé ne te permet plus d’effectuer tes services en magasin… ? 
    Contacte-nous : pour faciliter la vie des coop’ et de la coop’, on a des solutions ! 
    Tu peux aussi consulter le manuel des membres, le lien est un peu plus bas.
</p>
<p>
    <strong>Ø Pas le temps de faire ton rattrapage avant tes prochaines courses ?</strong>
    Tu peux demander au Bureau des membres un délai de 4 semaines (= 1 cycle).
    Si ce délai n’est pas suffisant, il peut être renouvelé jusqu’à 12 semaines en tout.
</p>
<p>
    <strong>Ø Tu avais prévenu ?</strong> 
    Tu nous as peut-être avertis de ton absence et nous t’en remercions, nous n'avons sans doute pas eu le temps de prévenir ton équipe. 
    Ce courriel est automatique pour tous les coopérateurs absents qu’ils nous aient prévenus ou non. 
    En cas d’absence connue plus de 24h à l'avance : 
    pense à échanger ton service directement sur ton espace membre <a href= "{EXCHANGE_VIDEO}" target="_blank">(tuto en vidéo)</a>.
</p>
"""

BODY_END_GREETINGS = """\
<p>
    L’équipe du Bureau des membres reste à ta disposition pour toute information 
    qui n’aurait pas été prise en compte ou pour toute nouvelle demande :
    tu peux répondre à ce courriel ou passer nous voir en magasin dans le «bocal».
</p>

<p>Bonne journée et à bientôt à SuperQuinquin,</p>
"""

BODY_SIGNATURE = """\
<p>
    <strong>L’équipe du Bureau des membres</strong> &#128522;
    <br><a href= "mailto: contact-bureaudesmembres@superquinquin.net" target="_blank">contact-bureaudesmembres@superquinquin.net</a>
    <br><strong>Lien pour accéder à l'espace membre :</strong> <a href= "https://gestion.superquinquin.fr/fr_FR/" target="_blank">https://gestion.superquinquin.fr/fr_FR/</a>
</p>

<p>
    * Décision votée lors de l’AG du {PREVIOUS_AG_DATE} et <a href="{PREVIOUS_AG_CR}" target="_blank">compte rendu</a>
    <br>** Manuel du membre : <a href="{CURRENT_COOP_MANUAL}" target="_blank">lien dernière version</a>
</p>

<p>
    PS: Les missions du Bureau des membres sont assurées par des coopérateurs comme toi.
    Il est possible que nous (ou le logiciel) fassions des erreurs. 
    Il est possible qu’une réponse mette un peu de temps à t’arriver 
    (si tu trouves que nous sommes constamment vraiment trop longs et que tu ferais un bien meilleur travail,
    n’hésite pas à nous rejoindre pour nous aider dans nos missions, nous t’accueillerons avec joie &#128521; .)
</p>
"""




# -- PRELOAD

START_GREETINGS = BODY_START_GREETINGS
INCENTIVE = BODY_INCENTIVE_LIST.format(
    DEFICITED_SHIFTS_CALENDAR=DEFICITED_SHIFTS_CALENDAR
)
QA = BODY_QA.format(
    EXCHANGE_VIDEO=EXCHANGE_VIDEO
)
END_GREETINGS = BODY_END_GREETINGS
SIGNATURE = BODY_SIGNATURE.format(
    PREVIOUS_AG_DATE=PREVIOUS_AG_DATE,
    PREVIOUS_AG_CR=PREVIOUS_AG_CR,
    CURRENT_COOP_MANUAL=CURRENT_COOP_MANUAL
)