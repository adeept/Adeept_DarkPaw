
#ifndef ADAFRUIT_NEOPIXEL_H
#define ADAFRUIT_NEOPIXEL_H

#if (ARDUINO >= 100)
#include <Arduino.h>
#else
#include <WProgram.h>
#include <pins_arduino.h>
#endif

#define NEOPIXEL_RMT 1
#if defined(NEOPIXEL_RMT) && defined(ESP32)
#include "RMT.h"
#endif
// RGB NeoPixel permutations; white and red offsets are always same
// Offset:         W          R          G          B
#define NEO_RGB ((0 << 6) | (0 << 4) | (1 << 2) | (2))
#define NEO_RBG ((0 << 6) | (0 << 4) | (2 << 2) | (1))
#define NEO_GRB ((1 << 6) | (1 << 4) | (0 << 2) | (2))
#define NEO_GBR ((2 << 6) | (2 << 4) | (0 << 2) | (1))
#define NEO_BRG ((1 << 6) | (1 << 4) | (2 << 2) | (0))
#define NEO_BGR ((2 << 6) | (2 << 4) | (1 << 2) | (0))

// RGBW NeoPixel permutations; all 4 offsets are distinct
// Offset:         W          R          G          B
#define NEO_WRGB ((0 << 6) | (1 << 4) | (2 << 2) | (3))
#define NEO_WRBG ((0 << 6) | (1 << 4) | (3 << 2) | (2))
#define NEO_WGRB ((0 << 6) | (2 << 4) | (1 << 2) | (3))
#define NEO_WGBR ((0 << 6) | (3 << 4) | (1 << 2) | (2))
#define NEO_WBRG ((0 << 6) | (2 << 4) | (3 << 2) | (1))
#define NEO_WBGR ((0 << 6) | (3 << 4) | (2 << 2) | (1))

#define NEO_RWGB ((1 << 6) | (0 << 4) | (2 << 2) | (3))
#define NEO_RWBG ((1 << 6) | (0 << 4) | (3 << 2) | (2))
#define NEO_RGWB ((2 << 6) | (0 << 4) | (1 << 2) | (3))
#define NEO_RGBW ((3 << 6) | (0 << 4) | (1 << 2) | (2))
#define NEO_RBWG ((2 << 6) | (0 << 4) | (3 << 2) | (1))
#define NEO_RBGW ((3 << 6) | (0 << 4) | (2 << 2) | (1))

#define NEO_GWRB ((1 << 6) | (2 << 4) | (0 << 2) | (3))
#define NEO_GWBR ((1 << 6) | (3 << 4) | (0 << 2) | (2))
#define NEO_GRWB ((2 << 6) | (1 << 4) | (0 << 2) | (3))
#define NEO_GRBW ((3 << 6) | (1 << 4) | (0 << 2) | (2))
#define NEO_GBWR ((2 << 6) | (3 << 4) | (0 << 2) | (1))
#define NEO_GBRW ((3 << 6) | (2 << 4) | (0 << 2) | (1))

#define NEO_BWRG ((1 << 6) | (2 << 4) | (3 << 2) | (0))
#define NEO_BWGR ((1 << 6) | (3 << 4) | (2 << 2) | (0))
#define NEO_BRWG ((2 << 6) | (1 << 4) | (3 << 2) | (0))
#define NEO_BRGW ((3 << 6) | (1 << 4) | (2 << 2) | (0))
#define NEO_BGWR ((2 << 6) | (3 << 4) | (1 << 2) | (0))
#define NEO_BGRW ((3 << 6) | (2 << 4) | (1 << 2) | (0))

// Add NEO_KHZ400 to the color order value to indicate a 400 KHz
// device.  All but the earliest v1 NeoPixels expect an 800 KHz data
// stream, this is the default if unspecified.  Because flash space
// is very limited on ATtiny devices (e.g. Trinket, Gemma), v1
// NeoPixels aren't handled by default on those chips, though it can
// be enabled by removing the ifndef/endif below -- but code will be
// bigger.  Conversely, can disable the NEO_KHZ400 line on other MCUs
// to remove v1 support and save a little space.

