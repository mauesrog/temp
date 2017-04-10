/*
 * usbapi.h
 *
 *  Created on: 21 февр. 2017 г.
 *      Author: maurirogel
 */

#ifndef BYTE
typedef unsigned char BYTE;
#endif // BYTE

#include <stdint.h>

#ifndef Uint16
typedef uint16_t Uint16;
#endif // Uint16

#ifndef Uint32
typedef uint32_t Uint32;
#endif // Uint32

#ifndef USBAPI_USBAPI_H_
#define USBAPI_USBAPI_H_

#define MAXDATA 2048

typedef short int USB_INT;

#define USBAPI_ERR_USB_WRONG_NUM_BYTES 0x08
#define USBAPI_ERR_USB_READ_ERROR_CODE 0x09
#define USBAPI_ERR_USB_NO_FREQ_SPEC 0x0A
#define USBAPI_ERR_USB_WRITE_BATT_VOLTAGE 0x0B
#define USBAPI_ERR_USB_OTHER 0x0C

#define USBAPI_sREADY 0x00
#define USBAPI_sTRANS 0xA0
#define USBAPI_sSIGN 0xC0
#define USBAPI_sBUSY 0xB0
#define USBAPI_sDAV 0xD0
#define USBAPI_sERROR 0xE0

typedef struct usbapi_handle {
    Uint16 *cmd_startEIS;
    Uint32 *cmd_frequencies; //24bits
    Uint16 *cmd_amplitude; //16bits
    Uint16 *cmd_currentranging; //2 bits
    Uint16 *cmd_samples;
    Uint16 *cmd_periods;
    float *cmd_battvolt;
    BYTE *fatal_error;
    BYTE *status;
    float (*voltage_data)[MAXDATA];
    float (*current_data)[MAXDATA];
    USB_INT *pos;
    int *current_frequency;
    BYTE *n_freqs;
    BYTE *waiting_for_data;
} usbapi_handle_t;

void delay_loop(void);

void wreg(BYTE reg, BYTE dat);
void wregAS(BYTE reg, BYTE dat);
BYTE rreg(BYTE reg);
BYTE rregAS(BYTE reg);
void readbytes(BYTE reg, BYTE N, BYTE *p);
void writebytes(BYTE reg, BYTE N, BYTE *p);

void usbapi_start_EIS(usbapi_handle_t handle);
void usbapi_stop_EIS(usbapi_handle_t handle);
void usbapi_send_eis_status_code(BYTE code);
void usbapi_send_eis_error(usbapi_handle_t handle);
void usbapi_sign_eis(usbapi_handle_t handle);
void usbapi_notify_dav(usbapi_handle_t handle);
void usbapi_write_eis_data(usbapi_handle_t handle);


#endif /* USBAPI_USBAPI_H_ */
