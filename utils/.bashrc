# .bashrc – toolbox (Fedora Silverblue)
[ -f /etc/bashrc ] && . /etc/bashrc
[ -f ~/.bash_prompt ] && . ~/.bash_prompt


# ---- Better history across many shells ----
shopt -s histappend
HISTSIZE=10000
HISTFILESIZE=20000
PROMPT_COMMAND="history -a; $PROMPT_COMMAND"

# ---- Optional ----
# Vi edit mode (matches my PSReadLine config):
# set -o vi

# Avoid `git status` etc. contending for index lock during prompt:
export GIT_OPTIONAL_LOCKS=0

# PATH
export PATH="$HOME/.local/bin:$HOME/bin:/usr/local/bin:$PATH"

# Stop here if non-interactive
[[ $- != *i* ]] && return

vi() {
    flatpak run org.vim.Vim "$@"
}

# Basics
alias ls='ls --color=auto'
alias ll='ls -lrth'
#alias vi=vim
set -o vi

# Updates & system shortcuts
alias u='rpm-ostree update && flatpak update'
alias reboot='systemctl reboot -i'
alias kk='killall ptyxis'

# Text scaling shortcuts
alias b='gsettings set org.gnome.desktop.interface text-scaling-factor 1.32'
alias s='gsettings set org.gnome.desktop.interface text-scaling-factor 1.0'

# Terminal profiles
alias t='ptyxis --tab-with-profile=0598d52a173ba2c5a7b658fa6a14775a'
alias f='ptyxis --tab-with-profile=705ffc0e49070d73366c7f8d69b6d281'

# Credentials
export JPM_USER="v032823"
export JPM_PASSWORD="545 washington blvd"
export AWS_PROFILE=s3_rolesanywhere

# SSL Fix: Points to the verified 2.5MB system bundle
export SSL_CERT_FILE=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem
export CURL_CA_BUNDLE=$SSL_CERT_FILE
export AWS_CRT_CA_BUNDLE=$SSL_CERT_FILE

# ——— AUTOMATIC S3 MOUNT (LIVE - NO CACHE) ———
if [[ -t 0 ]]; then
    # Auto-mount only if not already mounted
    if ! mountpoint -q /var/home/admin/s3 2>/dev/null; then
        # Removed --cache and set --metadata-ttl 0 for live Nautilus views
        mount-s3 filebucketdhan /var/home/admin/s3 \
            --allow-other \
            --metadata-ttl 0 \
            --foreground >/tmp/mount-s3.log 2>&1 &
        disown
        echo "S3 auto-mounted (Live mode, No Cache) → /var/home/admin/s3"
    fi
fi

# Manual Controls
alias s3unmount='sudo umount -l /var/home/admin/s3'
alias s3remount='s3unmount && mount-s3 filebucketdhan /var/home/admin/s3 --allow-other --metadata-ttl 0 --foreground >/tmp/mount-s3.log 2>&1 & disown'
alias gdrive='rclone mount gdrive: /var/home/admin/google --daemon --allow-other &'


# pnpm
export PNPM_HOME="/var/home/admin/.local/share/pnpm"
[[ ":$PATH:" != *":$PNPM_HOME:"* ]] && export PATH="$PNPM_HOME:$PATH"
export GITHUB_PAT="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123"