#define NEO_KHZ800 0x0000 // 800 KHz datastream
#ifndef __AVR_ATtiny85__
#define NEO_KHZ400 0x0100 // 400 KHz datastream
#endif

// If 400 KHz support is enabled, the third parameter to the constructor
// requires a 16-bit value (in order to select 400 vs 800 KHz speed).
// If only 800 KHz is enabled (as is default on ATtiny), an 8-bit value
// is sufficient to encode pixel color order, saving some space.

#ifdef NEO_KHZ400
typedef uint16_t neoPixelType;
#else
typedef uint8_t neoPixelType;
#endif

#if defined(NRF5) || defined(NRF52833)

typedef struct _neopixel_obj_t
{
  uint16_t pin_num;
  uint16_t num_pixels;
  uint8_t *data;
} neopixel_obj_t;

#ifndef NRF52833
void sendNeopixelBuffer(uint32_t pin, uint8_t *data_address, uint16_t num_leds);
#endif

#define PINMODE(pin) NRF_GPIO->PIN_CNF[pin] = ((uint32_t)GPIO_PIN_CNF_DIR_Output << GPIO_PIN_CNF_DIR_Pos) | ((uint32_t)GPIO_PIN_CNF_INPUT_Disconnect << GPIO_PIN_CNF_INPUT_Pos) | ((uint32_t)GPIO_PIN_CNF_PULL_Disabled << GPIO_PIN_CNF_PULL_Pos) | ((uint32_t)GPIO_PIN_CNF_DRIVE_S0S1 << GPIO_PIN_CNF_DRIVE_Pos) | ((uint32_t)GPIO_PIN_CNF_SENSE_Disabled << GPIO_PIN_CNF_SENSE_Pos);
#define HI(pin) NRF_GPIO->OUTSET = (1UL << pin);
#define LO(pin) NRF_GPIO->OUTCLR = (1UL << pin);
/*
//These defines are timed specific to a series of if statements and will need to be changed
//to compensate for different writing algorithms than the one in neopixel.c
#define NEOPIXEL_SEND_ONE	HI(PIN); \
        __asm ( \
                " NOP\n\t" \
                " NOP\n\t" \
                " NOP\n\t" \
                " NOP\n\t" \
                " NOP\n\t" \
                " NOP\n\t" \
                " NOP\n\t" \
                " NOP\n\t" \
                " NOP\n\t" \
            ); \
        LO(PIN); \

#define NEOPIXEL_SEND_ZERO HI(PIN); \
        __asm (  \
                " NOP\n\t"  \
            );  \
        LO(PIN);  \
        __asm ( \
                " NOP\n\t" \
                " NOP\n\t" \
                " NOP\n\t" \
                " NOP\n\t" \
                " NOP\n\t" \
                " NOP\n\t" \
                " NOP\n\t" \
                " NOP\n\t" \
            );
*/
typedef union
{
  struct
  {
    uint8_t g, r, b;
  } simple;
  uint8_t grb[3];
} color_t;

typedef struct
{
  uint8_t pin_num;
  uint16_t num_leds;
  color_t *leds;
} neopixel_strip_t;

#endif

class DFRobot_NeoPixel
{

public:
  // Constructor: number of LEDs, pin number, LED type
  //DFRobot_NeoPixel(uint8_t p=6, uint16_t n=4, uint8_t bright = 255, neoPixelType t=NEO_GRB + NEO_KHZ800);
  DFRobot_NeoPixel(void);
  ~DFRobot_NeoPixel();

  void
  begin(uint8_t p = 6, uint16_t n = 4, uint8_t bright = 255, neoPixelType t = NEO_GRB + NEO_KHZ800),
      show(void),
      setPin(uint8_t p),
      setPixelColor(uint16_t n, uint8_t r, uint8_t g, uint8_t b),
      setPixelColor(uint16_t n, uint8_t r, uint8_t g, uint8_t b, uint8_t w),
      setPixelColor(uint16_t n, uint32_t c, bool user = true),
      setRangeColor(int16_t start, int16_t end, uint32_t c),
      showRainbow(uint16_t start, uint16_t end, uint32_t startHue, uint32_t endHue),
      shift(int8_t offset),
      rotate(int8_t offset),
      showBarGraph(uint16_t start, uint16_t end, int16_t value, int16_t high),
      setBrightness(uint8_t),
      setBrightness(uint32_t),
      clear(),
      updateLength(uint16_t n),
      updateType(neoPixelType t);

