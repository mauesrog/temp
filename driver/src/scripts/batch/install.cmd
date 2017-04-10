rem Creates the required file structure in the user's file system to enable access to the .hive file.
rem It also generates an application shortcut for the Hive Battery app in the user's Start Menu.

@echo off
if exist "%HOMEPATH%\AppData\Local\Hive Battery" rd /s /q "%HOMEPATH%\AppData\Local\Hive Battery"
mkdir "%HOMEPATH%\AppData\Local\Hive Battery"
xcopy /y * "%HOMEPATH%\AppData\Local\Hive Battery"
del "%HOMEPATH%\AppData\Local\Hive Battery\install.cmd"

echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%HOMEPATH%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Hive Battery.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%HOMEPATH%\AppData\Local\Hive Battery\Hive Battery.exe" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs
cscript CreateShortcut.vbs
del CreateShortcut.vbs
