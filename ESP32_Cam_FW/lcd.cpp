#include <Adafruit_GFX.h>
#include <Adafruit_ST7735.h>
#include <SPI.h>
#include "lcd.h"

//SPI0をコンストラクタに指定する
Adafruit_ST7735 tft = Adafruit_ST7735(&SPI, TFT_CS, TFT_DC, TFT_RST);

void lcd_init(void)
{
    /* SPI.setTX(TFT_MOSI);                        //H/W SPI 設定 */
    /* SPI.setSCK(TFT_SCLK); */
    pinMode(TFT_BL, OUTPUT);
    pinMode(TFT_DC, OUTPUT);
    pinMode(TFT_RST, OUTPUT);
    SPI.begin();

    digitalWrite(TFT_BL, HIGH);
    digitalWrite(TFT_DC, HIGH);
    digitalWrite(TFT_RST, HIGH);

    tft.initR(INITR_BLACKTAB);                //Init ST7735S初期化

    tft.fillScreen(ST77XX_BLACK);               //背景の塗りつぶし

    //テキスト表示
    tft.setRotation(3);                         //画面回転
    tft.setTextSize(3);                         //サイズ

    tft.setCursor(0, 20);                      //カーソル位置
    tft.setTextColor(ST77XX_RED);              //赤
    tft.printf("TAMANEGI\n");

    tft.setTextColor(ST77XX_GREEN);            //緑
    tft.printf("TAMANEGI\n");

    tft.setTextColor(ST77XX_BLUE);             //青
    tft.printf("TAMANEGI\n");

    tft.setTextColor(ST77XX_YELLOW);           //黄
    tft.printf("TAMANEGI\n");
}
