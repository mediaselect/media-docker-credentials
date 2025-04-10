#!/bin/bash


if [ $(id -u) != 0 ] ; then
  echo "Les droits Superuser (root) sont nécessaires pour installer media_docker_linux"
  echo "Lancez 'sudo $0' pour obtenir les droits Superuser."
  exit 1
fi

is_valid_python3_version() {
    [[ $1 =~ ^python3\.[0-9]+$ ]]
}
PYTHON_VERSIONS=($(compgen -c python3. | sort -Vr))
PYTHON_COMMAND=""
for version in "${PYTHON_VERSIONS[@]}"
do
    if is_valid_python3_version "$version" && command -v $version &> /dev/null
    then
        ver_number=${version#python3.}
        if (( ver_number >= 6 ))
        then
            PYTHON_COMMAND=$version
            break
        fi
    fi
done
if [[ -z $PYTHON_COMMAND ]]
then
    echo "Une version 3.6 minimum de Python est nécessaire."
    echo "Merci d'installer une version de Python supérieur ou égale à 3.6 puis de relancer le programme."
    exit 1
else
    echo "Utilisation de $PYTHON_COMMAND (version $($PYTHON_COMMAND --version 2>&1 | cut -d' ' -f2))"
fi

echo -e "Installation des librairies nécessaires\n"

step_1_update() {
  echo "---------------------------------------------------------------------"
  echo "Starting step 1 - Update"
  apt update || { echo "Échec de la mise à jour des dépôts"; exit 1; }
  echo "Step 1 - Update done"
}

step_2_mainpackage() {
  echo "---------------------------------------------------------------------"
  echo "Starting step 2 - packages"
  apt -y install curl || { echo "Échec de l'installation de curl"; exit 1; }
  apt -y install unzip || { echo "Échec de l'installation de unzip"; exit 1; }
  echo "step 2 - packages done"
}

step_3_media_docker_linux_download() {
  echo "---------------------------------------------------------------------"
  echo "Starting step 3 - media_docker_linux download"
  user_home=$(eval echo ~${SUDO_USER:-$USER})
  cd "$user_home" || { echo "Failed to change to home directory"; exit 1; }
  echo "Downloading credentials package..."
  if ! curl -L -o media-docker-credentials.zip https://github.com/mediaselect/media-docker-credentials/archive/refs/tags/v1.0.0.zip; then
    echo "Download failed"
    exit 1
  fi
  if [ -d "media-docker-credentials" ]; then
    echo "Removing existing media-docker-credentials directory..."
    rm -rf "media-docker-credentials"
  fi
  echo "Extracting files..."
  if ! unzip media-docker-credentials.zip; then
    echo "Unzip failed"
    exit 1
  fi
  echo "Setting up credentials directory..."
  mv media-docker-credentials-1.0.0 media-docker-credentials
  rm media-docker-credentials.zip

  echo "Step 3 - media_docker_linux download done"
}

step_4_create_media-docker-credentials_directories() {
  echo "---------------------------------------------------------------------"
  echo "Starting step 4 - Creating media-docker-credentials directories"
  user=${SUDO_USER:-${USER}}
  echo "User: $user"

  mkdir -p "$user_home/.local/share/media-docker-credentials/logs"
  mkdir -p "$user_home/.config/media-docker-credentials"
  chown -R $user:$user "$user_home/.local/share/media-docker-credentials"
  chown -R $user:$user "$user_home/.config/media-docker-credentials"
  chown -R $user:$user "$user_home/media-docker-credentials"

  if [ ! -f "$user_home/.config/media-docker-credentials/config.ini" ]; then
    cp "$user_home/media-docker-credentials/config.ini" "$user_home/.config/media-docker-credentials/config.ini"
    chown $user:$user "$user_home/.config/media-docker-credentials/config.ini"
  fi

  echo "Step 4 - media-docker-credentials directories created"
}

step_5_virtual_environment() {
  echo "---------------------------------------------------------------------"
  echo "Starting step 5 - Virtual env + requirements install"
  cd $user_home/.local/share/media-docker-credentials
  echo "Downloading virtualenv..."
  if ! curl --location -o virtualenv.pyz https://bootstrap.pypa.io/virtualenv.pyz; then
    echo "Failed to download virtualenv"
    return 1
  fi
  echo "Creating virtual environment..."
  if ! sudo -u $user $PYTHON_COMMAND virtualenv.pyz .venv; then
    echo "Failed to create virtual environment"
    return 1
  fi
  echo "Installing requirements..."
  if ! sudo -u $user bash -c "source .venv/bin/activate && pip install -r '$user_home/media-docker-credentials/requirements.txt'"; then
    echo "Failed to install requirements"
    return 1
  echo "Step 5 - Virtual env created and requirements installed"
  fi
}


STEP=0

case ${STEP} in
  0)
  echo "Starting installation ..."
  step_1_update
  step_2_mainpackage
  step_3_media_docker_linux_download
  step_4_create_media-docker-credentials_directories
  step_5_virtual_environment
  ;;
esac
