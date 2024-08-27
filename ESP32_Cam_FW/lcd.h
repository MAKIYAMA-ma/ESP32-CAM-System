#ifndef _LCD_H_
#define _LCD_H_

#define TFT_BL   32 //14 // BL
#define TFT_DC   25 // DC
#define TFT_CS   5  // CS
#define TFT_SCLK 18 // Clock
#define TFT_MOSI 23 // MOSI
#define TFT_RST  27 // Reset

void lcd_init(void);

#endif // _LCD_H_
