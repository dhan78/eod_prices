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

# Updates & system
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

# SSL Fix: Point everything to the verified system bundle
export SSL_CERT_FILE=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem
export CURL_CA_BUNDLE=$SSL_CERT_FILE
export AWS_CRT_CA_BUNDLE=$SSL_CERT_FILE

# Export AWS credentials
if command -v aws &> /dev/null; then
    eval $(aws configure export-credentials --profile "$AWS_PROFILE" --format env 2>/dev/null)
fi

# ——— AUTOMATIC S3 MOUNT ———
if [[ -t 0 ]]; then
    # Ensure cache dir
    [[ ! -d /tmp/mountpoint-cache ]] && mkdir -p /tmp/mountpoint-cache && chmod 1777 /tmp/mountpoint-cache

    # Auto-mount only if not already mounted
    if ! mountpoint -q /var/home/admin/s3 2>/dev/null; then
        mount-s3 filebucketdhan /var/home/admin/s3 \
            --allow-other \
            --cache /tmp/mountpoint-cache \
            --max-cache-size 5120 \
            --metadata-ttl 600 --foreground >/tmp/mount-s3.log 2>&1 &
        disown
        echo "S3 auto-mounted → /var/home/admin/s3"
    fi
fi

# Aliases for Manual Controls
alias s3mount='mount-s3 filebucketdhan /var/home/admin/s3 --allow-other --cache /tmp/mountpoint-cache --max-cache-size 5120 --metadata-ttl 600 --foreground >/tmp/mount-s3.log 2>&1 & disown'
alias s3unmount='sudo umount /var/home/admin/s3'
alias gdrive='rclone mount gdrive: /var/home/admin/google --daemon --allow-other &'

# Prompt
PS1='$(whoami)@$(hostname):$(pwd)\$ '

# pnpm
export PNPM_HOME="/var/home/admin/.local/share/pnpm"
[[ ":$PATH:" != *":$PNPM_HOME:"* ]] && export PATH="$PNPM_HOME:$PATH"

