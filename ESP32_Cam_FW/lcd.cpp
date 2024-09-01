#include <Adafruit_GFX.h>
#include <Adafruit_ST7735.h>
#include <JPEGDecoder.h>
#include <SPI.h>
#include "lcd.h"

#if (TFT_SPI == TFT_SPI_VSPI)
Adafruit_ST7735 tft = Adafruit_ST7735(&SPI, TFT_CS, TFT_DC, TFT_RST);
#elif (TFT_SPI == TFT_SPI_HSPI)
SPIClass hspi(HSPI);
Adafruit_ST7735 tft = Adafruit_ST7735(&hspi, TFT_CS, TFT_DC, TFT_RST);
#endif


/* 撮影データの処理に関するパラメータ定義 */
#define BMPIMAGE_OFFSET  54  // BMPヘッダーのサイズ（通常は54バイト）
#define BMPIMAGE_WIDTH   320 // 幅ピクセル数
#define BMPIMAGE_HEIGHT  240 // 高さピクセル数

/* ピクセルデータを保存するバッファ */
/* uint16_t pixelBuffer[BMPIMAGE_WIDTH];  // 1ライン分のピクセルデータを格納するバッファ */


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

void lcd_displayBmp(uint8_t* imageData, int length)
{
    int pixelIndex = BMPIMAGE_OFFSET;
    tft.fillScreen(ST77XX_BLACK);
    for (int y = 0; y < BMPIMAGE_HEIGHT; y++) {
        for (int x = 0; x < BMPIMAGE_WIDTH; x++) {
            if (pixelIndex >= length) return; // 受信したデータが終了したら処理を終える

            uint16_t color = imageData[pixelIndex] << 8 | imageData[pixelIndex + 1];
            pixelIndex += 2;

            tft.drawPixel(x, y, color);
        }
    }
}

/* void lcd_displayJpg(uint8_t* imageData, int length) */
/* { */
/*     uint16_t color = 0xFFFF; */

/*     if (jpeg.openRAM(imageData, length, JPEGDraw)) { */
/*         Serial.println("JPEG data open successful"); */

/*         jpeg.setPixelType(RGB565_BIG_ENDIAN); // RGB565形式でデコード */
/*         tft.fillScreen(ST77XX_BLACK); */
/*         for (int y = 0; y < BMPIMAGE_HEIGHT; y++) { */
/*             for (int x = 0; x < BMPIMAGE_WIDTH; x++) { */
/*                 if (jpeg.decode(x, y, 1)) { // 1ピクセルのみデコード */
/*                     color = jpeg.pImage[y * jpeg.MCUWidth + x]; // デコードされたピクセルの色を取得 */
/*                 } else { */
/*                     color = 0xFFFF; */
/*                 } */
/*                 tft.drawPixel(x, y, color); */

/*                 Serial.printf("Pixel color at (%d, %d): 0x%04X\n", x, y, color); */
/*             } */
/*         } */

/*         jpeg.close(); */
/*     } else { */
/*         Serial.println("JPEG data open failed"); */
/*     } */
/* } */

void lcd_displayJpg(uint8_t* imageData, int length)
{
    // バイト配列からJPEGをデコード
    JpegDec.decodeArray(imageData, length);

    // 画像情報を取得
    uint16_t *pImg = JpegDec.pImage;
    int imgWidth = JpegDec.width;
    int imgHeight = JpegDec.height;

    // デコードした画像の表示
    for (int y = 0; y < imgHeight; y++) {
        for (int x = 0; x < imgWidth; x++) {
            int color = pImg[y * imgWidth + x];
            tft.drawPixel(x, y, color);
        }
    }

    // デコード終了
    JpegDec.abort(); // メモリを解放}
}
