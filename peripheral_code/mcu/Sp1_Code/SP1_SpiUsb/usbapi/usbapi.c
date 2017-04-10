/*
 * usbapi.c
 *

 */

#include "usbapi.h"
#include "stdio.h"
#include "stdlib.h"
#include "string.h"

#define IDENT(x) x
#define XSTR(x) #x
#define STR(x) XSTR(x)

#include STR(MAX_PATH)
#include STR(DEVICE_PATH)
#include STR(PROJECT_PATH)

union {
  float d;
  USB_INT bytes[sizeof(float)];
} convert_float_bytes;

void extract_bytes_float(float val, BYTE (*bytes)[], BYTE *n, BYTE offset);
USB_INT encode_bytes(usbapi_handle_t handle, USB_INT n, BYTE (*bytes)[64],
                        BYTE *bytes_written, USB_INT pos);
USB_INT index_to_code(USB_INT i, USB_INT j, USB_INT n);
void code_to_indices(USB_INT ec, USB_INT (*indices)[2], USB_INT n);

typedef union uint32_to_hex {
    uint32_t _long;
    BYTE hex[sizeof(uint32_t)];
} uint32_to_hex_t;

typedef union uint16_to_hex_t {
    uint16_t _int;
    BYTE hex[sizeof(uint16_t)];
} uint16_to_hex_t;

void delay_loop()   //was at i < 1000000 = 10mS?
{
    long i;
    for (i = 0; i < 1000; i++) {}       //changed from 1000 which works for dev board
}

void wreg(BYTE reg, BYTE dat)
{
    uint16_t combine;
    combine = dat + ((reg+2)<<8);
    SpiaRegs.SPITXBUF = combine;
    delay_loop();
}

// Write a MAX3410E register with the "ACK STATUS" bit set in the command byte
void wregAS(BYTE reg, BYTE dat)
{
    uint16_t combine;
    combine = dat + ((reg+3)<<8);
    SpiaRegs.SPITXBUF = combine;
    delay_loop();
}

// Read a register, return its value.
BYTE rreg(BYTE reg)
{
    uint16_t combine;
    uint16_t inter;
    BYTE  result;
    combine = 0x00 + ((reg)<<8);    //data is don't care, we're clocking in MISO bits
    SpiaRegs.SPITXBUF = combine;
    delay_loop();
    inter = SpiaRegs.SPIRXBUF;
    result = inter & 0xFF;
    return(result);
}

// Read a byte (as rreg), but also set the AckStat bit in the command byte.
BYTE rregAS(BYTE reg)
{
    uint16_t combine;
    BYTE inter, result;
    combine = 0x00 + ((reg+1)<<8);  //data is don't care, we're clocking in MISO bits
    SpiaRegs.SPITXBUF = combine;
    delay_loop();
    inter = SpiaRegs.SPIRXBUF;
    result = inter & 0xFF;
    return(result);
}

void readbytes(BYTE reg, BYTE N, BYTE *p)
{
    BYTE j;
    uint16_t combine;
    uint16_t inter;
    BYTE  result;
    for(j=0;j<N;j++)
    {
        combine = 0x00 + ((reg)<<8);    //data is don't care, we're clocking in MISO bits
        SpiaRegs.SPITXBUF = combine;
        delay_loop();
        inter = SpiaRegs.SPIRXBUF;
        result = inter & 0xFF;
        *p = result;
        p++;
    }
}
void writebytes(BYTE reg, BYTE N, BYTE *p)
{
    BYTE j,wd;
    uint16_t combine;
    for(j=0;j<N;j++)
    {
        wd= *p;
        combine =  wd + ((reg+2)<<8);
        SpiaRegs.SPITXBUF = combine;
        delay_loop();
        p++;
    }
}

void usbapi_send_eis_status_code(BYTE code)
{
    printf("Status = %02X\n", code);
    wreg(rEP0FIFO, code);
    wreg(rEP0FIFO, 0);
    wregAS(rEP0BC, 2);
}

void usbapi_send_eis_error(usbapi_handle_t handle)
{
    wreg(rEP0FIFO, USBAPI_sERROR);
    printf("actual error being sent: %02X\n", *(handle.fatal_error));
    wreg(rEP0FIFO, *(handle.fatal_error));
    wregAS(rEP0BC, 2);

    *(handle.fatal_error) = 0;
    *(handle.status) = USBAPI_sREADY;
}

