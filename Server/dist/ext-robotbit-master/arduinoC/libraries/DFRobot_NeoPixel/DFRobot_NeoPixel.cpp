#include "DFRobot_NeoPixel.h"
#if defined(NRF52833)
#include "neopixel.h"
#endif

struct parameterInit_t
{
    uint8_t p;
    uint16_t n;
    uint8_t b;
    neoPixelType t;
} parameterInit;
// via Michael Vogt/neophob: empty constructor is used when strand length
// isn't known at compile-time; situations where program config might be
// read from internal flash memory or an SD card, or arrive via serial
// command.  If using this constructor, MUST follow up with updateType(),
// updateLength(), etc. to establish the strand type, length and pin number!
DFRobot_NeoPixel::DFRobot_NeoPixel() : begun(false), pixels(NULL), pixels1(NULL), endTime(0)
{
#if defined(NRF5) || defined(NRF52833)
    strip->leds = NULL;
    strip1->leds = NULL;
#endif
    pin = -1;
}

DFRobot_NeoPixel::~DFRobot_NeoPixel()
{
    if (pixels)
        free(pixels);
#if defined(NRF5) || defined(NRF52833)
    if (strip->leds)
    {
        free(strip->leds);
        strip->leds = NULL;
    }
    if (strip1->leds)
    {
        free(strip1->leds);
        strip1->leds = NULL;
    }
#endif
    if (pin >= 0)
        pinMode(pin, INPUT);
}

void DFRobot_NeoPixel::begin(uint8_t p, uint16_t n, uint8_t bright, neoPixelType t)
{
    if (pin != -1)
    {
        if (parameterInit.p == p && parameterInit.n == n && parameterInit.b == bright && parameterInit.t == t)
            return;
    }
    parameterInit.p = p;
    parameterInit.n = n;
    parameterInit.b = bright;
    parameterInit.t = t;
    brightness = bright;
#if defined(NRF5) || defined(NRF52833)
    if (strip->leds)
    {
        free(strip->leds);
        strip->leds = NULL;
    }
    if (strip1->leds)
    {
        free(strip1->leds);
        strip1->leds = NULL;
    }
    strip->leds = (color_t *)malloc(sizeof(color_t) * n);
    strip1->leds = (color_t *)malloc(sizeof(color_t) * n);
    strip->num_leds = n;
    strip1->num_leds = n;
    this->clear();
    updateType(t);
    updateLength(n);
    setPin(p);
#else
    updateType(t);
    updateLength(n);
    setPin(p);
    if (pin >= 0)
    {
        pinMode(pin, OUTPUT);
        digitalWrite(pin, LOW);
    }
#if defined(ESP32)
    show();
#endif
    begun = true;
#endif
}

void DFRobot_NeoPixel::updateLength(uint16_t n)
{
    if (pixels)
    {
        free(pixels);
        pixels = NULL;
    } // Free existing data (if any)
    if (pixels1)
    {
        free(pixels1);
        pixels1 = NULL;
    } // Free existing data (if any)

    // Allocate new data -- note: ALL PIXELS ARE CLEARED
    numBytes = n * ((wOffset == rOffset) ? 3 : 4);
    if ((pixels = (uint8_t *)malloc(numBytes)) && (pixels1 = (uint8_t *)malloc(numBytes)))
    {
        memset(pixels, 0, numBytes);
        memset(pixels1, 0, numBytes);
        numLEDs = n;
    }
    else
    {
        numLEDs = numBytes = 0;
    }
}

void DFRobot_NeoPixel::updateType(neoPixelType t)
{
    boolean oldThreeBytesPerPixel = (wOffset == rOffset); // false if RGBW

    wOffset = (t >> 6) & 0b11; // See notes in header file
    rOffset = (t >> 4) & 0b11; // regarding R/G/B/W offsets
    gOffset = (t >> 2) & 0b11;
    bOffset = t & 0b11;
#ifdef NEO_KHZ400
    is800KHz = (t < 256); // 400 KHz flag is 1<<8
#endif

    // If bytes-per-pixel has changed (and pixel data was previously
    // allocated), re-allocate to new size.  Will clear any data.
    if (pixels)
    {
        boolean newThreeBytesPerPixel = (wOffset == rOffset);
        if (newThreeBytesPerPixel != oldThreeBytesPerPixel)
            updateLength(numLEDs);
    }
}

#if defined(ESP8266)
// ESP8266 show() is external to enforce ICACHE_RAM_ATTR execution
extern "C" void ICACHE_RAM_ATTR espShow(
    uint8_t pin, uint8_t *pixels, uint32_t numBytes, uint8_t type);
#elif defined(ESP32)
extern "C" void espShow(
    uint8_t pin, uint8_t *pixels, uint32_t numBytes, uint8_t type);
#endif // ESP8266

