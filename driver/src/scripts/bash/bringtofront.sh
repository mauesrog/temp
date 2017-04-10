# bringtofront.sh
#
# Brings the Hive Battery app to the front if the platform is running on MacOS.
#
# author: Mauricio Esquivel Rogel
# date: February 2017

if [ $# -ne 0 ]; then
	echo "bringtofront: invalid number of arguments: $# (0 required)" 1>&2
	exit 1
else
    x=$(osascript -e 'tell application "Finder" to set frontmost of process "Python" to true' 2>&1)
fi

exit 0
