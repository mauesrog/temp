CC = @gcc
PROG = usbapi
OBJS = usbapi.o
LIBS =
INSTALL_ROOT = /Users/maurirogel/Documents/Dartmouth/HiveBattery/new_version_peripheral/HeaderFiles/v200
MAX_PATH = ${INSTALL_ROOT}/F2837xS_headers/include/MAX3420E_BF1.h
DEVICE_PATH = ${INSTALL_ROOT}/F2837xS_headers/include/F2837xS_device.h
EXAMPLES_PATH = ${INSTALL_ROOT}/F2837xS_common/include/F2837xS_Examples.h
PROJECT_PATH = ${INSTALL_ROOT}/F2837xS_common/include/F28x_Project.h
CFLAGS = -Wall -pedantic -std=c11 -ggdb -DMAX_PATH=${MAX_PATH} -DDEVICE_PATH="${DEVICE_PATH}" -DPROJECT_PATH="${PROJECT_PATH}" -DEXAMPLES_PATH="${EXAMPLES_PATH}"

$(PROG): $(OBJS)
	$(CC) $(CFLAGS) $^ $(LIBS) -o $@

usbapi.o: usbapi.h  ${MAX_PATH} ${DEVICE_PATH} ${PROJECT_PATH}

clean:
	@rm -f *~
	@rm -f *.o
	@rm -rf $(PROG).dSYM
	@rm -f $(PROG)