void DFRobot_NeoPixel::show(void)
{

    if (!pixels)
        return;

    // Data latch = 50+ microsecond pause in the output stream.  Rather than
    // put a delay at the end of the function, the ending time is noted and
    // the function will simply hold off (if needed) on issuing the
    // subsequent round of data until the latch time has elapsed.  This
    // allows the mainline code to start generating the next frame of data
    // rather than stalling for the latch.
    while (!canShow())
        ;
        // endTime is a private member (rather than global var) so that mutliple
        // instances on different pins can be quickly issued in succession (each
        // instance doesn't delay the next).

        // In order to make this code runtime-configurable to work with any pin,
        // SBI/CBI instructions are eschewed in favor of full PORT writes via the
        // OUT or ST instructions.  It relies on two facts: that peripheral
        // functions (such as PWM) take precedence on output pins, so our PORT-
        // wide writes won't interfere, and that interrupts are globally disabled
        // while data is being issued to the LEDs, so no other code will be
        // accessing the PORT.  The code takes an initial 'snapshot' of the PORT
        // state, computes 'pin high' and 'pin low' values, and writes these back
        // to the PORT register as needed.

        //noInterrupts(); // Need 100% focus on instruction timing

#ifdef __AVR__
    // AVR MCUs -- ATmega & ATtiny (no XMEGA) ---------------------------------

    volatile uint16_t
        i = numBytes; // Loop counter
    volatile uint8_t
        *ptr = pixels, // Pointer to next byte
        b = *ptr++,    // Current byte value
        hi,            // PORT w/output bit set high
        lo;            // PORT w/output bit set low

    // Hand-tuned assembly code issues data to the LED drivers at a specific
    // rate.  There's separate code for different CPU speeds (8, 12, 16 MHz)
    // for both the WS2811 (400 KHz) and WS2812 (800 KHz) drivers.  The
    // datastream timing for the LED drivers allows a little wiggle room each
    // way (listed in the datasheets), so the conditions for compiling each
    // case are set up for a range of frequencies rather than just the exact
    // 8, 12 or 16 MHz values, permitting use with some close-but-not-spot-on
    // devices (e.g. 16.5 MHz DigiSpark).  The ranges were arrived at based
    // on the datasheet figures and have not been extensively tested outside
    // the canonical 8/12/16 MHz speeds; there's no guarantee these will work
    // close to the extremes (or possibly they could be pushed further).
    // Keep in mind only one CPU speed case actually gets compiled; the
    // resulting program isn't as massive as it might look from source here.

// 8 MHz(ish) AVR ---------------------------------------------------------
#if (F_CPU >= 7400000UL) && (F_CPU <= 9500000UL)

#ifdef NEO_KHZ400 // 800 KHz check needed only if 400 KHz support enabled
    if (is800KHz)
    {
#endif

        volatile uint8_t n1, n2 = 0; // First, next bits out

        // Squeezing an 800 KHz stream out of an 8 MHz chip requires code
        // specific to each PORT register.

        // 10 instruction clocks per bit: HHxxxxxLLL
        // OUT instructions:              ^ ^    ^   (T=0,2,7)

        // PORTD OUTPUT ----------------------------------------------------

#if defined(PORTD)
#if defined(PORTB) || defined(PORTC) || defined(PORTF)
        if (port == &PORTD)
        {
#endif // defined(PORTB/C/F)

            hi = PORTD | pinMask;
            lo = PORTD & ~pinMask;
            n1 = lo;
            if (b & 0x80)
                n1 = hi;

            // Dirty trick: RJMPs proceeding to the next instruction are used
            // to delay two clock cycles in one instruction word (rather than
            // using two NOPs).  This was necessary in order to squeeze the
            // loop down to exactly 64 words -- the maximum possible for a
            // relative branch.

            asm volatile(
                "headD:"
                "\n\t" // Clk  Pseudocode
                // Bit 7:
                "out  %[port] , %[hi]"
                "\n\t" // 1    PORT = hi
                "mov  %[n2]   , %[lo]"
                "\n\t" // 1    n2   = lo
                "out  %[port] , %[n1]"
                "\n\t" // 1    PORT = n1
                "rjmp .+0"
                "\n\t" // 2    nop nop
                "sbrc %[byte] , 6"
                "\n\t" // 1-2  if(b & 0x40)
                "mov %[n2]   , %[hi]"
                "\n\t" // 0-1   n2 = hi
                "out  %[port] , %[lo]"
                "\n\t" // 1    PORT = lo
                "rjmp .+0"
                "\n\t" // 2    nop nop
                // Bit 6:
                "out  %[port] , %[hi]"
                "\n\t" // 1    PORT = hi
                "mov  %[n1]   , %[lo]"
                "\n\t" // 1    n1   = lo
                "out  %[port] , %[n2]"
                "\n\t" // 1    PORT = n2
                "rjmp .+0"
                "\n\t" // 2    nop nop
                "sbrc %[byte] , 5"
                "\n\t" // 1-2  if(b & 0x20)
                "mov %[n1]   , %[hi]"
                "\n\t" // 0-1   n1 = hi
                "out  %[port] , %[lo]"
                "\n\t" // 1    PORT = lo
                "rjmp .+0"
                "\n\t" // 2    nop nop
                // Bit 5:
                "out  %[port] , %[hi]"
                "\n\t" // 1    PORT = hi
                "mov  %[n2]   , %[lo]"
                "\n\t" // 1    n2   = lo
                "out  %[port] , %[n1]"
                "\n\t" // 1    PORT = n1
                "rjmp .+0"
                "\n\t" // 2    nop nop
                "sbrc %[byte] , 4"
                "\n\t" // 1-2  if(b & 0x10)
                "mov %[n2]   , %[hi]"
                "\n\t" // 0-1   n2 = hi
                "out  %[port] , %[lo]"
                "\n\t" // 1    PORT = lo
                "rjmp .+0"
                "\n\t" // 2    nop nop
                // Bit 4:
                "out  %[port] , %[hi]"
                "\n\t" // 1    PORT = hi
                "mov  %[n1]   , %[lo]"
                "\n\t" // 1    n1   = lo
                "out  %[port] , %[n2]"
                "\n\t" // 1    PORT = n2
                "rjmp .+0"
                "\n\t" // 2    nop nop
                "sbrc %[byte] , 3"
                "\n\t" // 1-2  if(b & 0x08)
                "mov %[n1]   , %[hi]"
                "\n\t" // 0-1   n1 = hi
                "out  %[port] , %[lo]"
                "\n\t" // 1    PORT = lo
                "rjmp .+0"
                "\n\t" // 2    nop nop
                // Bit 3:
                "out  %[port] , %[hi]"
                "\n\t" // 1    PORT = hi
                "mov  %[n2]   , %[lo]"
                "\n\t" // 1    n2   = lo
                "out  %[port] , %[n1]"
                "\n\t" // 1    PORT = n1
                "rjmp .+0"
                "\n\t" // 2    nop nop
                "sbrc %[byte] , 2"
                "\n\t" // 1-2  if(b & 0x04)
                "mov %[n2]   , %[hi]"
                "\n\t" // 0-1   n2 = hi
                "out  %[port] , %[lo]"
                "\n\t" // 1    PORT = lo
                "rjmp .+0"
                "\n\t" // 2    nop nop
                // Bit 2:
                "out  %[port] , %[hi]"
                "\n\t" // 1    PORT = hi
                "mov  %[n1]   , %[lo]"
                "\n\t" // 1    n1   = lo
                "out  %[port] , %[n2]"
                "\n\t" // 1    PORT = n2
                "rjmp .+0"
                "\n\t" // 2    nop nop
                "sbrc %[byte] , 1"
                "\n\t" // 1-2  if(b & 0x02)
                "mov %[n1]   , %[hi]"
                "\n\t" // 0-1   n1 = hi
                "out  %[port] , %[lo]"
                "\n\t" // 1    PORT = lo
                "rjmp .+0"
                "\n\t" // 2    nop nop
                // Bit 1:
                "out  %[port] , %[hi]"
                "\n\t" // 1    PORT = hi
                "mov  %[n2]   , %[lo]"
                "\n\t" // 1    n2   = lo
                "out  %[port] , %[n1]"
                "\n\t" // 1    PORT = n1
                "rjmp .+0"
                "\n\t" // 2    nop nop
                "sbrc %[byte] , 0"
                "\n\t" // 1-2  if(b & 0x01)
                "mov %[n2]   , %[hi]"
                "\n\t" // 0-1   n2 = hi
                "out  %[port] , %[lo]"
                "\n\t" // 1    PORT = lo
                "sbiw %[count], 1"
                "\n\t" // 2    i-- (don't act on Z flag yet)
                // Bit 0:
                "out  %[port] , %[hi]"
                "\n\t" // 1    PORT = hi
                "mov  %[n1]   , %[lo]"
                "\n\t" // 1    n1   = lo
                "out  %[port] , %[n2]"
                "\n\t" // 1    PORT = n2
                "ld   %[byte] , %a[ptr]+"
                "\n\t" // 2    b = *ptr++
                "sbrc %[byte] , 7"
                "\n\t" // 1-2  if(b & 0x80)
                "mov %[n1]   , %[hi]"
                "\n\t" // 0-1   n1 = hi
                "out  %[port] , %[lo]"
                "\n\t" // 1    PORT = lo
                "brne headD"
                "\n" // 2    while(i) (Z flag set above)
                : [ byte ] "+r"(b),
                  [ n1 ] "+r"(n1),
                  [ n2 ] "+r"(n2),
                  [ count ] "+w"(i)
                : [ port ] "I"(_SFR_IO_ADDR(PORTD)),
                  [ ptr ] "e"(ptr),
                  [ hi ] "r"(hi),
                  [ lo ] "r"(lo));

#if defined(PORTB) || defined(PORTC) || defined(PORTF)
        }
        else // other PORT(s)
#endif       // defined(PORTB/C/F)
#endif       // defined(PORTD)

        // PORTB OUTPUT ----------------------------------------------------

#if defined(PORTB)
#if defined(PORTD) || defined(PORTC) || defined(PORTF)
            if (port == &PORTB)
        {
#endif // defined(PORTD/C/F)

            // Same as above, just switched to PORTB and stripped of comments.
            hi = PORTB | pinMask;
            lo = PORTB & ~pinMask;
            n1 = lo;
            if (b & 0x80)
                n1 = hi;

            asm volatile(
                "headB:"
                "\n\t"
                "out  %[port] , %[hi]"
                "\n\t"
                "mov  %[n2]   , %[lo]"
                "\n\t"
                "out  %[port] , %[n1]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "sbrc %[byte] , 6"
                "\n\t"
                "mov %[n2]   , %[hi]"
                "\n\t"
                "out  %[port] , %[lo]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "out  %[port] , %[hi]"
                "\n\t"
                "mov  %[n1]   , %[lo]"
                "\n\t"
                "out  %[port] , %[n2]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "sbrc %[byte] , 5"
                "\n\t"
                "mov %[n1]   , %[hi]"
                "\n\t"
                "out  %[port] , %[lo]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "out  %[port] , %[hi]"
                "\n\t"
                "mov  %[n2]   , %[lo]"
                "\n\t"
                "out  %[port] , %[n1]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "sbrc %[byte] , 4"
                "\n\t"
                "mov %[n2]   , %[hi]"
                "\n\t"
                "out  %[port] , %[lo]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "out  %[port] , %[hi]"
                "\n\t"
                "mov  %[n1]   , %[lo]"
                "\n\t"
                "out  %[port] , %[n2]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "sbrc %[byte] , 3"
                "\n\t"
                "mov %[n1]   , %[hi]"
                "\n\t"
                "out  %[port] , %[lo]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "out  %[port] , %[hi]"
                "\n\t"
                "mov  %[n2]   , %[lo]"
                "\n\t"
                "out  %[port] , %[n1]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "sbrc %[byte] , 2"
                "\n\t"
                "mov %[n2]   , %[hi]"
                "\n\t"
                "out  %[port] , %[lo]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "out  %[port] , %[hi]"
                "\n\t"
                "mov  %[n1]   , %[lo]"
                "\n\t"
                "out  %[port] , %[n2]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "sbrc %[byte] , 1"
                "\n\t"
                "mov %[n1]   , %[hi]"
                "\n\t"
                "out  %[port] , %[lo]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "out  %[port] , %[hi]"
                "\n\t"
                "mov  %[n2]   , %[lo]"
                "\n\t"
                "out  %[port] , %[n1]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "sbrc %[byte] , 0"
                "\n\t"
                "mov %[n2]   , %[hi]"
                "\n\t"
                "out  %[port] , %[lo]"
                "\n\t"
                "sbiw %[count], 1"
                "\n\t"
                "out  %[port] , %[hi]"
                "\n\t"
                "mov  %[n1]   , %[lo]"
                "\n\t"
                "out  %[port] , %[n2]"
                "\n\t"
                "ld   %[byte] , %a[ptr]+"
                "\n\t"
                "sbrc %[byte] , 7"
                "\n\t"
                "mov %[n1]   , %[hi]"
                "\n\t"
                "out  %[port] , %[lo]"
                "\n\t"
                "brne headB"
                "\n"
                : [ byte ] "+r"(b), [ n1 ] "+r"(n1), [ n2 ] "+r"(n2), [ count ] "+w"(i)
                : [ port ] "I"(_SFR_IO_ADDR(PORTB)), [ ptr ] "e"(ptr), [ hi ] "r"(hi),
                  [ lo ] "r"(lo));

#if defined(PORTD) || defined(PORTC) || defined(PORTF)
        }
#endif
#if defined(PORTC) || defined(PORTF)
        else
#endif // defined(PORTC/F)
#endif // defined(PORTB)

        // PORTC OUTPUT ----------------------------------------------------

#if defined(PORTC)
#if defined(PORTD) || defined(PORTB) || defined(PORTF)
            if (port == &PORTC)
        {
#endif // defined(PORTD/B/F)

            // Same as above, just switched to PORTC and stripped of comments.
            hi = PORTC | pinMask;
            lo = PORTC & ~pinMask;
            n1 = lo;
            if (b & 0x80)
                n1 = hi;

            asm volatile(
                "headC:"
                "\n\t"
                "out  %[port] , %[hi]"
                "\n\t"
                "mov  %[n2]   , %[lo]"
                "\n\t"
                "out  %[port] , %[n1]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "sbrc %[byte] , 6"
                "\n\t"
                "mov %[n2]   , %[hi]"
                "\n\t"
                "out  %[port] , %[lo]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "out  %[port] , %[hi]"
                "\n\t"
                "mov  %[n1]   , %[lo]"
                "\n\t"
                "out  %[port] , %[n2]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "sbrc %[byte] , 5"
                "\n\t"
                "mov %[n1]   , %[hi]"
                "\n\t"
                "out  %[port] , %[lo]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "out  %[port] , %[hi]"
                "\n\t"
                "mov  %[n2]   , %[lo]"
                "\n\t"
                "out  %[port] , %[n1]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "sbrc %[byte] , 4"
                "\n\t"
                "mov %[n2]   , %[hi]"
                "\n\t"
                "out  %[port] , %[lo]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "out  %[port] , %[hi]"
                "\n\t"
                "mov  %[n1]   , %[lo]"
                "\n\t"
                "out  %[port] , %[n2]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "sbrc %[byte] , 3"
                "\n\t"
                "mov %[n1]   , %[hi]"
                "\n\t"
                "out  %[port] , %[lo]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "out  %[port] , %[hi]"
                "\n\t"
                "mov  %[n2]   , %[lo]"
                "\n\t"
                "out  %[port] , %[n1]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "sbrc %[byte] , 2"
                "\n\t"
                "mov %[n2]   , %[hi]"
                "\n\t"
                "out  %[port] , %[lo]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "out  %[port] , %[hi]"
                "\n\t"
                "mov  %[n1]   , %[lo]"
                "\n\t"
                "out  %[port] , %[n2]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "sbrc %[byte] , 1"
                "\n\t"
                "mov %[n1]   , %[hi]"
                "\n\t"
                "out  %[port] , %[lo]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "out  %[port] , %[hi]"
                "\n\t"
                "mov  %[n2]   , %[lo]"
                "\n\t"
                "out  %[port] , %[n1]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "sbrc %[byte] , 0"
                "\n\t"
                "mov %[n2]   , %[hi]"
                "\n\t"
                "out  %[port] , %[lo]"
                "\n\t"
                "sbiw %[count], 1"
                "\n\t"
                "out  %[port] , %[hi]"
                "\n\t"
                "mov  %[n1]   , %[lo]"
                "\n\t"
                "out  %[port] , %[n2]"
                "\n\t"
                "ld   %[byte] , %a[ptr]+"
                "\n\t"
                "sbrc %[byte] , 7"
                "\n\t"
                "mov %[n1]   , %[hi]"
                "\n\t"
                "out  %[port] , %[lo]"
                "\n\t"
                "brne headC"
                "\n"
                : [ byte ] "+r"(b), [ n1 ] "+r"(n1), [ n2 ] "+r"(n2), [ count ] "+w"(i)
                : [ port ] "I"(_SFR_IO_ADDR(PORTC)), [ ptr ] "e"(ptr), [ hi ] "r"(hi),
                  [ lo ] "r"(lo));

#if defined(PORTD) || defined(PORTB) || defined(PORTF)
        }
#endif // defined(PORTD/B/F)
#if defined(PORTF)
        else
#endif
#endif // defined(PORTC)

        // PORTF OUTPUT ----------------------------------------------------

#if defined(PORTF)
#if defined(PORTD) || defined(PORTB) || defined(PORTC)
            if (port == &PORTF)
        {
#endif // defined(PORTD/B/C)

            hi = PORTF | pinMask;
            lo = PORTF & ~pinMask;
            n1 = lo;
            if (b & 0x80)
                n1 = hi;

            asm volatile(
                "headF:"
                "\n\t"
                "out  %[port] , %[hi]"
                "\n\t"
                "mov  %[n2]   , %[lo]"
                "\n\t"
                "out  %[port] , %[n1]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "sbrc %[byte] , 6"
                "\n\t"
                "mov %[n2]   , %[hi]"
                "\n\t"
                "out  %[port] , %[lo]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "out  %[port] , %[hi]"
                "\n\t"
                "mov  %[n1]   , %[lo]"
                "\n\t"
                "out  %[port] , %[n2]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "sbrc %[byte] , 5"
                "\n\t"
                "mov %[n1]   , %[hi]"
                "\n\t"
                "out  %[port] , %[lo]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "out  %[port] , %[hi]"
                "\n\t"
                "mov  %[n2]   , %[lo]"
                "\n\t"
                "out  %[port] , %[n1]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "sbrc %[byte] , 4"
                "\n\t"
                "mov %[n2]   , %[hi]"
                "\n\t"
                "out  %[port] , %[lo]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "out  %[port] , %[hi]"
                "\n\t"
                "mov  %[n1]   , %[lo]"
                "\n\t"
                "out  %[port] , %[n2]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "sbrc %[byte] , 3"
                "\n\t"
                "mov %[n1]   , %[hi]"
                "\n\t"
                "out  %[port] , %[lo]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "out  %[port] , %[hi]"
                "\n\t"
                "mov  %[n2]   , %[lo]"
                "\n\t"
                "out  %[port] , %[n1]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "sbrc %[byte] , 2"
                "\n\t"
                "mov %[n2]   , %[hi]"
                "\n\t"
                "out  %[port] , %[lo]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "out  %[port] , %[hi]"
                "\n\t"
                "mov  %[n1]   , %[lo]"
                "\n\t"
                "out  %[port] , %[n2]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "sbrc %[byte] , 1"
                "\n\t"
                "mov %[n1]   , %[hi]"
                "\n\t"
                "out  %[port] , %[lo]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "out  %[port] , %[hi]"
                "\n\t"
                "mov  %[n2]   , %[lo]"
                "\n\t"
                "out  %[port] , %[n1]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "sbrc %[byte] , 0"
                "\n\t"
                "mov %[n2]   , %[hi]"
                "\n\t"
                "out  %[port] , %[lo]"
                "\n\t"
                "sbiw %[count], 1"
                "\n\t"
                "out  %[port] , %[hi]"
                "\n\t"
                "mov  %[n1]   , %[lo]"
                "\n\t"
                "out  %[port] , %[n2]"
                "\n\t"
                "ld   %[byte] , %a[ptr]+"
                "\n\t"
                "sbrc %[byte] , 7"
                "\n\t"
                "mov %[n1]   , %[hi]"
                "\n\t"
                "out  %[port] , %[lo]"
                "\n\t"
                "brne headF"
                "\n"
                : [ byte ] "+r"(b), [ n1 ] "+r"(n1), [ n2 ] "+r"(n2), [ count ] "+w"(i)
                : [ port ] "I"(_SFR_IO_ADDR(PORTF)), [ ptr ] "e"(ptr), [ hi ] "r"(hi),
                  [ lo ] "r"(lo));

#if defined(PORTD) || defined(PORTB) || defined(PORTC)
        }
#endif // defined(PORTD/B/C)
#endif // defined(PORTF)

#ifdef NEO_KHZ400
    }
    else
    { // end 800 KHz, do 400 KHz

        // Timing is more relaxed; unrolling the inner loop for each bit is
        // not necessary.  Still using the peculiar RJMPs as 2X NOPs, not out
        // of need but just to trim the code size down a little.
        // This 400-KHz-datastream-on-8-MHz-CPU code is not quite identical
        // to the 800-on-16 code later -- the hi/lo timing between WS2811 and
        // WS2812 is not simply a 2:1 scale!

        // 20 inst. clocks per bit: HHHHxxxxxxLLLLLLLLLL
        // ST instructions:         ^   ^     ^          (T=0,4,10)

        volatile uint8_t next, bit;

        hi = *port | pinMask;
        lo = *port & ~pinMask;
        next = lo;
        bit = 8;

        asm volatile(
            "head20:"
            "\n\t" // Clk  Pseudocode    (T =  0)
            "st   %a[port], %[hi]"
            "\n\t" // 2    PORT = hi     (T =  2)
            "sbrc %[byte] , 7"
            "\n\t" // 1-2  if(b & 128)
            "mov  %[next], %[hi]"
            "\n\t" // 0-1   next = hi    (T =  4)
            "st   %a[port], %[next]"
            "\n\t" // 2    PORT = next   (T =  6)
            "mov  %[next] , %[lo]"
            "\n\t" // 1    next = lo     (T =  7)
            "dec  %[bit]"
            "\n\t" // 1    bit--         (T =  8)
            "breq nextbyte20"
            "\n\t" // 1-2  if(bit == 0)
            "rol  %[byte]"
            "\n\t" // 1    b <<= 1       (T = 10)
            "st   %a[port], %[lo]"
            "\n\t" // 2    PORT = lo     (T = 12)
            "rjmp .+0"
            "\n\t" // 2    nop nop       (T = 14)
            "rjmp .+0"
            "\n\t" // 2    nop nop       (T = 16)
            "rjmp .+0"
            "\n\t" // 2    nop nop       (T = 18)
            "rjmp head20"
            "\n\t" // 2    -> head20 (next bit out)
            "nextbyte20:"
            "\n\t" //                    (T = 10)
            "st   %a[port], %[lo]"
            "\n\t" // 2    PORT = lo     (T = 12)
            "nop"
            "\n\t" // 1    nop           (T = 13)
            "ldi  %[bit]  , 8"
            "\n\t" // 1    bit = 8       (T = 14)
            "ld   %[byte] , %a[ptr]+"
            "\n\t" // 2    b = *ptr++    (T = 16)
            "sbiw %[count], 1"
            "\n\t" // 2    i--           (T = 18)
            "brne head20"
            "\n" // 2    if(i != 0) -> (next byte)
            : [ port ] "+e"(port),
              [ byte ] "+r"(b),
              [ bit ] "+r"(bit),
              [ next ] "+r"(next),
              [ count ] "+w"(i)
            : [ hi ] "r"(hi),
              [ lo ] "r"(lo),
              [ ptr ] "e"(ptr));
    }
#endif // NEO_KHZ400

// 12 MHz(ish) AVR --------------------------------------------------------
#elif (F_CPU >= 11100000UL) && (F_CPU <= 14300000UL)

#ifdef NEO_KHZ400 // 800 KHz check needed only if 400 KHz support enabled
    if (is800KHz)
    {
#endif

        // In the 12 MHz case, an optimized 800 KHz datastream (no dead time
        // between bytes) requires a PORT-specific loop similar to the 8 MHz
        // code (but a little more relaxed in this case).

        // 15 instruction clocks per bit: HHHHxxxxxxLLLLL
        // OUT instructions:              ^   ^     ^     (T=0,4,10)

        volatile uint8_t next;

        // PORTD OUTPUT ----------------------------------------------------

#if defined(PORTD)
#if defined(PORTB) || defined(PORTC) || defined(PORTF)
        if (port == &PORTD)
        {
#endif // defined(PORTB/C/F)

            hi = PORTD | pinMask;
            lo = PORTD & ~pinMask;
            next = lo;
            if (b & 0x80)
                next = hi;

            // Don't "optimize" the OUT calls into the bitTime subroutine;
            // we're exploiting the RCALL and RET as 3- and 4-cycle NOPs!
            asm volatile(
                "headD:"
                "\n\t" //        (T =  0)
                "out   %[port], %[hi]"
                "\n\t" //        (T =  1)
                "rcall bitTimeD"
                "\n\t" // Bit 7  (T = 15)
                "out   %[port], %[hi]"
                "\n\t"
                "rcall bitTimeD"
                "\n\t" // Bit 6
                "out   %[port], %[hi]"
                "\n\t"
                "rcall bitTimeD"
                "\n\t" // Bit 5
                "out   %[port], %[hi]"
                "\n\t"
                "rcall bitTimeD"
                "\n\t" // Bit 4
                "out   %[port], %[hi]"
                "\n\t"
                "rcall bitTimeD"
                "\n\t" // Bit 3
                "out   %[port], %[hi]"
                "\n\t"
                "rcall bitTimeD"
                "\n\t" // Bit 2
                "out   %[port], %[hi]"
                "\n\t"
                "rcall bitTimeD"
                "\n\t" // Bit 1
                // Bit 0:
                "out  %[port] , %[hi]"
                "\n\t" // 1    PORT = hi    (T =  1)
                "rjmp .+0"
                "\n\t" // 2    nop nop      (T =  3)
                "ld   %[byte] , %a[ptr]+"
                "\n\t" // 2    b = *ptr++   (T =  5)
                "out  %[port] , %[next]"
                "\n\t" // 1    PORT = next  (T =  6)
                "mov  %[next] , %[lo]"
                "\n\t" // 1    next = lo    (T =  7)
                "sbrc %[byte] , 7"
                "\n\t" // 1-2  if(b & 0x80) (T =  8)
                "mov %[next] , %[hi]"
                "\n\t" // 0-1    next = hi  (T =  9)
                "nop"
                "\n\t" // 1                 (T = 10)
                "out  %[port] , %[lo]"
                "\n\t" // 1    PORT = lo    (T = 11)
                "sbiw %[count], 1"
                "\n\t" // 2    i--          (T = 13)
                "brne headD"
                "\n\t" // 2    if(i != 0) -> (next byte)
                "rjmp doneD"
                "\n\t"
                "bitTimeD:"
                "\n\t" //      nop nop nop     (T =  4)
                "out  %[port], %[next]"
                "\n\t" // 1    PORT = next     (T =  5)
                "mov  %[next], %[lo]"
                "\n\t" // 1    next = lo       (T =  6)
                "rol  %[byte]"
                "\n\t" // 1    b <<= 1         (T =  7)
                "sbrc %[byte], 7"
                "\n\t" // 1-2  if(b & 0x80)    (T =  8)
                "mov %[next], %[hi]"
                "\n\t" // 0-1   next = hi      (T =  9)
                "nop"
                "\n\t" // 1                    (T = 10)
                "out  %[port], %[lo]"
                "\n\t" // 1    PORT = lo       (T = 11)
                "ret"
                "\n\t" // 4    nop nop nop nop (T = 15)
                "doneD:"
                "\n"
                : [ byte ] "+r"(b),
                  [ next ] "+r"(next),
                  [ count ] "+w"(i)
                : [ port ] "I"(_SFR_IO_ADDR(PORTD)),
                  [ ptr ] "e"(ptr),
                  [ hi ] "r"(hi),
                  [ lo ] "r"(lo));

#if defined(PORTB) || defined(PORTC) || defined(PORTF)
        }
        else // other PORT(s)
#endif // defined(PORTB/C/F)
#endif // defined(PORTD)

        // PORTB OUTPUT ----------------------------------------------------

#if defined(PORTB)
#if defined(PORTD) || defined(PORTC) || defined(PORTF)
            if (port == &PORTB)
        {
#endif // defined(PORTD/C/F)

            hi = PORTB | pinMask;
            lo = PORTB & ~pinMask;
            next = lo;
            if (b & 0x80)
                next = hi;

            // Same as above, just set for PORTB & stripped of comments
            asm volatile(
                "headB:"
                "\n\t"
                "out   %[port], %[hi]"
                "\n\t"
                "rcall bitTimeB"
                "\n\t"
                "out   %[port], %[hi]"
                "\n\t"
                "rcall bitTimeB"
                "\n\t"
                "out   %[port], %[hi]"
                "\n\t"
                "rcall bitTimeB"
                "\n\t"
                "out   %[port], %[hi]"
                "\n\t"
                "rcall bitTimeB"
                "\n\t"
                "out   %[port], %[hi]"
                "\n\t"
                "rcall bitTimeB"
                "\n\t"
                "out   %[port], %[hi]"
                "\n\t"
                "rcall bitTimeB"
                "\n\t"
                "out   %[port], %[hi]"
                "\n\t"
                "rcall bitTimeB"
                "\n\t"
                "out  %[port] , %[hi]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "ld   %[byte] , %a[ptr]+"
                "\n\t"
                "out  %[port] , %[next]"
                "\n\t"
                "mov  %[next] , %[lo]"
                "\n\t"
                "sbrc %[byte] , 7"
                "\n\t"
                "mov %[next] , %[hi]"
                "\n\t"
                "nop"
                "\n\t"
                "out  %[port] , %[lo]"
                "\n\t"
                "sbiw %[count], 1"
                "\n\t"
                "brne headB"
                "\n\t"
                "rjmp doneB"
                "\n\t"
                "bitTimeB:"
                "\n\t"
                "out  %[port], %[next]"
                "\n\t"
                "mov  %[next], %[lo]"
                "\n\t"
                "rol  %[byte]"
                "\n\t"
                "sbrc %[byte], 7"
                "\n\t"
                "mov %[next], %[hi]"
                "\n\t"
                "nop"
                "\n\t"
                "out  %[port], %[lo]"
                "\n\t"
                "ret"
                "\n\t"
                "doneB:"
                "\n"
                : [ byte ] "+r"(b), [ next ] "+r"(next), [ count ] "+w"(i)
                : [ port ] "I"(_SFR_IO_ADDR(PORTB)), [ ptr ] "e"(ptr), [ hi ] "r"(hi),
                  [ lo ] "r"(lo));

#if defined(PORTD) || defined(PORTC) || defined(PORTF)
        }
#endif
#if defined(PORTC) || defined(PORTF)
        else
#endif // defined(PORTC/F)
#endif // defined(PORTB)

        // PORTC OUTPUT ----------------------------------------------------

#if defined(PORTC)
#if defined(PORTD) || defined(PORTB) || defined(PORTF)
            if (port == &PORTC)
        {
#endif // defined(PORTD/B/F)

            hi = PORTC | pinMask;
            lo = PORTC & ~pinMask;
            next = lo;
            if (b & 0x80)
                next = hi;

            // Same as above, just set for PORTC & stripped of comments
            asm volatile(
                "headC:"
                "\n\t"
                "out   %[port], %[hi]"
                "\n\t"
                "rcall bitTimeC"
                "\n\t"
                "out   %[port], %[hi]"
                "\n\t"
                "rcall bitTimeC"
                "\n\t"
                "out   %[port], %[hi]"
                "\n\t"
                "rcall bitTimeC"
                "\n\t"
                "out   %[port], %[hi]"
                "\n\t"
                "rcall bitTimeC"
                "\n\t"
                "out   %[port], %[hi]"
                "\n\t"
                "rcall bitTimeC"
                "\n\t"
                "out   %[port], %[hi]"
                "\n\t"
                "rcall bitTimeC"
                "\n\t"
                "out   %[port], %[hi]"
                "\n\t"
                "rcall bitTimeC"
                "\n\t"
                "out  %[port] , %[hi]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "ld   %[byte] , %a[ptr]+"
                "\n\t"
                "out  %[port] , %[next]"
                "\n\t"
                "mov  %[next] , %[lo]"
                "\n\t"
                "sbrc %[byte] , 7"
                "\n\t"
                "mov %[next] , %[hi]"
                "\n\t"
                "nop"
                "\n\t"
                "out  %[port] , %[lo]"
                "\n\t"
                "sbiw %[count], 1"
                "\n\t"
                "brne headC"
                "\n\t"
                "rjmp doneC"
                "\n\t"
                "bitTimeC:"
                "\n\t"
                "out  %[port], %[next]"
                "\n\t"
                "mov  %[next], %[lo]"
                "\n\t"
                "rol  %[byte]"
                "\n\t"
                "sbrc %[byte], 7"
                "\n\t"
                "mov %[next], %[hi]"
                "\n\t"
                "nop"
                "\n\t"
                "out  %[port], %[lo]"
                "\n\t"
                "ret"
                "\n\t"
                "doneC:"
                "\n"
                : [ byte ] "+r"(b), [ next ] "+r"(next), [ count ] "+w"(i)
                : [ port ] "I"(_SFR_IO_ADDR(PORTC)), [ ptr ] "e"(ptr), [ hi ] "r"(hi),
                  [ lo ] "r"(lo));

#if defined(PORTD) || defined(PORTB) || defined(PORTF)
        }
#endif // defined(PORTD/B/F)
#if defined(PORTF)
        else
#endif
#endif // defined(PORTC)

        // PORTF OUTPUT ----------------------------------------------------

#if defined(PORTF)
#if defined(PORTD) || defined(PORTB) || defined(PORTC)
            if (port == &PORTF)
        {
#endif // defined(PORTD/B/C)

            hi = PORTF | pinMask;
            lo = PORTF & ~pinMask;
            next = lo;
            if (b & 0x80)
                next = hi;

            // Same as above, just set for PORTF & stripped of comments
            asm volatile(
                "headF:"
                "\n\t"
                "out   %[port], %[hi]"
                "\n\t"
                "rcall bitTimeC"
                "\n\t"
                "out   %[port], %[hi]"
                "\n\t"
                "rcall bitTimeC"
                "\n\t"
                "out   %[port], %[hi]"
                "\n\t"
                "rcall bitTimeC"
                "\n\t"
                "out   %[port], %[hi]"
                "\n\t"
                "rcall bitTimeC"
                "\n\t"
                "out   %[port], %[hi]"
                "\n\t"
                "rcall bitTimeC"
                "\n\t"
                "out   %[port], %[hi]"
                "\n\t"
                "rcall bitTimeC"
                "\n\t"
                "out   %[port], %[hi]"
                "\n\t"
                "rcall bitTimeC"
                "\n\t"
                "out  %[port] , %[hi]"
                "\n\t"
                "rjmp .+0"
                "\n\t"
                "ld   %[byte] , %a[ptr]+"
                "\n\t"
                "out  %[port] , %[next]"
                "\n\t"
                "mov  %[next] , %[lo]"
                "\n\t"
                "sbrc %[byte] , 7"
                "\n\t"
                "mov %[next] , %[hi]"
                "\n\t"
                "nop"
                "\n\t"
                "out  %[port] , %[lo]"
                "\n\t"
                "sbiw %[count], 1"
                "\n\t"
                "brne headF"
                "\n\t"
                "rjmp doneC"
                "\n\t"
                "bitTimeC:"
                "\n\t"
                "out  %[port], %[next]"
                "\n\t"
                "mov  %[next], %[lo]"
                "\n\t"
                "rol  %[byte]"
                "\n\t"
                "sbrc %[byte], 7"
                "\n\t"
                "mov %[next], %[hi]"
                "\n\t"
                "nop"
                "\n\t"
                "out  %[port], %[lo]"
                "\n\t"
                "ret"
                "\n\t"
                "doneC:"
                "\n"
                : [ byte ] "+r"(b), [ next ] "+r"(next), [ count ] "+w"(i)
                : [ port ] "I"(_SFR_IO_ADDR(PORTF)), [ ptr ] "e"(ptr), [ hi ] "r"(hi),
                  [ lo ] "r"(lo));

#if defined(PORTD) || defined(PORTB) || defined(PORTC)
        }
#endif // defined(PORTD/B/C)
#endif // defined(PORTF)

#ifdef NEO_KHZ400
    }
    else
    { // 400 KHz

        // 30 instruction clocks per bit: HHHHHHxxxxxxxxxLLLLLLLLLLLLLLL
        // ST instructions:               ^     ^        ^    (T=0,6,15)

        volatile uint8_t next, bit;

        hi = *port | pinMask;
        lo = *port & ~pinMask;
        next = lo;
        bit = 8;

        asm volatile(
            "head30:"
            "\n\t" // Clk  Pseudocode    (T =  0)
            "st   %a[port], %[hi]"
            "\n\t" // 2    PORT = hi     (T =  2)
            "sbrc %[byte] , 7"
            "\n\t" // 1-2  if(b & 128)
            "mov  %[next], %[hi]"
            "\n\t" // 0-1   next = hi    (T =  4)
            "rjmp .+0"
            "\n\t" // 2    nop nop       (T =  6)
            "st   %a[port], %[next]"
            "\n\t" // 2    PORT = next   (T =  8)
            "rjmp .+0"
            "\n\t" // 2    nop nop       (T = 10)
            "rjmp .+0"
            "\n\t" // 2    nop nop       (T = 12)
            "rjmp .+0"
            "\n\t" // 2    nop nop       (T = 14)
            "nop"
            "\n\t" // 1    nop           (T = 15)
            "st   %a[port], %[lo]"
            "\n\t" // 2    PORT = lo     (T = 17)
            "rjmp .+0"
            "\n\t" // 2    nop nop       (T = 19)
            "dec  %[bit]"
            "\n\t" // 1    bit--         (T = 20)
            "breq nextbyte30"
            "\n\t" // 1-2  if(bit == 0)
            "rol  %[byte]"
            "\n\t" // 1    b <<= 1       (T = 22)
            "rjmp .+0"
            "\n\t" // 2    nop nop       (T = 24)
            "rjmp .+0"
            "\n\t" // 2    nop nop       (T = 26)
            "rjmp .+0"
            "\n\t" // 2    nop nop       (T = 28)
            "rjmp head30"
            "\n\t" // 2    -> head30 (next bit out)
            "nextbyte30:"
            "\n\t" //                    (T = 22)
            "nop"
            "\n\t" // 1    nop           (T = 23)
            "ldi  %[bit]  , 8"
            "\n\t" // 1    bit = 8       (T = 24)
            "ld   %[byte] , %a[ptr]+"
            "\n\t" // 2    b = *ptr++    (T = 26)
            "sbiw %[count], 1"
            "\n\t" // 2    i--           (T = 28)
            "brne head30"
            "\n" // 1-2  if(i != 0) -> (next byte)
            : [ port ] "+e"(port),
              [ byte ] "+r"(b),
              [ bit ] "+r"(bit),
              [ next ] "+r"(next),
              [ count ] "+w"(i)
            : [ hi ] "r"(hi),
              [ lo ] "r"(lo),
              [ ptr ] "e"(ptr));
    }
#endif // NEO_KHZ400

// 16 MHz(ish) AVR --------------------------------------------------------
#elif (F_CPU >= 15400000UL) && (F_CPU <= 19000000L)

#ifdef NEO_KHZ400 // 800 KHz check needed only if 400 KHz support enabled
    if (is800KHz)
    {
#endif

        // WS2811 and WS2812 have different hi/lo duty cycles; this is
        // similar but NOT an exact copy of the prior 400-on-8 code.

        // 20 inst. clocks per bit: HHHHHxxxxxxxxLLLLLLL
        // ST instructions:         ^   ^        ^       (T=0,5,13)

        volatile uint8_t next, bit;

        hi = *port | pinMask;
        lo = *port & ~pinMask;
        next = lo;
        bit = 8;
        //Serial.println("avr");
        noInterrupts();
        asm volatile(
            "head20:"
            "\n\t" // Clk  Pseudocode    (T =  0)
            "st   %a[port],  %[hi]"
            "\n\t" // 2    PORT = hi     (T =  2)
            "sbrc %[byte],  7"
            "\n\t" // 1-2  if(b & 128)
            "mov  %[next], %[hi]"
            "\n\t" // 0-1   next = hi    (T =  4)
            "dec  %[bit]"
            "\n\t" // 1    bit--         (T =  5)
            "st   %a[port],  %[next]"
            "\n\t" // 2    PORT = next   (T =  7)
            "mov  %[next] ,  %[lo]"
            "\n\t" // 1    next = lo     (T =  8)
            "breq nextbyte20"
            "\n\t" // 1-2  if(bit == 0) (from dec above)
            "rol  %[byte]"
            "\n\t" // 1    b <<= 1       (T = 10)
            "rjmp .+0"
            "\n\t" // 2    nop nop       (T = 12)
            "nop"
            "\n\t" // 1    nop           (T = 13)
            "st   %a[port],  %[lo]"
            "\n\t" // 2    PORT = lo     (T = 15)
            "nop"
            "\n\t" // 1    nop           (T = 16)
            "rjmp .+0"
            "\n\t" // 2    nop nop       (T = 18)
            "rjmp head20"
            "\n\t" // 2    -> head20 (next bit out)
            "nextbyte20:"
            "\n\t" //                    (T = 10)
            "ldi  %[bit]  ,  8"
            "\n\t" // 1    bit = 8       (T = 11)
            "ld   %[byte] ,  %a[ptr]+"
            "\n\t" // 2    b = *ptr++    (T = 13)
            "st   %a[port], %[lo]"
            "\n\t" // 2    PORT = lo     (T = 15)
            "nop"
            "\n\t" // 1    nop           (T = 16)
            "sbiw %[count], 1"
            "\n\t" // 2    i--           (T = 18)
            "brne head20"
            "\n" // 2    if(i != 0) -> (next byte)
            : [ port ] "+e"(port),
              [ byte ] "+r"(b),
              [ bit ] "+r"(bit),
              [ next ] "+r"(next),
              [ count ] "+w"(i)
            : [ ptr ] "e"(ptr),
              [ hi ] "r"(hi),
              [ lo ] "r"(lo));
        interrupts();
#ifdef NEO_KHZ400
    }
    else
    { // 400 KHz

        // The 400 KHz clock on 16 MHz MCU is the most 'relaxed' version.

        // 40 inst. clocks per bit: HHHHHHHHxxxxxxxxxxxxLLLLLLLLLLLLLLLLLLLL
        // ST instructions:         ^       ^           ^         (T=0,8,20)

        volatile uint8_t next, bit;

        hi = *port | pinMask;
        lo = *port & ~pinMask;
        next = lo;
        bit = 8;

        asm volatile(
            "head40:"
            "\n\t" // Clk  Pseudocode    (T =  0)
            "st   %a[port], %[hi]"
            "\n\t" // 2    PORT = hi     (T =  2)
            "sbrc %[byte] , 7"
            "\n\t" // 1-2  if(b & 128)
            "mov  %[next] , %[hi]"
            "\n\t" // 0-1   next = hi    (T =  4)
            "rjmp .+0"
            "\n\t" // 2    nop nop       (T =  6)
            "rjmp .+0"
            "\n\t" // 2    nop nop       (T =  8)
            "st   %a[port], %[next]"
            "\n\t" // 2    PORT = next   (T = 10)
            "rjmp .+0"
            "\n\t" // 2    nop nop       (T = 12)
            "rjmp .+0"
            "\n\t" // 2    nop nop       (T = 14)
            "rjmp .+0"
            "\n\t" // 2    nop nop       (T = 16)
            "rjmp .+0"
            "\n\t" // 2    nop nop       (T = 18)
            "rjmp .+0"
            "\n\t" // 2    nop nop       (T = 20)
            "st   %a[port], %[lo]"
            "\n\t" // 2    PORT = lo     (T = 22)
            "nop"
            "\n\t" // 1    nop           (T = 23)
            "mov  %[next] , %[lo]"
            "\n\t" // 1    next = lo     (T = 24)
            "dec  %[bit]"
            "\n\t" // 1    bit--         (T = 25)
            "breq nextbyte40"
            "\n\t" // 1-2  if(bit == 0)
            "rol  %[byte]"
            "\n\t" // 1    b <<= 1       (T = 27)
            "nop"
            "\n\t" // 1    nop           (T = 28)
            "rjmp .+0"
            "\n\t" // 2    nop nop       (T = 30)
            "rjmp .+0"
            "\n\t" // 2    nop nop       (T = 32)
            "rjmp .+0"
            "\n\t" // 2    nop nop       (T = 34)
            "rjmp .+0"
            "\n\t" // 2    nop nop       (T = 36)
            "rjmp .+0"
            "\n\t" // 2    nop nop       (T = 38)
            "rjmp head40"
            "\n\t" // 2    -> head40 (next bit out)
            "nextbyte40:"
            "\n\t" //                    (T = 27)
            "ldi  %[bit]  , 8"
            "\n\t" // 1    bit = 8       (T = 28)
            "ld   %[byte] , %a[ptr]+"
            "\n\t" // 2    b = *ptr++    (T = 30)
            "rjmp .+0"
            "\n\t" // 2    nop nop       (T = 32)
            "st   %a[port], %[lo]"
            "\n\t" // 2    PORT = lo     (T = 34)
            "rjmp .+0"
            "\n\t" // 2    nop nop       (T = 36)
            "sbiw %[count], 1"
            "\n\t" // 2    i--           (T = 38)
            "brne head40"
            "\n" // 1-2  if(i != 0) -> (next byte)
            : [ port ] "+e"(port),
              [ byte ] "+r"(b),
              [ bit ] "+r"(bit),
              [ next ] "+r"(next),
              [ count ] "+w"(i)
            : [ ptr ] "e"(ptr),
              [ hi ] "r"(hi),
              [ lo ] "r"(lo));
    }
#endif // NEO_KHZ400

#else
#error "CPU SPEED NOT SUPPORTED"
#endif // end F_CPU ifdefs on __AVR__

    // END AVR ----------------------------------------------------------------

#elif defined(__arm__)

        // ARM MCUs -- Teensy 3.0, 3.1, LC, Arduino Due ---------------------------

#if defined(__MK20DX128__) || defined(__MK20DX256__) // Teensy 3.0 & 3.1
#define CYCLES_800_T0H (F_CPU / 4000000)
#define CYCLES_800_T1H (F_CPU / 1250000)
#define CYCLES_800 (F_CPU / 800000)
#define CYCLES_400_T0H (F_CPU / 2000000)
#define CYCLES_400_T1H (F_CPU / 833333)
#define CYCLES_400 (F_CPU / 400000)

    uint8_t *p = pixels,
            *end = p + numBytes, pix, mask;
    volatile uint8_t *set = portSetRegister(pin),
                     *clr = portClearRegister(pin);
    uint32_t cyc;

    ARM_DEMCR |= ARM_DEMCR_TRCENA;
    ARM_DWT_CTRL |= ARM_DWT_CTRL_CYCCNTENA;

#ifdef NEO_KHZ400 // 800 KHz check needed only if 400 KHz support enabled
    if (is800KHz)
    {
#endif
        cyc = ARM_DWT_CYCCNT + CYCLES_800;
        while (p < end)
        {
            pix = *p++;
            for (mask = 0x80; mask; mask >>= 1)
            {
                while (ARM_DWT_CYCCNT - cyc < CYCLES_800)
                    ;
                cyc = ARM_DWT_CYCCNT;
                *set = 1;
                if (pix & mask)
                {
                    while (ARM_DWT_CYCCNT - cyc < CYCLES_800_T1H)
                        ;
                }
                else
                {
                    while (ARM_DWT_CYCCNT - cyc < CYCLES_800_T0H)
                        ;
                }
                *clr = 1;
            }
        }
        while (ARM_DWT_CYCCNT - cyc < CYCLES_800)
            ;
#ifdef NEO_KHZ400
    }
    else
    { // 400 kHz bitstream
        cyc = ARM_DWT_CYCCNT + CYCLES_400;
        while (p < end)
        {
            pix = *p++;
            for (mask = 0x80; mask; mask >>= 1)
            {
                while (ARM_DWT_CYCCNT - cyc < CYCLES_400)
                    ;
                cyc = ARM_DWT_CYCCNT;
                *set = 1;
                if (pix & mask)
                {
                    while (ARM_DWT_CYCCNT - cyc < CYCLES_400_T1H)
                        ;
                }
                else
                {
                    while (ARM_DWT_CYCCNT - cyc < CYCLES_400_T0H)
                        ;
                }
                *clr = 1;
            }
        }
        while (ARM_DWT_CYCCNT - cyc < CYCLES_400)
            ;
    }
#endif // NEO_KHZ400

#elif defined(__MKL26Z64__) // Teensy-LC

#if F_CPU == 48000000
    uint8_t *p = pixels,
            pix, count, dly,
            bitmask = digitalPinToBitMask(pin);
    volatile uint8_t *reg = portSetRegister(pin);
    uint32_t num = numBytes;
    asm volatile(
        "L%=_begin:"
        "\n\t"
        "ldrb	%[pix], [%[p], #0]"
        "\n\t"
        "lsl	%[pix], #24"
        "\n\t"
        "movs	%[count], #7"
        "\n\t"
        "L%=_loop:"
        "\n\t"
        "lsl	%[pix], #1"
        "\n\t"
        "bcs	L%=_loop_one"
        "\n\t"
        "L%=_loop_zero:"
        "strb	%[bitmask], [%[reg], #0]"
        "\n\t"
        "movs	%[dly], #4"
        "\n\t"
        "L%=_loop_delay_T0H:"
        "\n\t"
        "sub	%[dly], #1"
        "\n\t"
        "bne	L%=_loop_delay_T0H"
        "\n\t"
        "strb	%[bitmask], [%[reg], #4]"
        "\n\t"
        "movs	%[dly], #13"
        "\n\t"
        "L%=_loop_delay_T0L:"
        "\n\t"
        "sub	%[dly], #1"
        "\n\t"
        "bne	L%=_loop_delay_T0L"
        "\n\t"
        "b	L%=_next"
        "\n\t"
        "L%=_loop_one:"
        "strb	%[bitmask], [%[reg], #0]"
        "\n\t"
        "movs	%[dly], #13"
        "\n\t"
        "L%=_loop_delay_T1H:"
        "\n\t"
        "sub	%[dly], #1"
        "\n\t"
        "bne	L%=_loop_delay_T1H"
        "\n\t"
        "strb	%[bitmask], [%[reg], #4]"
        "\n\t"
        "movs	%[dly], #4"
        "\n\t"
        "L%=_loop_delay_T1L:"
        "\n\t"
        "sub	%[dly], #1"
        "\n\t"
        "bne	L%=_loop_delay_T1L"
        "\n\t"
        "nop"
        "\n\t"
        "L%=_next:"
        "\n\t"
        "sub	%[count], #1"
        "\n\t"
        "bne	L%=_loop"
        "\n\t"
        "lsl	%[pix], #1"
        "\n\t"
        "bcs	L%=_last_one"
        "\n\t"
        "L%=_last_zero:"
        "strb	%[bitmask], [%[reg], #0]"
        "\n\t"
        "movs	%[dly], #4"
        "\n\t"
        "L%=_last_delay_T0H:"
        "\n\t"
        "sub	%[dly], #1"
        "\n\t"
        "bne	L%=_last_delay_T0H"
        "\n\t"
        "strb	%[bitmask], [%[reg], #4]"
        "\n\t"
        "movs	%[dly], #10"
        "\n\t"
        "L%=_last_delay_T0L:"
        "\n\t"
        "sub	%[dly], #1"
        "\n\t"
        "bne	L%=_last_delay_T0L"
        "\n\t"
        "b	L%=_repeat"
        "\n\t"
        "L%=_last_one:"
        "strb	%[bitmask], [%[reg], #0]"
        "\n\t"
        "movs	%[dly], #13"
        "\n\t"
        "L%=_last_delay_T1H:"
        "\n\t"
        "sub	%[dly], #1"
        "\n\t"
        "bne	L%=_last_delay_T1H"
        "\n\t"
        "strb	%[bitmask], [%[reg], #4]"
        "\n\t"
        "movs	%[dly], #1"
        "\n\t"
        "L%=_last_delay_T1L:"
        "\n\t"
        "sub	%[dly], #1"
        "\n\t"
        "bne	L%=_last_delay_T1L"
        "\n\t"
        "nop"
        "\n\t"
        "L%=_repeat:"
        "\n\t"
        "add	%[p], #1"
        "\n\t"
        "sub	%[num], #1"
        "\n\t"
        "bne	L%=_begin"
        "\n\t"
        "L%=_done:"
        "\n\t"
        : [ p ] "+r"(p),
          [ pix ] "=&r"(pix),
          [ count ] "=&r"(count),
          [ dly ] "=&r"(dly),
          [ num ] "+r"(num)
        : [ bitmask ] "r"(bitmask),
          [ reg ] "r"(reg));
#else
#error "Sorry, only 48 MHz is supported, please set Tools > CPU Speed to 48 MHz"
#endif // F_CPU == 48000000

#elif defined(__SAMD21G18A__) || defined(__SAMD21J18A__) // Arduino Zero, SODAQ Autonomo and others

    // Tried this with a timer/counter, couldn't quite get adequate
    // resolution.  So yay, you get a load of goofball NOPs...

    uint8_t *ptr, *end, p, bitMask, portNum;
    uint32_t pinMask;

    portNum = g_APinDescription[pin].ulPort;
    pinMask = 1ul << g_APinDescription[pin].ulPin;
    ptr = pixels;
    end = ptr + numBytes;
    p = *ptr++;
    bitMask = 0x80;

    volatile uint32_t *set = &(PORT->Group[portNum].OUTSET.reg),
                      *clr = &(PORT->Group[portNum].OUTCLR.reg);

#ifdef NEO_KHZ400 // 800 KHz check needed only if 400 KHz support enabled
    if (is800KHz)
    {
#endif
        for (;;)
        {
            *set = pinMask;
            asm("nop; nop; nop; nop; nop; nop; nop; nop;");
            if (p & bitMask)
            {
                asm("nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop; nop; nop; nop;");
                *clr = pinMask;
            }
            else
            {
                *clr = pinMask;
                asm("nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop; nop; nop; nop;");
            }
            if (bitMask >>= 1)
            {
                asm("nop; nop; nop; nop; nop; nop; nop; nop; nop;");
            }
            else
            {
                if (ptr >= end)
                    break;
                p = *ptr++;
                bitMask = 0x80;
            }
        }
#ifdef NEO_KHZ400
    }
    else
    { // 400 KHz bitstream
        for (;;)
        {
            *set = pinMask;
            asm("nop; nop; nop; nop; nop; nop; nop; nop; nop; nop; nop;");
            if (p & bitMask)
            {
                asm("nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop; nop; nop;");
                *clr = pinMask;
            }
            else
            {
                *clr = pinMask;
                asm("nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop; nop; nop;");
            }
            asm("nop; nop; nop; nop; nop; nop; nop; nop;"
                "nop; nop; nop; nop; nop; nop; nop; nop;"
                "nop; nop; nop; nop; nop; nop; nop; nop;"
                "nop; nop; nop; nop; nop; nop; nop; nop;");
            if (bitMask >>= 1)
            {
                asm("nop; nop; nop; nop; nop; nop; nop;");
            }
            else
            {
                if (ptr >= end)
                    break;
                p = *ptr++;
                bitMask = 0x80;
            }
        }
    }
#endif

#elif defined(ARDUINO_STM32_FEATHER) // FEATHER WICED (120MHz)

    // Tried this with a timer/counter, couldn't quite get adequate
    // resolution.  So yay, you get a load of goofball NOPs...

    uint8_t *ptr, *end, p, bitMask;
    uint32_t pinMask;

    pinMask = BIT(PIN_MAP[pin].gpio_bit);
    ptr = pixels;
    end = ptr + numBytes;
    p = *ptr++;
    bitMask = 0x80;

    volatile uint16_t *set = &(PIN_MAP[pin].gpio_device->regs->BSRRL);
    volatile uint16_t *clr = &(PIN_MAP[pin].gpio_device->regs->BSRRH);

#ifdef NEO_KHZ400 // 800 KHz check needed only if 400 KHz support enabled
    if (is800KHz)
    {
#endif
        for (;;)
        {
            if (p & bitMask)
            { // ONE
                // High 800ns
                *set = pinMask;
                asm("nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop; nop; nop; nop; nop; nop;");
                // Low 450ns
                *clr = pinMask;
                asm("nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop; nop; nop; nop; nop; nop;");
            }
            else
            { // ZERO
                // High 400ns
                *set = pinMask;
                asm("nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop;");
                // Low 850ns
                *clr = pinMask;
                asm("nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop; nop; nop; nop; nop; nop; nop; nop;"
                    "nop; nop; nop; nop;");
            }
            if (bitMask >>= 1)
            {
                // Move on to the next pixel
                asm("nop;");
            }
            else
            {
                if (ptr >= end)
                    break;
                p = *ptr++;
                bitMask = 0x80;
            }
        }
#ifdef NEO_KHZ400
    }
    else
    { // 400 KHz bitstream
        // ToDo!
    }
#endif

#elif defined(NRF5) || defined(NRF52833)
    neopixel_obj_t self;
    self.num_pixels = strip->num_leds;
    self.pin_num = strip->pin_num;
    self.data = (uint8_t *)malloc(strip->num_leds * 3);
    uint32_t pin_mask = (1UL << self.pin_num);
    for (int i = 0; i < strip->num_leds; i++)
    {
        memcpy(self.data + i * 3, strip->leds[i].grb, 3);
    }
    LO(self.pin_num)
#if defined(NRF52833)
    neopixel_send_buffer(*getMicroBitPin(g_PinID[pin]), self.data, self.num_pixels * 3);
#elif defined(NRF5)
    sendNeopixelBuffer(pin_mask, self.data, self.num_pixels);
#endif
    free(self.data);
/*
	const uint8_t PIN =  strip->pin_num;
	NRF_GPIO->OUTCLR = (1UL << PIN);
	nrf_delay_us(50);
	uint32_t irq_state = __get_PRIMASK();
	__disable_irq();
			for (int i = 0; i < strip->num_leds; i++)
			{
				for (int j = 0; j < 3; j++)
				{
					if ((strip->leds[i].grb[j] & 128) > 0)	{NEOPIXEL_SEND_ONE}
					else	{NEOPIXEL_SEND_ZERO}
					
					if ((strip->leds[i].grb[j] & 64) > 0)	{NEOPIXEL_SEND_ONE}
					else	{NEOPIXEL_SEND_ZERO}
					
					if ((strip->leds[i].grb[j] & 32) > 0)	{NEOPIXEL_SEND_ONE}
					else	{NEOPIXEL_SEND_ZERO}
					
					if ((strip->leds[i].grb[j] & 16) > 0)	{NEOPIXEL_SEND_ONE}
					else	{NEOPIXEL_SEND_ZERO}
					
					if ((strip->leds[i].grb[j] & 8) > 0)	{NEOPIXEL_SEND_ONE}
					else	{NEOPIXEL_SEND_ZERO}
					
					if ((strip->leds[i].grb[j] & 4) > 0)	{NEOPIXEL_SEND_ONE}
					else	{NEOPIXEL_SEND_ZERO}
					
					if ((strip->leds[i].grb[j] & 2) > 0)	{NEOPIXEL_SEND_ONE}
					else	{NEOPIXEL_SEND_ZERO}
					
					if ((strip->leds[i].grb[j] & 1) > 0)	{NEOPIXEL_SEND_ONE}
					else	{NEOPIXEL_SEND_ZERO}
				}
			}
	__set_PRIMASK(irq_state);*/
#else // Other ARM architecture -- Presumed Arduino Due

#define SCALE VARIANT_MCK / 2UL / 1000000UL
#define INST (2UL * F_CPU / VARIANT_MCK)
#define TIME_800_0 ((int)(0.40 * SCALE + 0.5) - (5 * INST))
#define TIME_800_1 ((int)(0.80 * SCALE + 0.5) - (5 * INST))
#define PERIOD_800 ((int)(1.25 * SCALE + 0.5) - (5 * INST))
#define TIME_400_0 ((int)(0.50 * SCALE + 0.5) - (5 * INST))
#define TIME_400_1 ((int)(1.20 * SCALE + 0.5) - (5 * INST))
#define PERIOD_400 ((int)(2.50 * SCALE + 0.5) - (5 * INST))

    int pinMask, time0, time1, period, t;
    Pio *port;
    volatile WoReg *portSet, *portClear, *timeValue, *timeReset;
    uint8_t *p, *end, pix, mask;

    pmc_set_writeprotect(false);
    pmc_enable_periph_clk((uint32_t)TC3_IRQn);
    TC_Configure(TC1, 0,
                 TC_CMR_WAVE | TC_CMR_WAVSEL_UP | TC_CMR_TCCLKS_TIMER_CLOCK1);
    TC_Start(TC1, 0);

    pinMask = g_APinDescription[pin].ulPin;  // Don't 'optimize' these into
    port = g_APinDescription[pin].pPort;     // declarations above.  Want to
    portSet = &(port->PIO_SODR);             // burn a few cycles after
    portClear = &(port->PIO_CODR);           // starting timer to minimize
    timeValue = &(TC1->TC_CHANNEL[0].TC_CV); // the initial 'while'.
    timeReset = &(TC1->TC_CHANNEL[0].TC_CCR);
    p = pixels;
    end = p + numBytes;
    pix = *p++;
    mask = 0x80;

#ifdef NEO_KHZ400 // 800 KHz check needed only if 400 KHz support enabled
    if (is800KHz)
    {
#endif
        time0 = TIME_800_0;
        time1 = TIME_800_1;
        period = PERIOD_800;
#ifdef NEO_KHZ400
    }
    else
    { // 400 KHz bitstream
        time0 = TIME_400_0;
        time1 = TIME_400_1;
        period = PERIOD_400;
    }
#endif

    for (t = time0;; t = time0)
    {
        if (pix & mask)
            t = time1;
        while (*timeValue < period)
            ;
        *portSet = pinMask;
        *timeReset = TC_CCR_CLKEN | TC_CCR_SWTRG;
        while (*timeValue < t)
            ;
        *portClear = pinMask;
        if (!(mask >>= 1))
        { // This 'inside-out' loop logic utilizes
            if (p >= end)
                break; // idle time to minimize inter-byte delays.
            pix = *p++;
            mask = 0x80;
        }
    }
    while (*timeValue < period)
        ; // Wait for last bit
    TC_Stop(TC1, 0);

#endif // end Due

    // END ARM ----------------------------------------------------------------

#elif defined(ESP8266) || defined(ESP32)
#if defined(NEOPIXEL_RMT) && defined(ESP32)
    RmtChannel ch = Rmt.txInit(pin, 100, 1); // tick = 100ns
    //Rmt.setTick(ch, 100); // tick = 100ns
    rmt_item32_t *rmt_data = NULL;
    rmt_data = (rmt_item32_t *)realloc(rmt_data, sizeof(rmt_item32_t) * numBytes * 8);
    for (int i = 0; i < numBytes; i++)
    {
        uint8_t data = pixels[i];
        for (int j = 0; j < 8; j++)
        {
            if (data & 0x80)
            {
                rmt_data[i * 8 + j].duration0 = 8;
                rmt_data[i * 8 + j].level0 = 1;
                rmt_data[i * 8 + j].duration1 = 4;
                rmt_data[i * 8 + j].level1 = 0;
            }
            else
            {
                rmt_data[i * 8 + j].duration0 = 4;
                rmt_data[i * 8 + j].level0 = 1;
                rmt_data[i * 8 + j].duration1 = 8;
                rmt_data[i * 8 + j].level1 = 0;
            }
            data <<= 1;
        }
    }
    Rmt.writeAsync(ch, rmt_data, numBytes * 8);
    Rmt.txDeinit(ch);
    free(rmt_data);
#else
    espShow(pin, pixels, numBytes, is800KHz);
#endif
#elif defined(__ARDUINO_ARC__)

        // Arduino 101  -----------------------------------------------------------

#define NOPx7                \
    {                        \
        __builtin_arc_nop(); \
        __builtin_arc_nop(); \
        __builtin_arc_nop(); \
        __builtin_arc_nop(); \
        __builtin_arc_nop(); \
        __builtin_arc_nop(); \
        __builtin_arc_nop(); \
    }

    PinDescription *pindesc = &g_APinDescription[pin];
    register uint32_t loop = 8 * numBytes; // one loop to handle all bytes and all bits
    register uint8_t *p = pixels;
    register uint32_t currByte = (uint32_t)(*p);
    register uint32_t currBit = 0x80 & currByte;
    register uint32_t bitCounter = 0;
    register uint32_t first = 1;

    // The loop is unusual. Very first iteration puts all the way LOW to the wire -
    // constant LOW does not affect NEOPIXEL, so there is no visible effect displayed.
    // During that very first iteration CPU caches instructions in the loop.
    // Because of the caching process, "CPU slows down". NEOPIXEL pulse is very time sensitive
    // that's why we let the CPU cache first and we start regular pulse from 2nd iteration
    if (pindesc->ulGPIOType == SS_GPIO)
    {
        register uint32_t reg = pindesc->ulGPIOBase + SS_GPIO_SWPORTA_DR;
        uint32_t reg_val = __builtin_arc_lr((volatile uint32_t)reg);
        register uint32_t reg_bit_high = reg_val | (1 << pindesc->ulGPIOId);
        register uint32_t reg_bit_low = reg_val & ~(1 << pindesc->ulGPIOId);

        loop += 1; // include first, special iteration
        while (loop--)
        {
            if (!first)
            {
                currByte <<= 1;
                bitCounter++;
            }

            // 1 is >550ns high and >450ns low; 0 is 200..500ns high and >450ns low
            __builtin_arc_sr(first ? reg_bit_low : reg_bit_high, (volatile uint32_t)reg);
            if (currBit)
            { // ~400ns HIGH (740ns overall)
                NOPx7
                    NOPx7
            }
            // ~340ns HIGH
            NOPx7
            __builtin_arc_nop();

            // 820ns LOW; per spec, max allowed low here is 5000ns */
            __builtin_arc_sr(reg_bit_low, (volatile uint32_t)reg);
            NOPx7
                NOPx7

                if (bitCounter >= 8)
            {
                bitCounter = 0;
                currByte = (uint32_t)(*++p);
            }

            currBit = 0x80 & currByte;
            first = 0;
        }
    }
    else if (pindesc->ulGPIOType == SOC_GPIO)
    {
        register uint32_t reg = pindesc->ulGPIOBase + SOC_GPIO_SWPORTA_DR;
        uint32_t reg_val = MMIO_REG_VAL(reg);
        register uint32_t reg_bit_high = reg_val | (1 << pindesc->ulGPIOId);
        register uint32_t reg_bit_low = reg_val & ~(1 << pindesc->ulGPIOId);

        loop += 1; // include first, special iteration
        while (loop--)
        {
            if (!first)
            {
                currByte <<= 1;
                bitCounter++;
            }
            MMIO_REG_VAL(reg) = first ? reg_bit_low : reg_bit_high;
            if (currBit)
            { // ~430ns HIGH (740ns overall)
                NOPx7
                    NOPx7
                    __builtin_arc_nop();
            }
            // ~310ns HIGH
            NOPx7

                // 850ns LOW; per spec, max allowed low here is 5000ns */
                MMIO_REG_VAL(reg) = reg_bit_low;
            NOPx7
                NOPx7

                if (bitCounter >= 8)
            {
                bitCounter = 0;
                currByte = (uint32_t)(*++p);
            }

            currBit = 0x80 & currByte;
            first = 0;
        }
    }

#endif

    // END ARCHITECTURE SELECT ------------------------------------------------

    //  interrupts();
    endTime = micros(); // Save EOD time for latch on next call
}

