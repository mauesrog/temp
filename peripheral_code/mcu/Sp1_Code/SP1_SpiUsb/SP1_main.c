//###########################################################################
// FILE:   SP1_SpiUsb_main.c
// TITLE:  SP1 Prototype (F28377)
// DESCRIPTION: SPI/USB Communication portion of SP1 code

//INCLUDE HEADER FILES

	// General Includes
	#include "F2837xS_device.h"
	#include "F2837xS_Examples.h"
	#include "F28x_Project.h"     // Device Headerfile and Examples Include File
    #include <stdio.h>
    #include <stdint.h>
    #include <stdlib.h>
    #include <string.h>
    #include "MAX3420E_BF1.h"       // MAX3420E registers (rREGNAME), bits (bmBITNAME), and some handy macros
    #include "EnumApp_enum_data.h"  // HID keyboard enumeration data
    #include "usbapi/usbapi.h"
    #include <time.h>



// TEMP
Uint16 cmd_startEIS;
Uint32 cmd_frequencies; //24bits
Uint16 cmd_amplitude; //16bits
Uint16 cmd_currentranging; //2 bits
Uint16 cmd_samples;
Uint16 cmd_periods;
float EISData_Cal_V[MAXDATA];
float EISData_Cal_I[MAXDATA];
float VBatt_volts;

	typedef unsigned char BYTE;     // these save typing
	typedef unsigned short WORD;

#define TWENTY_MSEC 14200           // adjust this constant for 20 msec button checks
#define BOARD 1 // BOARD 0 - dev board, BOARD 1 - sp1

//
#define ENABLE_IRQS wreg(rEPIEN,(bmSUDAVIE+bmIN3BAVIE)); wreg(rUSBIEN,(bmURESIE+bmURESDNIE));
// Note: the SUSPEND IRQ will be enabled later, when the device is configured.
// This prevents repeated SUSPEND IRQ's

	//USB and SPI
	BYTE SUD[8];		// Local copy of the 8 setup data read from the MAX3420E SUDFIFO
	BYTE EP1OUT[64];        // Local copy of the 8 setup data read from the MAX3420E EP1OUTFIFO
	BYTE msgidx,msglen;	// Text string in EnumApp_enum_data.h--index and length
	BYTE configval;		// Set/Get_Configuration value
	BYTE ep3stall;		// Flag for EP3 Stall, set by Set_Feature, reported back in Get_Status
	BYTE interfacenum;      // Set/Get interface value
	BYTE inhibit_send = 0x01;	// Flag for the keyboard character send routine
	BYTE inhibit_read;  // Flag for the keyboard character send routine
	BYTE RWU_enabled;       // Set by Set/Clear_Feature RWU request, sent back for Get_Status-RWU
	BYTE Suspended;         // Tells the main loop to look for host resume and RWU pushbutton
	WORD msec_timer;        // Count off time in the main loop

	BYTE send3zeros;        // EP3-IN function uses this to send HID (key up) codes between keystrokes
	uint16_t pushbutton_type = 0;	//set to 1 to type
	uint16_t pushbutton_rwu = 0;	//set to 1 to remote wake up

	BYTE fatal_error = 0;
	BYTE status = 0;
	USB_INT pos = 0;
	int current_frequency = 0;
	BYTE waiting_for_data = 0x0;
	BYTE n_freqs = 0;

	usbapi_handle_t usb_handle = { &cmd_startEIS, &cmd_frequencies, &cmd_amplitude,
	                               &cmd_currentranging, &cmd_samples, &cmd_periods,
	                               &VBatt_volts, &fatal_error, &status,
																 &EISData_Cal_V, &EISData_Cal_I, &pos,
																 &current_frequency, &n_freqs,
	                               &waiting_for_data };

void spi_gpio_init(void);
void spi_fifo_init(void);
void error();

void read_csv(void);


// function prototypes (MAXIM)
//void SPI_Init(void);            // Configure MAXQ2000 and MAX3420E IO pins for SPI
void Reset_MAX(void);           // Reset the MAX3420E
BYTE MAX_Int_Pending(void);     // Poll the MAX3420E INT pin (set for active low level)
void test_SPI(void);
BYTE test=0;
BYTE gpio58 = 0;
int debug_usb_int_count = 0;

