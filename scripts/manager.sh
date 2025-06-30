#!/usr/bin/env bash

set -e
set -o pipefail

ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="${ROOT_DIR}/.venv"
VENV_CHECKSUM_FILE="${VENV_DIR}/requirements.sum"

if [ -z "$PIP_INDEX_URL" ]; then
  export PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
fi

# prepare python venv 
venv_base() {
  if ! "${VENV_DIR}/bin/python" --version &> /dev/null; then
    rm -rf "${VENV_DIR}"
    python3 -m venv "${VENV_DIR}"
    # now is a bug
    # https://stackoverflow.com/questions/70946286/pip-compile-raising-assertionerror-on-its-logging-handler
    "${VENV_DIR}/bin/pip" install --upgrade "pip"
    "${VENV_DIR}/bin/pip" install --upgrade "pip-tools"
  fi
}

venv_checksum() {
  files=("requirements.in")
  if [ -n "$(command -v shasum)" ]; then
    (cd "${ROOT_DIR}" && shasum -a 256 "${files[@]}")
  else
    (cd "${ROOT_DIR}" && sha256sum "${files[@]}")
  fi
}


venv_install() {
  VENV_CHECKSUM="$(cat 2>/dev/null "${VENV_CHECKSUM_FILE}" || true)"
  if [ "$(venv_checksum)" != "${VENV_CHECKSUM}" ]; then
      "${VENV_DIR}/bin/pip-compile" --no-emit-index-url "${ROOT_DIR}/requirements.in"
      "${VENV_DIR}/bin/pip" install -r "${ROOT_DIR}/requirements.txt"
      "${VENV_DIR}/bin/pip-sync" "${ROOT_DIR}/requirements.txt"
      venv_checksum > "${VENV_CHECKSUM_FILE}"
  fi
}

venv_activate() {
  if [ -z "$VIRTUAL_ENV" ]; then
    venv_base
    venv_install
    printf >&2 "activing ${VENV_DIR}/bin/activate\n"
    . "${VENV_DIR}/bin/activate"
  fi
}

venv_spawn() {
  # Inspired by https://superuser.com/a/591440
  dotdir="$(mktemp -d)"
  cat > "${dotdir}/.zshrc" <<EOF
case "\$(basename "\$SHELL")" in
  zsh)
    export ZDOTDIR="\$OLD_ZDOTDIR"
    if [ -f "\$ZDOTDIR/.zshenv" ]; then
      . "\$ZDOTDIR/.zshenv"
    fi
    if [ -f "\$ZDOTDIR/.zshrc" ]; then
      . "\$ZDOTDIR/.zshrc"
    fi
    ;;
  bash)
    if [ -f ~/.bashrc ]; then
      . ~/.bashrc
    fi
    if [ -f /etc/bash.bashrc ]; then
      . /etc/bash.bashrc
    fi
    ;;
esac
export PYTHONPATH="${VENV_DIR}/bin/python"
export VAGRANT_EXPERIMENTAL="disks"
. "${VENV_DIR}/bin/activate"

$@

printf >&2 '\\nEnter venv: ${VENV_DIR}\\n'
printf >&2 'You have entered the virtualenv now.\\n'
printf >&2 'Use CTRL-D or "exit" to quit.\\n'
EOF
  ln -s "${dotdir}/.zshrc" "${dotdir}/.bashrc"
  case $(basename "${SHELL}") in
    zsh)
      export OLD_ZDOTDIR="${ZDOTDIR:-${HOME}}"
      export ZDOTDIR="${dotdir}"
      exec zsh -i
      ;;
    bash)
      exec bash --init-file "${dotdir}/.bashrc" -i
      ;;
    *)
      printf >&2 'Unrecognized shell %s\n' "${SHELL}"
      ;;
  esac
}

case "$1" in
  venv)
    if [ -n "$VIRTUAL_ENV" ]; then
      printf >&2 'You are already in a virtualenv.\n'
      exit 0
    fi
    venv_base
    venv_install
    venv_spawn ${@:2}
    ;;
  ""|help|--help|-h)
    printf 'available commands:\n'
    printf '  venv     Open a shell with virtualenv.\n'
    ;;
  *)
    "$0" help
    exit 2
    ;;
esac