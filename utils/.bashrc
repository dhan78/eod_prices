# .bashrc – toolbox (Fedora Silverblue)
[ -f /etc/bashrc ] && . /etc/bashrc
# ===========================================================
# Custom prompt: git branch/upstream + venv, two-line layout
# ===========================================================

# ---- 256-color palette ----
__c_reset='\[\e[0m\]'
__c_cwd='\[\e[38;5;39m\]'      # bright blue   — cwd
__c_glocal='\[\e[38;5;42m\]'   # green         — local branch
__c_gup='\[\e[38;5;245m\]'     # dim gray      — upstream branch
__c_gsep='\[\e[38;5;240m\]'    # darker gray   — brackets / pipe
__c_venv='\[\e[38;5;250m\]'    # light gray    — venv label
__c_ps='\[\e[38;5;240m\]'      # muted         — "PS" label
__c_dollar='\[\e[38;5;33m\e[1m\]'  # bold blue — $

# ---- Git info: one rev-parse call covers repo check + branch + upstream ----
__git_prompt() {
    local out branch upstream
    out=$(git rev-parse --abbrev-ref HEAD '@{u}' 2>/dev/null)
    [ -z "$out" ] && return

    branch=$(printf '%s\n' "$out" | sed -n '1p')
    upstream=$(printf '%s\n' "$out" | sed -n '2p')

    if [ "$branch" = "HEAD" ]; then
        branch=$(git rev-parse --short HEAD 2>/dev/null) || return
    fi

    if [ -n "$upstream" ]; then
        printf '%s[%s%s%s %s|%s %s%s%s%s]%s' \
            "$__c_gsep" "$__c_reset" \
            "$__c_glocal" "$branch" "$__c_reset" \
            "$__c_gsep"  "$__c_reset" \
            "$__c_gup" "$upstream" "$__c_reset" \
            "$__c_gsep"
    else
        printf '%s[%s%s%s%s]%s' \
            "$__c_gsep" "$__c_reset" \
            "$__c_glocal" "$branch" "$__c_reset" \
            "$__c_gsep"
    fi
}

# ---- Suppress venv's own "(venv) " prefix; we render it ourselves ----
export VIRTUAL_ENV_DISABLE_PROMPT=1

__venv_prompt() {
    [ -z "$VIRTUAL_ENV" ] && return
    local label="${VIRTUAL_ENV_PROMPT:-$(basename "$VIRTUAL_ENV")}"
    label="${label#(}"; label="${label%)}"
    printf '%s(%s)%s ' "$__c_venv" "$label" "$__c_reset"
}

# ---- Prompt assembly ----
__set_prompt() {
    local git venv cwd tb dl
    git=$(__git_prompt)
    venv=$(__venv_prompt)
    cwd="${__c_cwd}\w${__c_reset}"
    tb=$(__tb_prompt)
    dl="${__c_dollar}\$${__c_reset}"

    if [ -n "$git" ]; then
        PS1="${git}\n${venv}${tb}${cwd} ${dl} "
    else
        PS1="${venv}${tb}${cwd} ${dl} "
    fi
}
PROMPT_COMMAND='__set_prompt'
__tb_prompt() {
    [ -f /run/.toolboxenv ] || return
    local name
    name=$(sed -n 's/^name="\(.*\)"$/\1/p' /run/.containerenv 2>/dev/null)
    printf '\[\e[38;5;208m\][tb:%s]\[\e[0m\] ' "${name:-toolbox}"
}

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
