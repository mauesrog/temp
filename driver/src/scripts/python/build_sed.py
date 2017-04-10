"""SED File Creation.

Generates the SED file necessary to create the .EXE file that installs the software. It uses the template located
at 'scripts/sed/template.SED' to crate a custom package installer. Furthermore, this module fills in the blanks in the
template with the user's actual data.

"""
import re
import os

PWD = os.path.dirname(os.path.abspath(__file__))
src = re.sub(r"\\", r"/", os.path.abspath(os.path.join(PWD, '../..')))

f = open('src/scripts/sed/template.SED', 'rb')

sed_file = re.match(r"(?P<hardcode>(.*?\n?)*)\$.*\n(?P<user>(.*?\n?)*)\$.*", f.read()).groupdict()
f.close()

sed_user = re.sub(r"\%cd\%", src, sed_file['user'])

real_sed = re.sub(r"/", r"\\", sed_file['hardcode'] + sed_user)

f = open('src/scripts/sed/create-package.SED', 'wb')

f.write(real_sed)
