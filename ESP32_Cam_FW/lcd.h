#ifndef _LCD_H_
#define _LCD_H_

#define TFT_SPI_VSPI 1
#define TFT_SPI_HSPI 2
#define TFT_SPI TFT_SPI_HSPI

#define TFT_BL   2  // BL
#define TFT_DC   32 // DC
#define TFT_RST  0  // Reset
#if (TFT_SPI == TFT_SPI_VSPI)
#define TFT_CS   5  // CS
#define TFT_SCLK 18 // Clock
#define TFT_MOSI 23 // MOSI
#define TFT_MISO 19 // MISO
#elif (TFT_SPI == TFT_SPI_HSPI)
#define TFT_CS   15  // CS
#define TFT_SCLK 14 // Clock
#define TFT_MOSI 13 // MOSI
#define TFT_MISO 12 // MISO
#endif

void lcd_init(void);
void lcd_setText(String txt);

#endif // _LCD_H_