// USB functions
void std_request(void);
void class_request(void);
void vendor_request(void);
void send_descriptor(void);
void send_keystroke(BYTE);
void feature(BYTE);
void get_status(void);
void set_interface(void);
void get_interface(void);
void set_configuration(void);
void get_configuration(void);


// Application code
void do_SETUP(void);      // Handle a USB SETUP transfer
void USBsend(void); 	//written by MB
void check_for_resume(void);
void service_irqs(void);
void initialize_MAX(void);
void print_r(BYTE r);


interrupt void spiTxFifoIsr(void);
interrupt void spiRxFifoIsr(void);


#define WAITSTEP               asm(" RPT #255 || NOP")


FILE *log;

// Start of main
void main(void)
   {
// Initialize System Control: PLL, WatchDog, enable Peripheral Clocks
// This example function is found in the F2837xS_SysCtrl.c file.
      InitSysCtrl();

//  Initialize GPIO:
   // This example function is found in the F2837xS_Gpio.c file and
   // illustrates how to set the GPIO to it's default state.
   // Setup only the GP I/O only for SPI-A functionality
	  InitSpiaGpio();

// Initialize and Set Up GPIOs
    InitGpio();

// Disable CPU interrupts and clear all CPU interrupt flags:
    DINT;
    IER = 0x0000;
    IFR = 0x0000;

    // Initialize the PIE control registers to their default state. The default state is all PIE interrupts disabled and flags are cleared
    // This function is found in the F2837xS_PieCtrl.c file.
	InitPieCtrl();


// Initialize the PIE vector table with pointers to the shell Interrupt Service Routines (ISR). This will populate the entire table, even if the interrupt
// is not used in this example.  This is useful for debug purposes. The shell ISR routines are found in F2837xS_DefaultIsr.c.
// This function is found in F2837xS_PieVect.c.
    InitPieVectTable();

// Map interrupt functions
	EALLOW;
	PieVectTable.SPIA_RX_INT = &spiRxFifoIsr;			//SPI receive
	PieVectTable.SPIA_TX_INT = &spiTxFifoIsr;			//SPI transmit
	EDIS;

	InitCpuTimers();

// Enable Interrupts
 	PieCtrlRegs.PIECTRL.bit.ENPIE = 1;     // Enable the PIE block
 	PieCtrlRegs.PIEIER6.bit.INTx1 = 1;     // Enable PIE Group 6, INT 1
 	PieCtrlRegs.PIEIER6.bit.INTx2 = 1;     // Enable PIE Group 6, INT 2
    IER |= M_INT6;

    EINT;  // Enable Global interrupt INTM
    ERTM;  // Enable Global realtime interrupt DBGM

	initialize_MAX();

	// printf("\nInitial:\n");
	// print_r(rEPIRQ);
	//read_csv((0x1 << 6) * 4);
	/*
	BYTE bytes[64], bytes_written, pos1 = 0;
	matrix_encode(current, &bytes, &bytes_written, pos1);
	usbapi_write_eis_data(usb_handle);
	*/

	//MAIN LOOP
    for(;;) {
	  if(Suspended)
		check_for_resume();

	  if (MAX_Int_Pending()){	//	don't rely on interr
		service_irqs();
	    debug_usb_int_count++;
	  }
	  msec_timer++;
	  if(msec_timer==TWENTY_MSEC) {
		msec_timer=0;
	 //   if((rreg(rGPIO) & 0x10) == 0) // Check the pushbutton on GPI-0
		if (pushbutton_type > 0) {
			delay_loop();
			if (pushbutton_type == 2) {
			    inhibit_send = 0x02;
			} else {
			    inhibit_send = 0x00;
			}
			L0_ON                     // Turn on the SEND light
			pushbutton_type = 0;
		}
	  }
    }
}

