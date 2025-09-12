# .bashrc

# Source global definitions
if [ -f /etc/bashrc ]; then
    . /etc/bashrc
fi

# User specific environment
if ! [[ "$PATH" =~ "$HOME/.local/bin:$HOME/bin:" ]]; then
    PATH="$HOME/.local/bin:$HOME/bin:$PATH"
fi
export PATH

# Uncomment the following line if you don't like systemctl's auto-paging feature:
# export SYSTEMD_PAGER=

# User specific aliases and functions
if [ -d ~/.bashrc.d ]; then
    for rc in ~/.bashrc.d/*; do
        if [ -f "$rc" ]; then
            . "$rc"
        fi
    done
fi
unset rc

# If not running interactively, don't do anything
[[ $- != *i* ]] && return

alias ls='ls --color=auto'
PS1='[\u@\h \W]\$ '
set -o vi
alias ll="ls -lrt"
alias vi="vim"
export FZF_DEFAULT_COMMAND="find -L"
alias vi="vim"
alias vf='vim $(fzf)'
alias cdf='cd $(fzf)'
alias u="sudo dnf update && flatpak update"
alias kk="killall ptyxis"

if [ -d "$HOME/.local/bin" ] ; then
    PATH="$HOME/.local/bin:$PATH"
fi
alias reboot="systemctl reboot -i"
export JPM_USER="v032823"
export JPM_PASSWORD="Daytona,Workspace"

alias b="gsettings set org.gnome.desktop.interface text-scaling-factor 1.5"
alias s="gsettings set org.gnome.desktop.interface text-scaling-factor 1.0"
alias s3="rclone mount aws:filebucketdhan ~/s3 -vv --s3-profile S3_RW_access-766644654959 --daemon"
alias gdrive="rclone mount gdrive: google --daemon"

#source ~/IdeaProjects/eod_prices/venv_intellij/bin/activate
export PS1='$(whoami)@$(hostname):$(pwd)\$ '
export DOCKER_HOST=unix:///run/user/$UID/podman/podman.sock