// Set the output pin number
void DFRobot_NeoPixel::setPin(uint8_t p)
{
#if defined(NRF5) || defined(NRF52833)
    pin = p;
    strip->pin_num = g_ADigitalPinMap[p];
    PINMODE(strip->pin_num);
    LO(strip->pin_num);
    for (int i = 0; i < strip->num_leds; i++)
    {
        strip->leds[i].simple.g = 0;
        strip->leds[i].simple.r = 0;
        strip->leds[i].simple.b = 0;
    }
#else
    if (begun && (pin >= 0))
        pinMode(pin, INPUT);
    pin = p;
    if (begun)
    {
        pinMode(p, OUTPUT);
        digitalWrite(p, LOW);
    }
#ifdef __AVR__
    port = portOutputRegister(digitalPinToPort(p));
    pinMask = digitalPinToBitMask(p);
#endif
#endif
}

// Set pixel color from separate R,G,B components:
void DFRobot_NeoPixel::setPixelColor(
    uint16_t n, uint8_t r, uint8_t g, uint8_t b)
{

#if defined(NRF5) || defined(NRF52833)

    if (n < strip->num_leds)
    {
        strip1->leds[n].simple.r = ((uint8_t)(r));
        strip1->leds[n].simple.g = ((uint8_t)(g));
        strip1->leds[n].simple.b = ((uint8_t)(b));
        strip->leds[n].simple.r = (((uint8_t)(r)) * brightness) >> 8;
        strip->leds[n].simple.g = (((uint8_t)(g)) * brightness) >> 8;
        strip->leds[n].simple.b = (((uint8_t)(b)) * brightness) >> 8;
    }
    else
        return;

#else

    if (n < numLEDs)
    {

        uint8_t *p, *p1;
        if (wOffset == rOffset)
        {                         // Is an RGB-type strip
            p = &pixels[n * 3];   // 3 bytes per pixel
            p1 = &pixels1[n * 3]; // 3 bytes per pixel
        }
        else
        {                         // Is a WRGB-type strip
            p = &pixels[n * 4];   // 4 bytes per pixel
            p1 = &pixels1[n * 4]; // 4 bytes per pixel
            p[wOffset] = 0;       // But only R,G,B passed -- set W to 0
            p1[wOffset] = 0;      // But only R,G,B passed -- set W to 0
        }
        p1[rOffset] = r; // R,G,B always stored
        p1[gOffset] = g;
        p1[bOffset] = b;
        if (brightness)
        { // See notes in setBrightness()
            r = (r * brightness) >> 8;
            g = (g * brightness) >> 8;
            b = (b * brightness) >> 8;
        }
        p[rOffset] = r; // R,G,B always stored
        p[gOffset] = g;
        p[bOffset] = b;
    }
#endif
    show();
}