void print_r(BYTE r) {
    BYTE j, nbytes = rreg(r);
    int i;

    printf("0x%02X: 0x%02X\n", r, nbytes);

    switch(r) {
        case rEPIRQ: ;
            printf("IN0BAVIRQ: 0x%02X\n", nbytes & bmIN0BAVIRQ);
            printf("OUT0DAVIRQ: 0x%02X\n", nbytes & bmOUT0DAVIRQ);
            break;
        case rEP1OUTBC: ;
            for(i = 0; i < nbytes; i++) {
                j = rreg(rEP1OUTFIFO);
                printf("0x%02X ", j);
            }
            break;
        default: ;
    }
}

void initialize_MAX(void)
{
ep3stall=0;			// EP3 inintially un-halted (no stall) (CH9 testing)
inhibit_send = 0x01;		// 0 means send, 1 means inhibit sending
send3zeros=1;
msec_timer=0;

// software flags
configval=0;                    // at pwr on OR bus reset we're unconfigured
Suspended=0;
RWU_enabled=0;                  // Set by host Set_Feature(enable RWU) request
//
//SPI_Init();                     // set up MAXQ2000 to use its SPI port as a master

		spi_fifo_init();   // Initialize the SPI only
		spi_gpio_init();	  // Set up SPI GPIOs
//
// Al ways set the FDUPSPI bit in the PINCTL register FIRST if you are using the SPI port in
// full duplex mode. This configures the port properly for subsequent SPI accesses.
//
wreg(rPINCTL,(bmFDUPSPI+gpxSOF+bmPOSINT));	//got rid on int neg level because don't have a pull up resistor. set POSINT so that 0-1 transition for interrupt
test = rreg(rPINCTL);

Reset_MAX();

wreg(rGPIO,0x00);                   // lites off (Active HIGH)
// This is a self-powered design, so the host could turn off Vbus while we are powered.
// Therefore set the VBGATE bit to have the MAX3420E automatically disconnect the D+
// pullup resistor in the absense of Vbus. Note: the VBCOMP pin must be connected to Vbus
// or pulled high for this code to work--a low on VBCOMP will prevent USB connection.
wreg(rUSBCTL,(bmCONNECT+bmVBGATE)); // VBGATE=1 disconnects D+ pullup if host turns off VBUS

ENABLE_IRQS


wreg(rCPUCTL,bmIE);                 // Enable the INT pin
delay_loop();
}

//
// error - Function to halt debugger on error
//
void error(void)
{
    asm("     ESTOP0");  //Test failed!! Stop!
    for (;;);
}

//
//Set up GPIOs for SPI
//
void spi_gpio_init()
{
	GPIO_SetupPinMux(58, GPIO_MUX_CPU1, 15); //GPIO61 - MOSI
	GPIO_SetupPinOptions(58, GPIO_OUTPUT, 0);
	GPIO_WritePin(58,0);

	GPIO_SetupPinMux(60, GPIO_MUX_CPU1, 15); //GPIO60 - SCLK
	GPIO_SetupPinOptions(60, GPIO_OUTPUT, 0);
	GPIO_WritePin(60,0);

	GPIO_SetupPinMux(61, GPIO_MUX_CPU1, 15); //GPIO61 - CS
	GPIO_SetupPinOptions(61, GPIO_OUTPUT, 0);
	GPIO_WritePin(61,1);

    GPIO_SetupPinMux(57, GPIO_MUX_CPU1, 0); //GPIO57 -  SPI INT
    GPIO_SetupPinOptions(57, GPIO_INPUT, GPIO_ASYNC);

    GPIO_SetupPinMux(59, GPIO_MUX_CPU1, 15); //GPIO57 -  MISO
    GPIO_SetupPinOptions(59, GPIO_INPUT, GPIO_ASYNC);
}


