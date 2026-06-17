alias mysql='mysql -h 127.0.0.1 -u omni -p'
cd "$HOME"
export APP_LOG_DIR="/var/log/student-apps/$STUDENT_ID"
PS1='\[\e[01;32m\]\u@\h\[\e[00m\]:\[\e[01;34m\]\w\[\e[00m\]\$ '
[[ $- == *i* ]] && clear && cat /etc/motd
[ -f "$HOME/shared/NOTICE.txt" ] && echo "" && cat "$HOME/shared/NOTICE.txt"
alias runapp="/usr/local/bin/runapp-safe"
python3() {
    if [ "$#" -eq 1 ] && [ "$1" = "app.py" ] || [ "$#" -eq 1 ] && [ "$1" = "$HOME/app.py" ]; then
        /usr/local/bin/runapp-safe
    else
        command python3 "$@"
    fi
}