void DFRobot_NeoPixel::setPixelColor(
    uint16_t n, uint8_t r, uint8_t g, uint8_t b, uint8_t w)
{

    if (n < numLEDs)
    {
        if (brightness)
        { // See notes in setBrightness()
            r = (r * brightness) >> 8;
            g = (g * brightness) >> 8;
            b = (b * brightness) >> 8;
            w = (w * brightness) >> 8;
        }
        uint8_t *p;
        if (wOffset == rOffset)
        {                       // Is an RGB-type strip
            p = &pixels[n * 3]; // 3 bytes per pixel (ignore W)
        }
        else
        {                       // Is a WRGB-type strip
            p = &pixels[n * 4]; // 4 bytes per pixel
            p[wOffset] = w;     // Store W
        }
        p[rOffset] = r; // Store R,G,B
        p[gOffset] = g;
        p[bOffset] = b;
    }
    show();
}

void DFRobot_NeoPixel::rotate(int8_t offset)
{

    if (abs(offset) <= 0)
        return;
#if defined(NRF5) || defined(NRF52833)
    if (strip->num_leds <= 0)
        return;
    uint16_t steps = strip->num_leds;
#else
    if (numLEDs <= 0)
        return;
    uint16_t steps = numLEDs;
#endif
    // offset = offset % steps;
    if(offset > 0){
        offset = offset % steps;
    }else{
        offset = abs(offset) % steps;
        offset = -offset;
    }
    if (offset > 0)
    {
        uint32_t c[offset];
        for (int i = 0; i < offset; i++)
            c[i] = this->getPixelColor(steps - offset + i);
        for (int i = steps - 1; i >= offset; i--)
        {
            this->setPixelColor(i, this->getPixelColor(i - offset), false);
        }
        for (int i = 0; i < offset; i++)
        {
            this->setPixelColor(i, c[i], false);
        }
    }
    else
    {
        uint32_t c[abs(offset)];
        for (int i = 0; i < abs(offset); i++)
            c[i] = this->getPixelColor(i);
        for (int i = 0; i <= steps - abs(offset); i++)
        {
            this->setPixelColor(i, this->getPixelColor(i + abs(offset)), false);
        }
        for (int i = steps - abs(offset); i < steps; i++)
        {
            this->setPixelColor(i, c[i - steps + abs(offset)], false);
        }
    }

    show();
}