void usbapi_sign_eis(usbapi_handle_t handle)
{
    printf("Sign with current range: %02X\n", *(handle.cmd_currentranging) & 0xFF);
    BYTE n_bytes = 0, batt_volt[4], i;

    extract_bytes_float(*(handle.cmd_battvolt), &batt_volt, &n_bytes, 0);

    if (n_bytes != 4) {
      *(handle.fatal_error) = USBAPI_ERR_USB_WRITE_BATT_VOLTAGE;
      *(handle.status) = USBAPI_sERROR;
      usbapi_send_eis_error(handle);
      return;
    }

    wreg(rEP0FIFO, *(handle.status));
    wreg(rEP0FIFO, *(handle.cmd_currentranging) & 0xFF);


    for (i = 0; i < n_bytes; i++) { wreg(rEP0FIFO, batt_volt[i]); }

    wregAS(rEP0BC, 2 + n_bytes);

    *(handle.status) = USBAPI_sREADY;
}

void usbapi_start_EIS(usbapi_handle_t handle)
{
    puts("Start eis");
    int i, j, k, n_bytes = rreg(rEP0BC);

    if (n_bytes != 7) {
        *(handle.fatal_error) = USBAPI_ERR_USB_WRONG_NUM_BYTES;
        rregAS(rFNADDR);
        wreg(rEPIRQ, bmOUT0DAVIRQ);
        return;
    }

    uint32_to_hex_t freqs_to_hex;
    uint16_to_hex_t others_to_hex;

    BYTE period_data[2], bytes_arr[7];
    Uint32 curr_byte, byte_val;

    for (i = 0; i < n_bytes - 1; i++) {
        bytes_arr[i] = rreg(rEP0FIFO);
    }

    for (j = 0; j < 2; j++) {
        period_data[j] = bytes_arr[5] & (0xF << (4 * (1 - j)));
    }

    *(handle.cmd_samples) = period_data[0] >> 4;
    *(handle.cmd_periods) = period_data[1];

    bytes_arr[6] = rregAS(rEP0FIFO);
    wreg(rEPIRQ, bmOUT0DAVIRQ);


   *(handle.cmd_frequencies) = 0;
   *(handle.cmd_amplitude) = 0;
   *(handle.n_freqs) = 0;

    for (i = 0; i < n_bytes; i++) {
        curr_byte = bytes_arr[i];

        if (i < 3) {
            *(handle.cmd_frequencies) += curr_byte << (8 * (2 - i));
        } else if (i < 5) {
            *(handle.cmd_amplitude) += curr_byte << (8 * (4 - i));
        } else if (i == 6) {
            *(handle.cmd_currentranging) = curr_byte;
        }
    }

    byte_val = *(handle.cmd_frequencies);

    while (byte_val) {
        *(handle.n_freqs) += byte_val & 0x1;
        byte_val >>= 1;
        printf("n_freqs = %i, byte_val = %lu\n", *(handle.n_freqs), byte_val);
    }

    freqs_to_hex._long = *(handle.cmd_frequencies);

    printf("Frequency: 0x");

    for (k = sizeof(uint32_t) - 1; k >= 0; k--) {
        printf("%02X", freqs_to_hex.hex[k]);
    }

    others_to_hex._int = *(handle.cmd_amplitude);

    printf("\nAmplitude: 0x");

    for (k = sizeof(uint16_t) - 1; k >= 0; k--) {
        printf("%02X", others_to_hex.hex[k]);
    }

    others_to_hex._int = *(handle.cmd_samples);

    printf("\nSamples: 0x");

    for (k = sizeof(uint16_t) - 1; k >= 0; k--) {
        printf("%02X", others_to_hex.hex[k]);
    }

    others_to_hex._int = *(handle.cmd_periods);

    printf("\nPeriods: 0x");

    for (k = sizeof(uint16_t) - 1; k >= 0; k--) {
        printf("%02X", others_to_hex.hex[k]);
    }

    others_to_hex._int = *(handle.cmd_currentranging);

    printf("\nCurrent ranging: 0x");

    for (k = sizeof(uint16_t) - 1; k >= 0; k--) {
        printf("%02X", others_to_hex.hex[k]);
    }

    *(handle.status) = USBAPI_sBUSY;
    *(handle.waiting_for_data) = 0x1;

    *(handle.cmd_startEIS) = 1;

}

