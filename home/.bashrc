# ~/.bashrc

# If not running interactively, don't do anything
[[ $- != *i* ]] && return

alias ls='ls --color=auto'
alias grep='grep --color=auto'
alias fastfetch='fastfetch --disable-linewrap'

#HISTCONTROL=ignoreboth
export HISTCONTROL=ignoreboth:erasedups
export HISTIGNORE="ls:ll:cd:pwd:bg:fg:history:clear"
export HISTTIMEFORMAT="%F %T "

#PS1='\[\033[1;35m\]┌──(\[\033[1;32m\]\u@\h\[\033[1;35m\])-[\[\033[0m\]\w\[\033[1;35m\]]\n└─\[\033[1;33m\][\t] ❯\[\033[0m\] '

fastfetch 
export PATH="$PATH:$HOME/.local/bin"

set_window_title() {
    local dir_name=$(basename "$PWD")
    if [ "$PWD" = "$HOME" ]; then
        dir_name="~"
    fi
    echo -ne "\033]0;[${dir_name}] - Bash\007"
}

trap 'echo -ne "\033]0;[$(basename "$PWD")] - $BASH_COMMAND\007"' DEBUG
PROMPT_COMMAND="set_window_title"

eval "$(starship init bash)"
