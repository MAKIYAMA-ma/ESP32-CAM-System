#include <Adafruit_GFX.h>
#include <Adafruit_ST7735.h>
#include <SPI.h>
#include "lcd.h"

#if (TFT_SPI == TFT_SPI_VSPI)
Adafruit_ST7735 tft = Adafruit_ST7735(&SPI, TFT_CS, TFT_DC, TFT_RST);
#elif (TFT_SPI == TFT_SPI_HSPI)
SPIClass hspi(HSPI);
Adafruit_ST7735 tft = Adafruit_ST7735(&hspi, TFT_CS, TFT_DC, TFT_RST);
#endif

void lcd_init(void)
{
    Serial.println("start lcd init");

    digitalWrite(TFT_RST, LOW);
    digitalWrite(TFT_BL,  LOW);
    pinMode(TFT_BL,  OUTPUT);
    pinMode(TFT_DC,  OUTPUT);
    pinMode(TFT_RST, OUTPUT);

    delay(500);
    digitalWrite(TFT_RST, HIGH);
    digitalWrite(TFT_BL,  HIGH);

    tft.initR(INITR_BLACKTAB);
    tft.fillScreen(ST77XX_BLACK);
    tft.setRotation(3);
    /* tft.setTextWrap(false); */

    tft.setTextSize(2);
    tft.setTextColor(ST77XX_WHITE);
    tft.setCursor(5, 5);
    tft.print("Ready...");
    delay(3000);
}

void lcd_setText(String txt)
{
    tft.fillScreen(ST77XX_BLACK);
    tft.setCursor(5, 5);
    tft.print(txt);
}