  void setBrightness(int bright) { setBrightness((uint8_t)bright); }
  void setBrightness(float bright) { setBrightness((uint8_t)bright); }
  void setBrightness(double bright) { setBrightness((uint8_t)bright); }
#if defined(ESP32)
  void setBrightness(long int bright)
  {
    setBrightness((uint8_t)bright);
  }
#else
  void setBrightness(int32_t bright)
  {
    setBrightness((uint8_t)bright);
  }
#endif
  uint8_t
      *
      getPixels(void) const,
      getBrightness(void) const;
  int8_t
  getPin(void) { return pin; };
  uint16_t
  numPixels(void) const;
  static uint32_t
  Color(uint8_t r, uint8_t g, uint8_t b),
      Color(uint8_t r, uint8_t g, uint8_t b, uint8_t w);
  uint32_t
  getPixelColor(uint16_t n) const;
  uint32_t rgbToColor(uint8_t r, uint8_t g, uint8_t b);
  inline bool
#if defined(__AVR__)
  canShow(void)
  {
    return (micros() - endTime) >= 300L;
  }
#endif
#if defined(NRF5) || defined(NRF52833)
  canShow(void)
  {
    return (micros() - endTime) >= 300L;
  }
#endif
#if defined(ESP32)
  canShow(void)
  {
    return (micros() - endTime) >= 300L;
  }
#endif

#if defined(NRF5) || defined(NRF52833)
  void neopixel_init(neopixel_strip_t *strip, uint8_t pin_num, uint16_t num_leds);

  void neopixel_clear(neopixel_strip_t *strip);

  void neopixel_show(neopixel_strip_t *strip);

  uint8_t neopixel_set_color(neopixel_strip_t *strip, uint16_t index, uint8_t red, uint8_t green, uint8_t blue);

  uint8_t neopixel_set_color_and_show(neopixel_strip_t *strip, uint16_t index, uint8_t red, uint8_t green, uint8_t blue);

  void neopixel_destroy(neopixel_strip_t *strip);

#endif

private:
  struct parameterInit_t
  {
    uint8_t p;
    uint16_t n;
    uint8_t b;
    neoPixelType t;
  } parameterInit;

  uint32_t hsl(uint32_t h, uint32_t s, uint32_t l);

  boolean
#ifdef NEO_KHZ400 // If 400 KHz NeoPixel support enabled...
      is800KHz,   // ...true if 800 KHz pixels
#endif
      begun; // true if begin() previously called
  uint16_t
      numLEDs,  // Number of RGB LEDs in strip
      numBytes; // Size of 'pixels' buffer below (3 or 4 bytes/pixel)
  int8_t
      pin; // Output pin number (-1 if not yet set)
  uint8_t
      brightness,
      *pixels,  // Holds LED color values (3 or 4 bytes each)
      *pixels1, // Holds LED color values (3 or 4 bytes each)
      rOffset,  // Index of red byte within each 3- or 4-byte pixel
      gOffset,  // Index of green byte
      bOffset,  // Index of blue byte
      wOffset;  // Index of white byte (same as rOffset if no white)
  uint32_t
      endTime; // Latch timing reference
#ifdef __AVR__
  volatile uint8_t
      *port; // Output PORT register
  uint8_t
      pinMask; // Output PORT bitmask
#endif

#if defined(NRF5) || defined(NRF52833)
  neopixel_strip_t m_strip;
  neopixel_strip_t m_strip1;
  neopixel_strip_t *strip = &m_strip;
  neopixel_strip_t *strip1 = &m_strip1;
#endif
};

#endif // ADAFRUIT_NEOPIXEL_H
