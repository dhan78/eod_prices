# .bashrc – toolbox (Fedora Silverblue)
[ -f /etc/bashrc ] && . /etc/bashrc

# PATH
export PATH="$HOME/.local/bin:$HOME/bin:/usr/local/bin:$PATH"

# Stop here if non-interactive
[[ $- != *i* ]] && return

# Basics
alias ls='ls --color=auto'
alias ll='ls -lrth'
alias vi=vim
set -o vi

# Updates & system shortcuts
alias u='rpm-ostree update && flatpak update'
alias reboot='systemctl reboot -i'
alias kk='killall ptyxis'

# Text scaling shortcuts
alias b='gsettings set org.gnome.desktop.interface text-scaling-factor 1.5'
alias s='gsettings set org.gnome.desktop.interface text-scaling-factor 1.0'

# Terminal profiles
alias t='ptyxis --tab-with-profile=eaf86203830101cf43d48ace69922637'
alias f='ptyxis --tab-with-profile=705ffc0e49070d73366c7f8d69b6d281'

# Credentials
export JPM_USER="v032823"
export JPM_PASSWORD="Daytona,Workspace"
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

# Prompt
PS1='$(whoami)@$(hostname):$(pwd)\$ '

# pnpm
export PNPM_HOME="/var/home/admin/.local/share/pnpm"
[[ ":$PATH:" != *":$PNPM_HOME:"* ]] && export PATH="$PNPM_HOME:$PATH"
