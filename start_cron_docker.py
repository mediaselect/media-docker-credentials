import configparser
import keyring
import logging
import os
import subprocess
import sys

from logging.handlers import RotatingFileHandler

user_home = os.path.expanduser("~")
config_path = f"{user_home}/.config/media-docker-credentials/config.ini"
config = configparser.ConfigParser()
config.read(config_path)

log_file = os.path.expanduser("~/.local/share/media-docker-credentials/logs/inject_credentials.log")
max_bytes = 10 * 1024 * 1024  # 10 MB
backup_count = 5

log_dir = os.path.dirname(log_file)
os.makedirs(log_dir, exist_ok=True)

log_handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count)
log_format = '%(asctime)s %(levelname)s %(message)s'
log_datefmt = '%d-%m-%Y %H:%M:%S'
formatter = logging.Formatter(log_format, log_datefmt)

log_handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.addHandler(log_handler)
logger.setLevel(logging.INFO)

DOCKER_CONTAINER_NAME = config['Docker']['container_name']

USERNAME_MEDIASELECT = keyring.get_password("media-select", "email")
PASSWORD_MEDIASELECT = keyring.get_password("media-select", "password")
FREEBOX_SERVER_IP = keyring.get_password("freeboxos", "username")
ADMIN_PASSWORD = keyring.get_password("freeboxos", "password")

if not USERNAME_MEDIASELECT or not PASSWORD_MEDIASELECT or not FREEBOX_SERVER_IP or not ADMIN_PASSWORD:
    logging.error("Credentials not found by keyring.")
    sys.exit(1)

env_command = (
    f"export USERNAME_MEDIASELECT='{USERNAME_MEDIASELECT}' PASSWORD_MEDIASELECT='{PASSWORD_MEDIASELECT}' "
    f"FREEBOX_SERVER_IP='{FREEBOX_SERVER_IP}' ADMIN_PASSWORD='{ADMIN_PASSWORD}' && "
    f"/home/seluser/.venv/bin/python3 /home/seluser/select-freeboxos/cron_docker.py "
    ">> /var/log/select_freeboxos/select_freeboxos.log 2>&1"
)

try:
    subprocess.run(
        ["docker", "exec", "-u", "seluser", DOCKER_CONTAINER_NAME, "bash", "-c", env_command],
        check=True
    )
    print("Credentials injected and script started successfully.")
except subprocess.CalledProcessError as e:
    print("Error injecting credentials:", e)