//
// spi_fifo_init - Initialize SPI FIFO
//
void spi_fifo_init()
{
   //
   // Initialize SPI FIFO registers
   //
   SpiaRegs.SPICCR.bit.SPISWRESET = 0; // Reset SPI

   SpiaRegs.SPICCR.all = 0x000F;     //16-bit character, non-Loopback mode
   SpiaRegs.SPICTL.all = 0x0017;     //Interrupt enabled, Master/Slave
                                     //XMIT enabled
   SpiaRegs.SPISTS.all = 0x0000;
   SpiaRegs.SPIBRR.all = 0x007F; //0x0063;     // Baud rate  - MB (attempt to slow down to fix connectivity issues for SP1)
  // SpiaRegs.SPIFFTX.all = 0xC022;    // Enable FIFO's, set TX FIFO level to 4
  // SpiaRegs.SPIFFRX.all = 0x0022;    // Set RX FIFO level to 4
   SpiaRegs.SPIFFCT.all = 0x00;
  // SpiaRegs.SPIPRI.all = 0x0010;

   SpiaRegs.SPICCR.bit.SPISWRESET=1; // Enable SPI
 //  SpiaRegs.SPIFFTX.bit.TXFIFO=1;
   //SpiaRegs.SPIFFRX.bit.RXFIFORESET=1;
}


void service_irqs(void) {
    BYTE itest1,itest2;
    ENABLE_IRQS

    itest1 = rreg(rEPIRQ);            // Check the EPIRQ bits
    itest2 = rreg(rUSBIRQ);           // Check the USBIRQ bits

    if(debug_usb_int_count ==3) {
        test = 0;
    }

    if(itest1 & bmSUDAVIRQ) {
        wreg(rEPIRQ,bmSUDAVIRQ);     // clear the SUDAV IRQ
        do_SETUP();
    }

    if (itest2 & bmNOVBUSIRQ) {
        puts("getting something!");
    }

    if (itest1 & bmIN3BAVIRQ) {         // Was an EP3-IN packet just dispatched to the host?
        // USBsend();
    }                             // NOTE: don't clear the IN3BAVIRQ bit here--loading the EP3-IN byte
                                      // count register in the do_IN3() function does it.
    if ((configval != 0) && (itest2&bmSUSPIRQ)) {   // HOST suspended bus for 3 msec
        wreg(rUSBIRQ,(bmSUSPIRQ+bmBUSACTIRQ));  // clear the IRQ and bus activity IRQ
        L2_ON                         // turn on the SUSPEND light

        Suspended=1;                  // signal the main loop
    }

    if(rreg(rUSBIRQ)& bmURESIRQ) {
        L1_ON                         // turn the BUS RESET light on
        L2_OFF                        // Suspend light off (if on)
        wreg(rUSBIRQ,bmURESIRQ);      // clear the IRQ
    }

    if (rreg(rUSBIRQ) & bmURESDNIRQ) {
        L1_OFF                        // turn the BUS RESET light off
        wreg(rUSBIRQ,bmURESDNIRQ);    // clear the IRQ bit
        Suspended=0;                  // in case we were suspended

        ENABLE_IRQS                   // ...because a bus reset clears the IE bit
     }
}


void do_SETUP(void)
{
    readbytes(rSUDFIFO,8,SUD);          // got a SETUP packet. Read 8 SETUP bytes
    switch(SUD[bmRequestType]&0x60) {     // Parse the SETUP packet. For request type, look only at b6&b5
        case 0x00:	std_request();		break;
        case 0x20:	class_request();	break;  // just a stub in this program
        case 0x40:	vendor_request();	break;  // just a stub in this program
        default: STALL_EP0                       // unrecognized request type
    }
}


void check_for_resume(void)
{
  if(rreg(rUSBIRQ) & bmBUSACTIRQ)     // THE HOST RESUMED BUS TRAFFIC
      {
      L2_OFF
      Suspended=0;                    // no longer suspended
      status= USBAPI_sREADY;
      }
  else if(RWU_enabled)                // Only if the host enabled RWU
      {
   //   if((rreg(rGPIO)&0x40)==0)       // See if the Remote Wakeup button was pressed
	  if(pushbutton_rwu==1)
        {
        L2_OFF                        // turn off suspend light
        Suspended=0;                  // no longer suspended
        SETBIT(rUSBCTL,bmSIGRWU)      // signal RWU
        while ((rreg(rUSBIRQ)&bmRWUDNIRQ)==0) ;	// spin until RWU signaling done
        CLRBIT(rUSBCTL,bmSIGRWU)      // remove the RESUME signal
        wreg(rUSBIRQ,bmRWUDNIRQ);     // clear the IRQ
        delay_loop();
        pushbutton_rwu = 0;
       // while((rreg(rGPIO)&0x40)==0) ;  // hang until RWU button released
        while(pushbutton_rwu==1)
        wreg(rUSBIRQ,bmBUSACTIRQ);    // wait for bus traffic -- clear the BUS Active IRQ
        while((rreg(rUSBIRQ) & bmBUSACTIRQ)==0) ; // & hang here until it's set again...
        }
      }
}


