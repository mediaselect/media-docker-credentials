import configparser
import keyring
import getpass
import logging
import os
import requests

from requests.exceptions import ConnectTimeout, ConnectionError, RequestException
from bs4 import BeautifulSoup
from subprocess import Popen, PIPE, run, CalledProcessError

user_home = os.path.expanduser("~")
config_path = f"{user_home}/.config/media-docker-credentials/config.ini"
config = configparser.ConfigParser()
config.read(config_path)

DOCKER_CONTAINER_NAME = config['Docker']['container_name']

def get_website_title(url):
    """Get the title of a website."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.find("title").string.strip()
        return title
    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred: {e}")
        return None

def check_freebox_connection(server_ip, timeout=6):
    """
    Check connection to a Freebox server

    Args:
        server_ip (str): IP address of the Freebox server
        timeout (int): Timeout in seconds for the connection attempt

    Returns:
        int or None: HTTP status code if successful, None if connection failed
    """
    try:
        response = requests.head(f"https://{server_ip}/login.php", timeout=timeout)
        print(f"Successfully connected to {server_ip}")
        return response.status_code
    except ConnectTimeout:
        print(f"Connection to {server_ip} timed out after {timeout} seconds")
        return None
    except ConnectionError:
        print(f"Failed to connect to {server_ip}")
        return None
    except RequestException as e:
        print(f"Request failed: {e}")
        return None

answers = ["oui", "non"]
opciones = ["1", "2", "3"]
opcion = 5
https = "false"

print("\nBienvenue dans le programme d'installation pour stocker par chiffrement vos "
      "identifiants de connexion à MEDIA-select.fr et Freebox OS."
      "\n\nVous pouvez vous connecter à Freebox OS soit par internet, "
      "soit par votre réseau local. Par mesure de sécurité, le programme "
      "utilisera uniquement des connexions par HTTPS pour se connecter par "
      "internet. La connexion par le réseau local se fera en HTTP et n'est donc "
      "pas sécurisé. Ceci ne pose pas de problème si votre PC est fixe et "
      "qu'il reste toujours connecté à votre domicile dans votre réseau "
      "local que vous partagez seulement avec des personnes de confiance. "
      "Dans le cas contraire, il est conseillé de configurer "
      "l'accès à distance à Freebox OS de manière sécurisée, avec un nom de domaine personnalisé: "
      "https://www.universfreebox.com/article/36003/Tuto-Accedez-a-Freebox-OS-a-distance-de-maniere-securisee-avec-un-nom-de-domaine-personnalise\n"
      "En plus de sécuriser votre connexion par HTTPS, ceci vous permettra de vous "
      "connecter en déplacement.\n")


while opcion not in opciones:
    opcion = input("Merci de choisir une des options suivantes:\n\n1) J'ai "
                "configuré l'accès à Freebox OS hors de mon domicile et "
                "je choisis de sécuriser ma connexion par HTTPS.\n\n2) Mon "
                "PC restera toujours connecté au réseau local de ma "
                "Freebox et je ne veux pas configurer l'accès à "
                "à Freebox OS hors de mon domicile.\n\n3) Je "
                "désire quitter le programme d'installation.\n\n"
                "Choisissez entre 1 et 3: ")

if opcion == "1":

    FREEBOX_SERVER_IP = input(
        "\nVeuillez saisir l'adresse à utiliser pour l'accès distant de "
        "votre Freebox.\nCelle-ci peut ressembler à "
        "https://votre-sous-domaine.freeboxos.fr:55412\n"
        "Veillez à choisir le port d'accès distant sécurisé (HTTPS et "
        "non HTTP) pour sécuriser la connexion: \n"
    )
    FREEBOX_SERVER_IP = FREEBOX_SERVER_IP.replace("https://", "")
    FREEBOX_SERVER_IP = FREEBOX_SERVER_IP.replace("http://", "")
    FREEBOX_SERVER_IP = FREEBOX_SERVER_IP.rstrip("/")

    http_response = check_freebox_connection(FREEBOX_SERVER_IP)

    while http_response != 200:
        FREEBOX_SERVER_IP = input("\nLa connexion à la Freebox Server a "
            "échoué.\n\nMerci de saisir de nouveau l'adresse à utiliser pour "
            "l'accès distant de votre Freebox.\nCelle-ci peut ressembler à "
            "https://votre-sous-domaine.freeboxos.fr:55412\n"
            "Veillez à choisir le port d'accès distant sécurisé (HTTPS et "
            "non HTTP) pour sécuriser la connexion: \n")
        FREEBOX_SERVER_IP = FREEBOX_SERVER_IP.replace("https://", "")
        FREEBOX_SERVER_IP = FREEBOX_SERVER_IP.replace("http://", "")
        FREEBOX_SERVER_IP = FREEBOX_SERVER_IP.rstrip("/")
        http_response = check_freebox_connection(FREEBOX_SERVER_IP)

elif opcion == "2":
    print("\nVous avez choisi de vous connecter à votre Freebox par votre "
        "réseau local.")

    FREEBOX_SERVER_IP = "192.168.1.254"

    url = "http://" + FREEBOX_SERVER_IP
    title = get_website_title(url)

    option = 5
    repeat = False
    out_prog = "nose"

    while title != "Freebox OS":
        print("\nLa connexion à la Freebox Server a échoué.\n\nMerci de vérifier "
                "que vous êtes bien connecté au réseau local de votre Freebox "
                "(cable ethernet ou wifi).")
        if repeat:
            print("\nLe programme a détecté une nouvelle fois que le routeur "
                "est différent de celui de la Freebox server.\n")
        if title is not None:
            print("\nLe programme a détecté comme nom possible de votre "
                "routeur la valeur suivante: " + title + "\n")
        else:
            print("\nLe programme n'a pas détecté le nom de votre routeur.\n")
        if repeat:
            while out_prog.lower() not in answers:
                out_prog = input("Voulez-vous continuer de tenter de vous "
                                "connecter? (repondre par oui ou non): ")
        if out_prog.lower() == "non":
            print('Sortie du programme.\n')
            exit()

        print("Merci de vérifier que vous êtes bien connecté au réseau local "
            "de votre Freebox serveur. \n")
        while option not in opciones:
            option = input(
                "Après avoir vérifié la connexion, vous pouvez choisir une "
                "de ces 3 options pour continuer:\n\n1) Vous n'étiez pas "
                "connecté au réseau local de votre Freebox serveur "
                "précédemment et vous voulez tenter de nouveau de vous "
                "connecter\n\n2) Vous êtiez sûr d'être connecté au réseau "
                "local de votre Freebox serveur. Vous avez vérifié l'adresse "
                "ip de la Freebox server dans la fenêtre 'Paramètres de la "
                "Freebox' après avoir clické sur 'Mode réseau' et celle-ci "
                "est différente de 192.168.1.254.\n\n3) "
                "Vous voulez utiliser le nom d'hôte mafreebox.freebox.fr qui "
                "fonctionnera sans avoir besoin de vérifier l'adresse IP de "
                "la freebox server. Il faudra cependant veiller à ne pas "
                "utiliser de VPN avec votre PC/Mac pour pouvoir vous "
                "connecter.\n\nChoisissez entre 1 et 3: "
            )
        if option == "1":
            cmd = ["ip", "route", "show", "default"]
            ip_ad = Popen(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True)
            stdout, stderr = ip_ad.communicate()
            FREEBOX_SERVER_IP = stdout.split()[2]

            print("\nLe programme a détecté que votre routeur "
                "a l'adresse ip " + FREEBOX_SERVER_IP + "\n\nLe programme va "
                "maitenant vérifier si celui-ci est celui de la Freebox server\n")
        elif option == "2":
            FREEBOX_SERVER_IP = input(
                "\nVeuillez saisir l'adresse IP de votre Freebox: "
            )
        else:
            FREEBOX_SERVER_IP = "mafreebox.freebox.fr"

        option = "5"

        print("\nNouvelle tentative de connexion à la Freebox:\n\nVeuillez patienter.")
        print("\n---------------------------------------------------------------\n")

        url = "http://" + FREEBOX_SERVER_IP
        title = get_website_title(url)

        repeat = True
        out_prog = "nose"

else:
    print("Merci d'avoir utilisé le programme d'installation pour stocker par chiffrement vos "
        "identifiants de connexion à MEDIA-select.fr à Freebox OS."
        "\n\nAu revoir!")
    exit()

try:
    keyring.set_password("freeboxos", "username", FREEBOX_SERVER_IP)
    if opcion == 1:
        print("L'URL pour accéder à Freebox OS a été enregistré par "
            "keyring.")
    else:
        print("L'adresse IP pour accéder à Freebox OS a été enregistré par "
            "keyring.")
except Exception as e:
    if opcion == 1:
        print(f"Error: Failed to store Freeboxos URL with keyring. {str(e)}")
    else:
        print(f"Error: Failed to store Freeboxos IP adress with keyring. {str(e)}")
    exit()


if opcion == "1":
    https = "true"

print("Le programme peut atteindre la page de login de Freebox OS. Il "
    "va maintenant tenter de se connecter à Freebox OS avec votre "
    " mot de passe:")

not_connected = True
test_password_response = "no_se"
answer_hide = "maybe"
n = 0

while not_connected:
    try_again ="maybe"
    if answer_hide.lower() == "oui":
        freebox_os_password = input(
            "\nVeuillez saisir votre mot de passe admin de la Freebox: "
        )
    else:
        freebox_os_password = getpass.getpass(
            "\nVeuillez saisir votre mot de passe admin de la Freebox: "
        )
    print(
        "\nVeuillez patienter pendant la tentative de connexion à "
        "Freebox OS avec votre mot de passe.\n"
    )

    try:
        cmd = [
            "docker", "exec", "-u", "seluser", DOCKER_CONTAINER_NAME, "bash", "-c",
            (
                f"FREEBOX_SERVER_IP='{FREEBOX_SERVER_IP}' "
                f"https='{https}' "
                f"freebox_os_password='{freebox_os_password}' "
                "python3 /home/seluser/select-freeboxos/test_freeboxos_password.py"
            )
        ]
        test_password = run(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True)
        test_password_response = test_password.stdout.strip()
    except CalledProcessError as e:
        print("❌ Docker exec failed:", e)
        print("Impossible de tester le mot de passe de Freebox OS dans le conteneur "
              f"Docker {DOCKER_CONTAINER_NAME}. Merci de vérifier s'il est bien en cours "
              "d'execution puis relancez le programme credentials_setup_linux.py")
        exit()

    if test_password_response == "good_password":
        not_connected = False
        try:
            keyring.set_password("freeboxos", "password", freebox_os_password)
            print("Le mot de passe admin à Freebox OS a été enregistré par "
                  "keyring.")
        except Exception as e:
            print(f"Error: Failed to store password in keyring. {str(e)}")
            exit()
    elif test_password_response == "bad_password":
        n += 1
        if n > 6:
            print(
                "\nImpossible de se connecter à Freebox OS avec ce mot de passe. "
                "Veuillez vérifier votre mot de passe de connexion admin en vous "
                "connectant à l'adresse http://mafreebox.freebox.fr/login.php puis "
                "relancez le programme credentials_setup_linux.py. "
            )
            exit()
        while try_again.lower() not in answers:
            try_again = input(
                "\nLe programme install.py n'a pas pu se connecter à Freebox OS car "
                "le mot de passe ne correspond pas à celui enregistré dans "
                "la Freebox.\nVoulez-vous essayer de nouveau?(répondre par oui ou non): "
            )

        if try_again.lower() == "oui":
            if answer_hide.lower() != "oui":
                while answer_hide.lower() not in answers:
                    answer_hide = input(
                        "\nVoulez-vous afficher le mot de passe que vous saisissez "
                        "pour que cela soit plus facile? (répondre par oui ou non): "
                    )
        else:
            exit()

response = requests.head("https://media-select.fr")
http_response = response.status_code

if http_response != 200:
    print(
        "\nVotre machine hote n'est pas connectée à internet. Veuillez "
        "vérifier votre connection internet et relancer le programme "
        "d'installation.\n\n"
    )
    exit()

username_mediaselect = input(
    "Veuillez saisir votre identifiant de connexion (adresse "
    "email) sur MEDIA-select.fr: "
)
password_mediaselect = getpass.getpass(
    "Veuillez saisir votre mot de passe sur MEDIA-select.fr: "
)

http_status = 403

while http_status != 200:
 
    response = requests.head("https://www.media-select.fr/api/v1/progweek", auth=(username_mediaselect, password_mediaselect))
    http_status = response.status_code

    if http_status != 200:
        try_again = input(
            "Le couple identifiant de connexion et mot de passe "
            "est incorrect.\nVoulez-vous essayer de nouveau?(oui ou non): "
        )
        answer_hide = "maybe"
        if try_again.lower() == "oui":
            username_mediaselect = input(
                "Veuillez saisir de nouveau votre identifiant de connexion (adresse email) sur MEDIA-select.fr: "
            )
            while answer_hide.lower() not in answers:
                answer_hide = input(
                    "Voulez-vous afficher le mot de passe que vous saisissez "
                    "pour que cela soit plus facile? (répondre par oui ou non): "
                )
            if answer_hide.lower() == "oui":
                password_mediaselect = input(
                    "Veuillez saisir de nouveau votre mot de passe sur MEDIA-select.fr: "
                )
            else:
                password_mediaselect = getpass.getpass(
                    "Veuillez saisir de nouveau votre mot de passe sur MEDIA-select.fr: "
                )


try:
    keyring.set_password("media-select", "email", username_mediaselect)
    print("\nL'email de connexion à MEDIA-select.fr a été enregistré par "
            "keyring.")
except Exception as e:
    print(f"\nError: Failed to store connection email to MEDIA-select.fr in keyring. {str(e)}")
    exit()

try:
    keyring.set_password("media-select", "password", password_mediaselect)
    print("\nLe mot de passe de connexion à MEDIA-select.fr a été enregistré par "
            "keyring.")
except Exception as e:
    print(f"\nError: Failed to store password to MEDIA-select.fr in keyring. {str(e)}")
    exit()

print("\nLe programme credentials_setup_linux.py a enregistré les identifiants de "
      "connexion à MEDIA-select.fr et Freebox OS avec succès.\n")
