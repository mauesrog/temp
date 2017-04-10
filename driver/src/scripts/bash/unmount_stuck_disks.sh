# Ejects the disk images still attached.

for disk in $(hdiutil info | grep "Hive Battery" | awk '{ print $1 }'); do hdiutil detach $disk; done