//*******************
void std_request(void)
{
switch(SUD[bRequest])
	{
	case	SR_GET_DESCRIPTOR:	send_descriptor();    break;
	case	SR_SET_FEATURE:		feature(1);           break;
	case	SR_CLEAR_FEATURE:	feature(0);           break;
	case	SR_GET_STATUS:		get_status();         break;
	case	SR_SET_INTERFACE:	set_interface();      break;
	case	SR_GET_INTERFACE:	get_interface();      break;
	case	SR_GET_CONFIGURATION:   get_configuration();  break;
	case	SR_SET_CONFIGURATION:   set_configuration();  break;
	case	SR_SET_ADDRESS:         rregAS(rFNADDR);      break;  // discard return value
	default:  STALL_EP0
	}
}

//**************************
void set_configuration(void)
{
configval=SUD[wValueL];           // Store the config value
if(configval != 0)                // If we are configured,
  SETBIT(rUSBIEN,bmSUSPIE);       // start looking for SUSPEND interrupts
rregAS(rFNADDR);                  // dummy read to set the ACKSTAT bit
}

void get_configuration(void)
{
wreg(rEP0FIFO,configval);         // Send the config value
wregAS(rEP0BC,1);
}

//**********************
void set_interface(void)	// All we accept are Interface=0 and AlternateSetting=0, otherwise send STALL
{
BYTE dumval;
if((SUD[wValueL]==0)		// wValueL=Alternate Setting index
  &&(SUD[wIndexL]==0))		// wIndexL=Interface index
  	dumval=rregAS(rFNADDR);	// dummy read to set the ACKSTAT bit
else STALL_EP0
}

//**********************
void get_interface(void)	// Check for Interface=0, always report AlternateSetting=0
{
if(SUD[wIndexL]==0)		// wIndexL=Interface index
  {
  wreg(rEP0FIFO,0);		// AS=0
  wregAS(rEP0BC,1);		// send one byte, ACKSTAT
  }
else STALL_EP0
}

//*******************
void get_status(void)
{
BYTE testbyte;
testbyte=SUD[bmRequestType];
switch(testbyte)
	{
	case 0x80: 			// directed to DEVICE
		wreg(rEP0FIFO,(RWU_enabled+1));	// first byte is 000000rs where r=enabled for RWU and s=self-powered.
		wreg(rEP0FIFO,0x00);		// second byte is always 0
		wregAS(rEP0BC,2); 		// load byte count, arm the IN transfer, ACK the status stage of the CTL transfer
		break;
	case 0x81: 			// directed to INTERFACE
		wreg(rEP0FIFO,0x00);		// this one is easy--two zero bytes
		wreg(rEP0FIFO,0x00);
		wregAS(rEP0BC,2); 		// load byte count, arm the IN transfer, ACK the status stage of the CTL transfer
		break;
	case 0x82: 			// directed to ENDPOINT
		if(SUD[wIndexL]==0x83)		// We only reported ep3, so it's the only one the host can stall IN3=83
                  {
                  wreg(rEP0FIFO,ep3stall);	// first byte is 0000000h where h is the halt (stall) bit
                  wreg(rEP0FIFO,0x00);		// second byte is always 0
                  wregAS(rEP0BC,2); 		// load byte count, arm the IN transfer, ACK the status stage of the CTL transfer
                  break;
                  }
		else  STALL_EP0		// Host tried to stall an invalid endpoint (not 3)
	default:      STALL_EP0		// don't recognize the request
	}
}

