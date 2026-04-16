case $- in
		*i*) ;;
			*) return;;
esac

alias mysql='mysql -h 127.0.0.1 -u s2501045 -p'
cd "$HOME"
PS1='\[\e[01;32m\]\u@\h\[\e[00m\]:\[\e[01;34m\]\w\[\e[00m\]\$ '
export APP_LOG_DIR="/var/log/student-apps/$STUDENT_ID"
alias runapp="python3 app.py >> \"$APP_LOG_DIR/app.log\" 2>&1"
[ -f "$HOME/shared/NOTICE.txt" ] && echo "" && cat "$HOME/shared/NOTICE.txt"
[[ $- == *i* ]] && clear && cat /etc/motd
