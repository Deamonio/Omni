case $- in
		*i*) ;;
			*) return;;
esac

export PATH="$HOME:$PATH"
alias mysql='mysql -h 127.0.0.1 -u omni -p'
cd "$HOME"
PS1='\[\e[01;32m\]\u@\h\[\e[00m\]:\[\e[01;34m\]\w\[\e[00m\]\$ '
PS1='\[\e[01;32m\]\u@\h\[\e[00m\]:\[\e[01;34m\]\w\[\e[00m\]\$ (admin) '
echo ""
echo "  관리자 계정 – 'omni --help' 로 사용법 확인"
echo ""
alias mysql='mysql -h 127.0.0.1 -u omni -p'
export APP_LOG_DIR="/var/log/student-apps/$STUDENT_ID"
alias runapp="python3 app.py >> \"$APP_LOG_DIR/app.log\" 2>&1"
[ -f "$HOME/shared/NOTICE.txt" ] && echo "" && cat "$HOME/shared/NOTICE.txt"
[[ $- == *i* ]] && clear && cat /etc/motd