// **********************************************************************************************
// FUNCTION: Set/Get_Feature. Call as feature(1) for Set_Feature or feature(0) for Clear_Feature.
// There are two set/clear feature requests:
//	To a DEVICE: 	Remote Wakeup (RWU).
//  	To an ENDPOINT:	Stall (EP3 only for this app)
//
void feature(BYTE sc)
{
BYTE mask;
  if((SUD[bmRequestType]==0x02)	// dir=h->p, recipient = ENDPOINT
  &&  (SUD[wValueL]==0x00)	// wValueL is feature selector, 00 is EP Halt
  &&  (SUD[wIndexL]==0x83))	// wIndexL is endpoint number IN3=83
      {
      mask=rreg(rEPSTALLS);   // read existing bits
      if(sc==1)               // set_feature
        {
        mask += bmSTLEP3IN;       // Halt EP3IN
        ep3stall=1;
        }
      else                        // clear_feature
        {
        mask &= ~bmSTLEP3IN;      // UnHalt EP3IN
        ep3stall=0;
        wreg(rCLRTOGS,bmCTGEP3IN);  // clear the EP3 data toggle
        }
      wreg(rEPSTALLS,(mask|bmACKSTAT)); // Don't use wregAS for this--directly writing the ACKSTAT bit
      }
  else if ((SUD[bmRequestType]==0x00)	// dir=h->p, recipient = DEVICE
           &&  (SUD[wValueL]==0x01))	// wValueL is feature selector, 01 is Device_Remote_Wakeup
            {
            RWU_enabled = sc<<1;	// =2 for set, =0 for clear feature. The shift puts it in the get_status bit position.
            rregAS(rFNADDR);		// dummy read to set ACKSTAT
            }
  else STALL_EP0
}

//************************
void send_descriptor(void)
{
WORD reqlen,sendlen,desclen;
BYTE *pDdata;					// pointer to ROM Descriptor data to send
//
// NOTE This function assumes all descriptors are 64 or fewer bytes and can be sent in a single packet
//
desclen = 0;					// check for zero as error condition (no case statements satisfied)
reqlen = SUD[wLengthL] + 256*SUD[wLengthH];	// 16-bit
	switch (SUD[wValueH])			// wValueH is descriptor type
	{
	case  GD_DEVICE:
              desclen = DD[0];	// descriptor length
              pDdata = DD;
              break;
	case  GD_CONFIGURATION:
              desclen = CD[2];	// Config descriptor includes interface, HID, report and ep descriptors
              pDdata = CD;
              break;
	case  GD_STRING:
              desclen = strDesc[SUD[wValueL]][0];   // wValueL=string index, array[0] is the length
              pDdata = strDesc[SUD[wValueL]];       // point to first array element
              break;
	case  GD_HID:
              desclen = CD[18];
              pDdata = &CD[18];
              break;
	case  GD_REPORT:
              desclen = CD[25];
              pDdata = RepD;
        break;
	}	// end switch on descriptor type
//
if (desclen!=0)                   // one of the case statements above filled in a value
	{
	sendlen = (reqlen <= desclen) ? reqlen : desclen; // send the smaller of requested and avaiable
        writebytes(rEP0FIFO,sendlen,pDdata);
        wregAS(rEP0BC,sendlen);   // load EP0BC to arm the EP0-IN transfer & ACKSTAT

	}
else STALL_EP0  // none of the descriptor types match
}

void class_request(void)
{
STALL_EP0
}

void vendor_request(void)
{
    switch(SUD[bRequest]) {
        case INITIATE_EIS: usbapi_start_EIS(usb_handle); break;
        case INITIATE_ABORT_EIS: usbapi_stop_EIS(usb_handle); break;
        case INITIATE_EIS_DATA_TRANSFER:
            pos = (SUD[wValueL] + SUD[wIndexL]) * 15;
            usbapi_write_eis_data(usb_handle);
            break;
        case UPDATE_EIS:
            if (fatal_error) {
                printf("%02X %02X\n", fatal_error, status);
                status = USBAPI_sERROR;
            }

            if (waiting_for_data && status == USBAPI_sBUSY) {
                waiting_for_data = 0x0;
                read_csv();
            }

            switch(status) {
                case USBAPI_sERROR: usbapi_send_eis_error(usb_handle); break;
                case USBAPI_sSIGN: usbapi_sign_eis(usb_handle); break;
                default: usbapi_send_eis_status_code(status);
            }

            break;
        case CLEAR_EIS_ERR: usbapi_send_eis_status_code(USBAPI_sREADY); break;
        default: STALL_EP0
    }
}

