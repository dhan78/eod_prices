#!/usr/bin/bash
export DISPLAY=':0'
WIN="CAR_PRD"

while [ 1 ]; 
do  
	pid=`/usr/bin/xdotool search --onlyvisible --class "Wfica"`
	if [[ "$pid" -gt "1" ]]; then

		if [[ "$(/usr/bin/xdotool getactivewindow)" -ne "$pid" ]]; then
			/usr/bin/xdotool search --onlyvisible --name $WIN keydown alt keyup alt keydown alt keyup alt
			/usr/bin/xdotool mousemove_relative --sync 10 10
			echo "LVDI is not activeWindow. DON'T BE LAZY!!! sent alt_up_down"
		else
			echo "Actively working! Keep it up!" 
			/usr/bin/xdotool mousemove_relative --sync 10 10
			echo "Moving Mouse relative ..."
			
		fi # for checking mouse location
	else
		abc=123	
		# echo "No LVDI detected"
	fi # for checking if vdi is open

sleep 120;
done;