void DFRobot_NeoPixel::showBarGraph(uint16_t start, uint16_t end, int16_t value, int16_t high)
{
    if (end < start)
    {
        uint16_t num = end;
        end = start;
        start = num;
    }

#if defined(NRF5) || defined(NRF52833)
    if (strip->num_leds <= 0)
        return;
    start = max(start, 0);
    start = min(start, strip->num_leds);
    end = max(end, 0);
    end = min(end, strip->num_leds);
#else
    if (numLEDs <= 0)
        return;
    start = max(start, 0);
    start = min(start, numLEDs);
    end = max(end, 0);
    end = min(end, numLEDs);
#endif

    if (high <= 0)
    {
        this->clear();
        this->setPixelColor(0 + start, 0xffff00, false);
        this->show();
        return;
    }

    value = abs(value);
#if defined(NRF5) || defined(NRF52833)
    if (strip->num_leds <= 0)
        return;
    uint16_t n = end - start + 1;
#else
    if (numLEDs <= 0)
        return;
    uint16_t n = end - start + 1;
#endif
    uint16_t n1 = n - 1;
    int v = (value * n) / high;
    if (v == 0)
    {
        for (uint16_t i = 1; i < n; ++i)
            this->setPixelColor(i + start, 0, false);
    }
    else
    {
        for (uint16_t i = 0; i < n; ++i)
        {
            if (i < v)
            {
                uint32_t b = i * 255 / n1;
                this->setPixelColor(i + start, ((b & 0xFF) << 16) | ((0 & 0xFF) << 8) | ((255 - b) & 0xFF), false);
            }
            else
                this->setPixelColor(i + start, 0, false);
        }
    }
    this->show();
}