void read_csv(void)
{
		VBatt_volts = 4.5;
    USB_INT i, n = (0x1 << cmd_samples) * cmd_periods;

    srand(time(NULL));

    for (i = 0; i < n; i++) {
        EISData_Cal_I[i] = (float) rand() / (float) (RAND_MAX / 2.0) - 1.0;
        EISData_Cal_V[i] = (float) rand() / (float) (RAND_MAX / 2.0) - 1.0;
    }

    usbapi_notify_dav(usb_handle);

    /*
    int j;

    current = matrix_new(2, 47);

    for (j = 0; j < 47; j++) {
        matrix_set_entry(&current, 0, j, EISData_Cal_I[j]);
    }

    for (j = 0; j < 47; j++) {
        matrix_set_entry(&current, 1, j, EISData_Cal_V[j]);
    }
    */
}



// ******************** END of ENUMERATION CODE ********************
//
void Reset_MAX(void)
{
BYTE dum;
wreg(rUSBCTL,0x20);	// chip reset
wreg(rUSBCTL,0x00);	// remove the reset
    do                  // Chip reset stops the oscillator. Wait for it to stabilize.
    {
    dum=rreg(rUSBIRQ);
    dum &= bmOSCOKIRQ;
    }
    while (dum==0);
}



BYTE MAX_Int_Pending(void)
{
	//return (BYTE)((PI6&0x01)==0);
	//
	if (BOARD ==1){
		return (BYTE) (GPIO_ReadPin(57)==1);
	}
	else if (BOARD ==0){
		return (BYTE) (GPIO_ReadPin(58)==1);
	}
	else return 0;


}

/*void SPI_Init(void) --kept this for the comments of how SPI should be configured
{
// Set up the MAXQ2000 SPI port
  CKCN = 0x00;              // system clock divisor is 1
  SS_HI                     // SS# high
  PD5 |= 0x070;             // Set SPI pins (SCLK, MOSI, and SS#) as outputs
  PD5 &= ~0x088;            // Set SPI pins (MISO,GPX) as inputs
  PD6 &= ~0x01;             // Set P60 (INT) as input
  SPICK = 0x00;             // fastest SPI clock--div by 2
  SPICF = 0x00;             // mode(0,0), 8 bit data
  SPICN |= bmMSTM;          // Set SPI controller as master
  SPICN |= bmSPIEN;         // Enable the SPI controller
}*/


//
// spiTxFifoIsr - ISR for SPI transmit FIFO
//
interrupt void spiTxFifoIsr(void)
{
/*    Uint16 i;
    for(i=0;i<1;i++)
    {
       SpiaRegs.SPITXBUF=sdata[i];      // Send data
    }

    for(i=0;i<2;i++)                    // Increment data for next cycle
    {
       sdata[i] = sdata[i] + 1;
    }*/

    SpiaRegs.SPIFFTX.bit.TXFFINTCLR=1;  // Clear Interrupt flag
    PieCtrlRegs.PIEACK.all|=0x20;       // Issue PIE ACK
}


//
// spiRxFifoIsr - ISR for SPI receive FIFO
//
interrupt void spiRxFifoIsr(void)
{
   /* Uint16 i;

    for(i=0; i<1; i++)
    {
        rdata[i]=SpiaRegs.SPIRXBUF;     // Read data
    }

    for(i=0; i<2; i++)                  // Check received data
    {
        if(rdata[i] != rdata_point+i)
        {
 //           error();
        }
    }

    rdata_point++;
    SpiaRegs.SPIFFRX.bit.RXFFOVFCLR=1;  // Clear Overflow flag
    SpiaRegs.SPIFFRX.bit.RXFFINTCLR=1;  // Clear Interrupt flag
    PieCtrlRegs.PIEACK.all|=0x20;       // Issue PIE ack*/
}


// End of File
