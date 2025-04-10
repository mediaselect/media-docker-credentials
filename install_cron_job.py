import os
import subprocess
from datetime import datetime

def backup_crontab():
    # Function to back up the existing crontab
    backup_filename = f"/tmp/crontab_backup_{datetime.now().strftime('%Y%m%d%H%M%S')}.bak"
    try:
        with open(backup_filename, "w") as backup_file:
            subprocess.run(["crontab", "-l"], stdout=backup_file, check=True)
        print(f"Crontab existant sauvegardé dans : {backup_filename}")
    except subprocess.CalledProcessError:
        print("Aucun crontab existant à sauvegarder.")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde du crontab : {e}")

def add_cron_job():
    # Function to add the new cron job
    cron_job = ("@reboot /usr/sbin/anacron -t $HOME/media-docker-credentials/anacrontab "
                "-S $HOME/.local/share/media-docker-credentials")

    backup_crontab()

    try:
        current_crontab = subprocess.check_output(["crontab", "-l"], text=True)
    except subprocess.CalledProcessError:
        current_crontab = ""

    # Check if the exact cron job command already exists
    cron_lines = current_crontab.strip().splitlines()
    if cron_job.strip() in cron_lines:
        print("\nLa tâche cron existe déjà. Aucun changement réalisé.")
        return

    cron_lines.append(cron_job)
    new_crontab = "\n".join(cron_lines) + "\n"
    with subprocess.Popen(['crontab'], stdin=subprocess.PIPE, text=True) as proc:
        proc.communicate(new_crontab)

    print("\nLa tâche Cron job a été ajoutée!")

def main():

    user = os.getenv('USER')
    print(f"\nConfiguration de la tâche cron pour démarrer le programme "
          "cron_docker.py dans le conteneur Docker freeboxos_select de "
          f"l'utilisateur : {user}\n")

    confirmation = input("Cela ajoutera une nouvelle tâche cron à votre crontab. Continuer ? (o/n): ").strip().lower()

    if confirmation in ['o', 'oui']:
        add_cron_job()
    else:
        print("\nConfiguration de la tâche cron annulée.")

if __name__ == "__main__":
    main()