void usbapi_notify_dav(usbapi_handle_t handle)
{
    *(handle.status) = USBAPI_sDAV;
}

void usbapi_write_eis_data(usbapi_handle_t handle) {
    BYTE all_freqs_done = 0x0, finished_set;

    if (rreg(rEP0BC) != 1) {
        *(handle.fatal_error) = USBAPI_ERR_USB_NO_FREQ_SPEC;
        rregAS(rFNADDR);
        wreg(rEPIRQ, bmOUT0DAVIRQ);
        return;
    }

    *(handle.current_frequency) = rreg(rEP0FIFO);
    *(handle.status) = USBAPI_sTRANS;

    printf("Freq: %i\n", *(handle.current_frequency));

    BYTE i, bytes_written, bytes[64];
    USB_INT pos = *(handle.pos), pos_int;

    USB_INT n = (0x1 << *(handle.cmd_samples)) * *(handle.cmd_periods);

    if ((pos_int = encode_bytes(handle, n, &bytes, &bytes_written, pos)) != -1) {
        finished_set = 0x0;
    } else {
        finished_set = 0x1;

        if (*(handle.current_frequency) + 1 >= *(handle.n_freqs)) {
            all_freqs_done = 0x1;
        }
    }

    for (i = 0; i < bytes_written; i++) { wreg(rEP3INFIFO, bytes[i]); }

    wreg(rEP3INBC, bytes_written);
    wregAS(rEPIRQ, bmOUT0DAVIRQ);

    if (finished_set) {
        printf("Current freq: %i n_freqs: %i\n", *(handle.current_frequency), *(handle.n_freqs));

        if (all_freqs_done) {
            puts("Finished with file.");

            *(handle.status) = USBAPI_sSIGN;
        } else {
            puts("Finished with set.");
            *(handle.status) = USBAPI_sBUSY;
            *(handle.waiting_for_data) = 0x1;
        }
    } else {
        printf("Stopped at %i\n", pos_int);
    }
}

void usbapi_stop_EIS(usbapi_handle_t handle) {
    rregAS(rFNADDR);
}

void extract_bytes_float(float val, BYTE (*bytes)[], BYTE *n, BYTE offset)
{
    BYTE l, bytes_temp[sizeof(float)], ef, cd, k;

    convert_float_bytes.d = val;
    memcpy(&bytes_temp, convert_float_bytes.bytes, sizeof(float));

    for (k = 0; k < sizeof(float); k++) {
      l = bytes_temp[k];

      ef = l & 0xff;
      cd = (l>>8) & 0xff;

      (*bytes)[offset + (*n)++] = ef;
      (*bytes)[offset + (*n)++] = cd;
    }
}

USB_INT encode_bytes(usbapi_handle_t handle, USB_INT n, BYTE (*bytes)[64],
                        BYTE *bytes_written, USB_INT pos) {
    USB_INT indices[2], res = -1, i, j;
    BYTE n_bytes = 0, first_bytes = 0;
    float (*array)[2048];

    printf("before: %i\n n: %i\n", pos, n);

    code_to_indices(pos, &indices, n);

    for (i = indices[0]; i < 2; i++) {
      for (j = indices[1]; j < n; j++) {
        if (n_bytes == 60) {
          res = index_to_code(i, j, n);
          break;
        }

        array = i == 0 ? handle.voltage_data : handle.current_data;
        extract_bytes_float((*array)[j], &(*bytes), &n_bytes, 4);

        if (j == n - 1) { indices[1] = 0; }
      }
      if (n_bytes >= 60) { break; }
    }

    printf("after: %i\n %i\n", res * 15, res);

    extract_bytes_float(res, &(*bytes), &first_bytes, 0);

    *bytes_written = n_bytes + 4;

    return res;
}

USB_INT index_to_code(USB_INT i, USB_INT j, USB_INT n) {
  return (i * n + j) / 15;
}

void code_to_indices(USB_INT ec, USB_INT (*indices)[2], USB_INT n) {
  (*indices)[1] = ec % n;
  (*indices)[0] = (ec - (*indices)[1]) / n;
  printf("i= %i j= %i\n", (*indices)[0], (*indices)[1]);
}
