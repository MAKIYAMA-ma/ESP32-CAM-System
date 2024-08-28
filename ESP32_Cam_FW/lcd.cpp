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
#if 1
    Serial.println("start lcd init");

    pinMode(TFT_BL,  OUTPUT);
    /* pinMode(TFT_DC,  OUTPUT); */
    /* pinMode(TFT_RST, OUTPUT); */

    /* digitalWrite(TFT_RST, HIGH); */
    /* delay(50); */
    /* digitalWrite(TFT_RST, LOW); */
    /* delay(500); */
    /* digitalWrite(TFT_RST, HIGH); */

    /* Serial.println("LCD ON"); */
    digitalWrite(TFT_BL,  HIGH);
    /* digitalWrite(TFT_DC,  HIGH); */

    tft.initR(INITR_GREENTAB);
    tft.fillScreen(ST77XX_BLACK);
    tft.setRotation(3);
    /* tft.setTextWrap(false); */

    tft.setTextSize(3);
    tft.setTextColor(ST77XX_RED);
    tft.setCursor(5, 5);
    tft.print("Ready...");
    delay(3000);
#else
    Serial.println("start lcd init");

    pinMode(TFT_BL,  OUTPUT);
    pinMode(TFT_DC,  OUTPUT);
    pinMode(TFT_RST, OUTPUT);

    SPI.begin();  // SPIの初期化

    // SPIトランザクションを開始
    SPI.beginTransaction(SPISettings(24000000, MSBFIRST, SPI_MODE0));

    digitalWrite(TFT_RST, HIGH);
    delay(50);
    digitalWrite(TFT_RST, LOW);
    delay(500);
    digitalWrite(TFT_RST, HIGH);

    Serial.println("LCD ON");
    digitalWrite(TFT_BL,  HIGH);
    digitalWrite(TFT_DC,  HIGH);

    tft.initR(INITR_GREENTAB);  // 他のオプションも試してみてください: INITR_GREENTAB, INITR_REDTAB

    tft.fillScreen(ST77XX_BLACK);

    tft.setRotation(0);  // 0, 1, 2も試してみてください
    tft.setTextSize(3);

    tft.setCursor(0, 20);
    tft.setTextColor(ST77XX_RED);
    tft.printf("TAMANEGI\n");

    // SPIトランザクションを終了
    SPI.endTransaction();

    Serial.println("LCD text displayed");
#endif
}