void DFRobot_NeoPixel::shift(int8_t offset)
{

    if (abs(offset) <= 0)
        return;
#if defined(NRF5) || defined(NRF52833)
    if (strip->num_leds <= 0)
        return;
    uint16_t steps = strip->num_leds;
#else
    if (numLEDs <= 0)
        return;
    uint16_t steps = numLEDs;
#endif

    if (abs(offset) > steps)
    {
        this->clear();
        return;
    }

    if (offset > 0)
    {
        for (int i = steps - 1; i >= offset; i--)
        {
            this->setPixelColor(i, this->getPixelColor(i - offset), false);
        }
        for (int i = 0; i < offset; i++)
        {
            this->setPixelColor(i, 0, false);
        }
    }
    else
    {
        for (int i = 0; i <= steps - abs(offset); i++)
        {
            this->setPixelColor(i, this->getPixelColor(i + abs(offset)), false);
        }
        for (int i = steps - abs(offset); i < steps; i++)
        {
            this->setPixelColor(i, 0, false);
        }
    }

    show();
}

void DFRobot_NeoPixel::showRainbow(uint16_t start, uint16_t end, uint32_t startHue, uint32_t endHue)
{

    if (end < start)
    {
        uint16_t num = end;
        end = start;
        start = num;
    }

#if defined(NRF5) || defined(NRF52833)
    if (strip->num_leds <= 0)
        return;
    start = max(start, 0);
    start = min(start, strip->num_leds);
    end = max(end, 0);
    end = min(end, strip->num_leds);
    uint16_t steps = end - start + 1;
#else
    if (numLEDs <= 0)
        return;
    start = max(start, 0);
    start = min(start, numLEDs);
    end = max(end, 0);
    end = min(end, numLEDs);
    uint16_t steps = end - start + 1;
#endif
    uint16_t saturation = 100;
    uint16_t luminance = 50;
    //uint16_t direction = HueInterpolationDirection.Clockwise;
    //hue
    uint16_t h1 = startHue;
    uint16_t h2 = endHue;
    uint16_t hDistCW = ((h2 + 360) - h1) % 360;
    uint16_t hStepCW = (hDistCW * 100) / steps;
    //uint16_t hDistCCW = ((h1 + 360) - h2) % 360;
    //uint16_t hStepCCW = -(hDistCCW * 100) / steps
    uint16_t hStep = hStepCW;
    uint16_t h1_100 = h1 * 100; //we multiply by 100 so we keep more accurate results while doing interpolation
    uint16_t s1 = saturation;
    uint16_t s2 = saturation;
    uint16_t sDist = s2 - s1;
    uint16_t sStep = sDist / steps;
    uint16_t s1_100 = s1 * 100;

    //lum
    uint16_t l1 = luminance;
    uint16_t l2 = luminance;
    uint16_t lDist = l2 - l1;
    uint16_t lStep = lDist / steps;
    uint16_t l1_100 = l1 * 100;

    //interpolate
    if (steps == 1)
    {
        this->setPixelColor(start, hsl(h1 + hStep, s1 + sStep, l1 + lStep), false);
    }
    else
    {
        this->setPixelColor(start, hsl(startHue, saturation, luminance), false);
        for (int i = start + 1; i < start + steps - 1; i++)
        {
            uint16_t h = (h1_100 + i * hStep) / 100 + 360;
            uint16_t s = (s1_100 + i * sStep) / 100;
            uint16_t l = (l1_100 + i * lStep) / 100;
            this->setPixelColor(i, hsl(h, s, l), false);
        }
        this->setPixelColor(start + steps - 1, hsl(endHue, saturation, luminance), false);
    }
    show();
}

