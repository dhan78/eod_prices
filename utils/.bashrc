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
alias u="rpm-ostree update && flatpak update"
alias kk="killall ptyxis"

if [ -d "$HOME/.local/bin" ] ; then
    PATH="$HOME/.local/bin:$PATH"
fi
alias reboot="systemctl reboot -i"
export JPM_USER="v032823"
export JPM_PASSWORD="Daytona,Workspace"


alias b="gsettings set org.gnome.desktop.interface text-scaling-factor 1.5"
alias s="gsettings set org.gnome.desktop.interface text-scaling-factor 1.0"
alias t="ptyxis --tab-with-profile=1a15b599330c73f669116af269018f83"
alias f="ptyxis --tab-with-profile=2a16b82c662d729e6f29c15568d5d68f"
export AWS_PROFILE=s3_rolesanywhere
alias s3='AWS_PROFILE=s3_rolesanywhere rclone mount aws:filebucketdhan /var/home/admin/s3 --daemon --vfs-cache-mode writes --allow-other'
alias gdrive="rclone mount gdrive: google --daemon"

export PS1='$(whoami)@$(hostname):$(pwd)\$ '
