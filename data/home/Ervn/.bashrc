#
# ~/.bashrc
#

# If not running interactively, don't do anything
[[ $- != *i* ]] && return

alias ls='ls --color=auto'
alias grep='grep --color=auto'
PS1='[\u@\h \W]\$ '

source /usr/share/nvm/init-nvm.sh

alias emacs='emacs -nw'

alias poweroff='sudo poweroff'
alias reboot='sudo reboot'