uint32_t DFRobot_NeoPixel::hsl(uint32_t h, uint32_t s, uint32_t l)
{
    h = h % 360;
    s = max(s, 0);
    s = min(s, 99);
    l = max(l, 0);
    l = min(l, 99);
    uint32_t c = (((100 - abs(2 * l - 100)) * s) << 8) / 10000; //chroma, [0,255]
    uint8_t h1 = h / 60;                                        //[0,6]
    uint16_t h2 = (h - h1 * 60) * 256 / 60;                     //[0,255]
    uint32_t temp = abs(int32_t(((h1 % 2) << 8) + h2) - 256);
    uint32_t x = (c * (256 - (temp))) >> 8; //[0,255], second largest component of this color
    uint32_t _r, _g, _b;
    if (h1 == 0)
    {
        _r = c;
        _g = x;
        _b = 0;
    }
    else if (h1 == 1)
    {
        _r = x;
        _g = c;
        _b = 0;
    }
    else if (h1 == 2)
    {
        _r = 0;
        _g = c;
        _b = x;
    }
    else if (h1 == 3)
    {
        _r = 0;
        _g = x;
        _b = c;
    }
    else if (h1 == 4)
    {
        _r = x;
        _g = 0;
        _b = c;
    }
    else if (h1 == 5)
    {
        _r = c;
        _g = 0;
        _b = x;
    }
    uint32_t m = ((l * 2 << 8) / 100 - c) / 2;
    uint32_t r = _r + m;
    uint32_t g = _g + m;
    uint32_t b = _b + m;
    return ((r & 0xFF) << 16) | ((g & 0xFF) << 8) | (b & 0xFF);
}

void DFRobot_NeoPixel::setRangeColor(int16_t start, int16_t end, uint32_t c)
{

    if (start < 0 || end < 0)
    {
#if defined(NRF5) || defined(NRF52833)
        start = 0;
        end = strip->num_leds - 1;
#else
        start = 0;
        end = numLEDs - 1;
#endif
    }

    if (end < start)
    {
        uint16_t num = end;
        end = start;
        start = num;
    }
#if defined(NRF5) || defined(NRF52833)
    if (strip->num_leds <= 0)
        return;
    start = max(start, 0);
    start = min(start, strip->num_leds);
    end = max(end, 0);
    end = min(end, strip->num_leds);
#else
    if (numLEDs <= 0)
        return;
    start = max(start, 0);
    start = min(start, numLEDs);
    end = max(end, 0);
    end = min(end, numLEDs);
#endif

    for (uint16_t n = start; n < end + 1; n++)
    {
        this->setPixelColor(n, c, false);
    }

    show();
}

// Set pixel color from 'packed' 32-bit RGB color:
void DFRobot_NeoPixel::setPixelColor(uint16_t n, uint32_t c, bool user)
{

#if defined(NRF5) || defined(NRF52833)

    if (n < strip->num_leds)
    {
        strip1->leds[n].simple.r = ((uint8_t)(c >> 16));
        strip1->leds[n].simple.g = ((uint8_t)(c >> 8));
        strip1->leds[n].simple.b = ((uint8_t)(c));
        strip->leds[n].simple.r = (((uint8_t)(c >> 16)) * brightness) >> 8;
        strip->leds[n].simple.g = (((uint8_t)(c >> 8)) * brightness) >> 8;
        strip->leds[n].simple.b = (((uint8_t)(c)) * brightness) >> 8;
    }
    else
        return;
#else

    if (n < numLEDs)
    {
        uint8_t *p, *p1,
            r = (uint8_t)(c >> 16),
            g = (uint8_t)(c >> 8),
            b = (uint8_t)c;

        if (wOffset == rOffset)
        {
            p = &pixels[n * 3];
            p1 = &pixels1[n * 3];
        }
        else
        {
            p = &pixels[n * 4];
            p1 = &pixels1[n * 4];
            uint8_t w = (uint8_t)(c >> 24);
            p[wOffset] = brightness ? ((w * brightness) >> 8) : w;
            p1[wOffset] = brightness ? ((w * brightness) >> 8) : w;
        }
        p1[rOffset] = r;
        p1[gOffset] = g;
        p1[bOffset] = b;
        r = (r * brightness) >> 8;
        g = (g * brightness) >> 8;
        b = (b * brightness) >> 8;
        p[rOffset] = r;
        p[gOffset] = g;
        p[bOffset] = b;
    }
#endif
    if (user)
        show();
}

// Convert separate R,G,B into packed 32-bit RGB color.
// Packed format is always RGB, regardless of LED strand color order.
uint32_t DFRobot_NeoPixel::Color(uint8_t r, uint8_t g, uint8_t b)
{
    return ((uint32_t)r << 16) | ((uint32_t)g << 8) | b;
}

// Convert separate R,G,B,W into packed 32-bit WRGB color.
// Packed format is always WRGB, regardless of LED strand color order.
uint32_t DFRobot_NeoPixel::Color(uint8_t r, uint8_t g, uint8_t b, uint8_t w)
{
    return ((uint32_t)w << 24) | ((uint32_t)r << 16) | ((uint32_t)g << 8) | b;
}

// Query color from previously-set pixel (returns packed 32-bit RGB value)
uint32_t DFRobot_NeoPixel::getPixelColor(uint16_t n) const
{

#if defined(NRF5) || defined(NRF52833)

    if (n >= strip->num_leds)
        return 0;

    return ((uint32_t)strip1->leds[n].simple.r << 16) |
           ((uint32_t)strip1->leds[n].simple.g << 8) |
           ((uint32_t)strip1->leds[n].simple.b);

#else

    if (n >= numLEDs)
        return 0; // Out of bounds, return no color.

    uint8_t *p1;

    if (wOffset == rOffset)
    { // Is RGB-type device
        p1 = &pixels1[n * 3];
        // Stored color was decimated by setBrightness().  Returned value
        // attempts to scale back to an approximation of the original 24-bit
        // value used when setting the pixel color, but there will always be
        // some error -- those bits are simply gone.  Issue is most
        // pronounced at low brightness levels.
        return ((uint32_t)p1[rOffset] << 16) |
               ((uint32_t)p1[gOffset] << 8) |
               (uint32_t)p1[bOffset];
    }
    else
    { // Is RGBW-type device

        p1 = &pixels[n * 4];

        return ((uint32_t)p1[wOffset] << 24) |
               ((uint32_t)p1[rOffset] << 16) |
               ((uint32_t)p1[gOffset] << 8) |
               (uint32_t)p1[bOffset];
    }

#endif
}

// Returns pointer to pixels[] array.  Pixel data is stored in device-
// native format and is not translated here.  Application will need to be
// aware of specific pixel data format and handle colors appropriately.
uint8_t *DFRobot_NeoPixel::getPixels(void) const
{
    return pixels;
}

uint16_t DFRobot_NeoPixel::numPixels(void) const
{
    return numLEDs;
}

// Adjust output brightness; 0=darkest (off), 255=brightest.  This does
// NOT immediately affect what's currently displayed on the LEDs.  The
// next call to show() will refresh the LEDs at this level.  However,
// this process is potentially "lossy," especially when increasing
// brightness.  The tight timing in the WS2811/WS2812 code means there
// aren't enough free cycles to perform this scaling on the fly as data
// is issued.  So we make a pass through the existing color data in RAM
// and scale it (subsequent graphics commands also work at this
// brightness level).  If there's a significant step up in brightness,
// the limited number of steps (quantization) in the old data will be
// quite visible in the re-scaled version.  For a non-destructive
// change, you'll need to re-render the full strip data.  C'est la vie.
void DFRobot_NeoPixel::setBrightness(uint8_t b)
{
    // Stored brightness value is different than what's passed.
    // This simplifies the actual scaling math later, allowing a fast
    // 8x8-bit multiply and taking the MSB.  'brightness' is a uint8_t,
    // adding 1 here may (intentionally) roll over...so 0 = max brightness
    // (color values are interpreted literally; no scaling), 1 = min
    // brightness (off), 255 = just below max brightness.
    /* uint8_t newBrightness = b + 1;
  if(newBrightness != brightness) { // Compare against prior value
    // Brightness has changed -- re-scale existing data in RAM
    uint8_t  c,
            *ptr           = pixels,
             oldBrightness = brightness - 1; // De-wrap old brightness value
    uint16_t scale;
    if(oldBrightness == 0) scale = 0; // Avoid /0
    else if(b == 255) scale = 65535 / oldBrightness;
    else scale = (((uint16_t)newBrightness << 8) - 1) / oldBrightness;
    for(uint16_t i=0; i<numBytes; i++) {
      c      = *ptr;
      *ptr++ = (c * scale) >> 8;
    }
    brightness = newBrightness;
  }*/
    brightness = b;
#if defined(NRF5) || defined(NRF52833)
    if (strip->num_leds <= 0)
        return;
    for (int n = 0; n < strip->num_leds; n++)
    {
        strip->leds[n].simple.r = ((strip1->leds[n].simple.r) * brightness) >> 8;
        strip->leds[n].simple.g = ((strip1->leds[n].simple.g) * brightness) >> 8;
        strip->leds[n].simple.b = ((strip1->leds[n].simple.b) * brightness) >> 8;
    }
#else
    if (numLEDs <= 0)
        return;
    uint8_t *p, *p1;
    for (int n = 0; n < numLEDs; n++)
    {
        p = &pixels[n * 3];
        p1 = &pixels1[n * 3];
        p[rOffset] = (p1[rOffset] * brightness) >> 8;
        p[gOffset] = (p1[gOffset] * brightness) >> 8;
        p[bOffset] = (p1[bOffset] * brightness) >> 8;
    }
#endif
    show();
}

void DFRobot_NeoPixel::setBrightness(uint32_t b)
{
    setBrightness((uint8_t)b);
}

//Return the brightness value
uint8_t DFRobot_NeoPixel::getBrightness(void) const
{
    return brightness - 1;
}

void DFRobot_NeoPixel::clear()
{

#if defined(NRF5) || defined(NRF52833)
    if (strip->num_leds <= 0)
        return;
    for (int i = 0; i < strip->num_leds; i++)
    {
        strip1->leds[i].simple.g = 0;
        strip1->leds[i].simple.r = 0;
        strip1->leds[i].simple.b = 0;
        strip->leds[i].simple.g = 0;
        strip->leds[i].simple.r = 0;
        strip->leds[i].simple.b = 0;
    }
    show();

#else
    if (numLEDs <= 0)
        return;
    memset(pixels, 0, numBytes);
    memset(pixels1, 0, numBytes);

#endif
    show();
}

uint32_t DFRobot_NeoPixel::rgbToColor(uint8_t r, uint8_t g, uint8_t b)
{
    uint32_t cr = r;
    uint32_t cg = g;
    uint32_t cb = b;

    return ((cr << 16) | (cg << 8)) | cb;
}

#if defined(NRF5)
void sendNeopixelBuffer(uint32_t pin, uint8_t *data_address, uint16_t num_leds)
{
    asm volatile(
        "push {r0, r1, r2, r3, r4, r5, r6}"
        "\n\t"
        "mov r4, r1"
        "\n\t"
        "mov r6, #3"
        "\n\t"
        "mul r6, r2, r6"
        "\n\t"
        "mov r5, r6"
        "\n\t"
        "movs r3, #160"
        "\n\t"
        "movs r1, #0x0c"
        "\n\t"
        "lsl r3, r3, #15"
        "\n\t"
        "add r3, #05"
        "\n\t"
        "lsl r3, r3, #8"
        "\n\t"
        "add r2, r3, r1"
        "\n\t"
        "add r3, #0x08"
        "\n\t"
        "mov r1, r0"
        "\n\t"
        "mrs r6, PRIMASK"
        "\n\t"
        "push {r6}"
        "\n\t"
        "cpsid i"
        "\n\t"
        "b .start"
        "\n\t"
        ".nextbit:"
        "\n\t"
        "str r1, [r3, #0]"
        "\n\t"
        "tst r6, r0"
        "\n\t"
        "bne .bitisone"
        "\n\t"
        "str r1, [r2, #0]"
        "\n\t"
        ".bitisone:"
        "\n\t"
        "lsr r6, #1"
        "\n\t"
        "bne .justbit"
        "\n\t"
        "add r4, #1"
        "\n\t"
        "sub r5, #1"
        "\n\t"
        "beq .stop"
        "\n\t"
        ".start:"
        "\n\t"
        "movs r6, #0x80"
        "\n\t"
        "nop"
        "\n\t"
        ".common:"
        "\n\t"
        "str r1, [r2, #0]"
        "\n\t"
        "ldrb r0, [r4, #0]"
        "\n\t"
        "b .nextbit"
        "\n\t"
        ".justbit:"
        "\n\t"
        "b .common"
        "\n\t"
        ".stop:"
        "\n\t"
        "str r1, [r2, #0]"
        "\n\t"
        "pop {r6}"
        "\n\t"
        "msr PRIMASK, r6"
        "\n\t"
        "pop {r0, r1, r2, r3, r4, r5, r6}"
        "\n\t"
        "bx lr"
        "\n\t");
}
#endif
