#include <Adafruit_GFX.h>
#include <Adafruit_ST7735.h>
#include <JPEGDecoder.h>
#include <SPI.h>
#include "lcd.h"
#include "config.h"

#ifndef SAVE_IMAGE_TO_SDCARD
#if (TFT_SPI == TFT_SPI_VSPI)
Adafruit_ST7735 tft = Adafruit_ST7735(&SPI, TFT_CS, TFT_DC, TFT_RST);
#elif (TFT_SPI == TFT_SPI_HSPI)
SPIClass hspi(HSPI);
Adafruit_ST7735 tft = Adafruit_ST7735(&hspi, TFT_CS, TFT_DC, TFT_RST);
#endif

#define TFT_WIDTH   160 // TFTのドット数
#define TFT_HEIGHT  128 // TFTのドット数

/* 撮影データの処理に関するパラメータ定義 */
#define BMPIMAGE_OFFSET  54  // BMPヘッダーのサイズ（通常は54バイト）
#define BMPIMAGE_WIDTH   320 // 幅ピクセル数
#define BMPIMAGE_HEIGHT  240 // 高さピクセル数

/* ピクセルデータを保存するバッファ */
/* uint16_t pixelBuffer[BMPIMAGE_WIDTH];  // 1ライン分のピクセルデータを格納するバッファ */

static void printRGB565(uint16_t color);

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

#define DEBUG_MODE 0
#if (DEBUG_MODE == 2)
// RGB565形式のカラー定義
enum ColorRGB565 {
    WHITE = 0xFFFF, // 11111 111111 11111
    RED   = 0xF800, // 11111 000000 00000
    GREEN = 0x07E0, // 00000 111111 00000
    BLUE  = 0x001F, // 00000 000000 11111
    BLACK = 0x0000  // 00000 000000 00000
};
#endif
void lcd_displayJpg(uint8_t* imageData, int length)
{
#if (DEBUG_MODE == 1)
    // バイト配列からJPEGをデコード
    JpegDec.decodeArray(imageData, length);

    // 画像情報を取得
    uint16_t *pImg = JpegDec.pImage;
    int imgWidth = JpegDec.width;
    int imgHeight = JpegDec.height;

    Serial.printf("image_size : %d x %d\n", imgWidth, imgHeight);

    // デコードした画像の表示
    for (int y = 0; y < TFT_HEIGHT; y++) {
        for (int x = 0; x < TFT_WIDTH; x++) {
            Serial.printf("draw(%3d, %3d) -> [%5d]", x, y, y * imgWidth + x);
            uint16_t color = pImg[y * imgWidth + x];
            tft.drawPixel(x, y, color);
            Serial.printf(" : drawn[0x%04X(", color);
            printRGB565(color);
            Serial.printf(")]\n");
        }
    }

    // デコード終了
    JpegDec.abort(); // メモリを解放}
#elif (DEBUG_MODE == 2)
    // Test code to check tft.drawPixel
    int colors[] = {WHITE, RED, GREEN, BLUE, BLACK};
    int colorIndex = 0;
    const int numColors = sizeof(colors) / sizeof(colors[0]);

    for (int y = 0; y < TFT_HEIGHT; y++) {
        for (int x = 0; x < TFT_WIDTH; x++) {
            int color = colors[colorIndex];
            Serial.printf("x, y : (%d, %d)\n", x, y);
            tft.drawPixel(x, y, color);
            colorIndex = (colorIndex + 1) % numColors;
        }
    }
#else
    // バイト配列からJPEGをデコード
    JpegDec.decodeArray(imageData, length);

    // 画像情報を取得
    uint16_t *pImg = JpegDec.pImage;
    int imgWidth = JpegDec.width;
    int imgHeight = JpegDec.height;
    int tgtX, tgtY;

    Serial.printf("image_size : %d x %d\n", imgWidth, imgHeight);
    int rate = 1;
    if(imgWidth > TFT_WIDTH) {
        rate = (imgWidth / TFT_WIDTH);
        if(imgWidth%TFT_WIDTH != 0) {
            rate++;
        }
    }
    if(imgHeight > TFT_HEIGHT) {
        int rate_h = (imgHeight / TFT_HEIGHT);
        if(imgHeight%TFT_HEIGHT != 0) {
            rate_h++;
        }
        if(rate_h > rate) {
            rate = rate_h;
        }
    }
    Serial.printf("rate : %d\n", rate);

    // デコードした画像の表示
    tgtY = 0;
    /* for (int y = 0; y < TFT_HEIGHT; y++) { */
    for (int y = 0; y < imgHeight; y++) {
        if(y % rate) {
            continue;
        }
        tgtX = 0;
        /* for (int x = 0; x < TFT_WIDTH; x++) { */
        for (int x = 0; x < imgWidth; x++) {
            /* Serial.printf("x, y : (%d, %d)\n", x, y); */
            if(x % rate) {
                continue;
            }
            Serial.printf("draw(%3d, %3d) <- ((%3d, %3d) -> [%5d])", tgtX, tgtY, x, y, y * imgWidth + x);
            uint16_t color = pImg[y * imgWidth + x];
            tft.drawPixel(tgtX, tgtY, color);
            Serial.printf(" : drawn[0x%04X(", color);
            printRGB565(color);
            Serial.printf(")]\n");
            tgtX++;
        }
        tgtY++;
    }

    // デコード終了
    JpegDec.abort(); // メモリを解放}
#endif
}

static void printRGB565(uint16_t color)
{
    // RGB565から各成分を取り出す
    uint8_t red   = (color >> 11) & 0x1F;  // 5ビットのR成分
    uint8_t green = (color >> 5)  & 0x3F;  // 6ビットのG成分
    uint8_t blue  = color & 0x1F;          // 5ビットのB成分

    // フルスケールに拡張 (0-255)
    red = (red * 255) / 31;
    green = (green * 255) / 63;
    blue = (blue * 255) / 31;

    // 結果を表示
    Serial.printf("R: %3u, G: %3u, B: %3u", red, green, blue);
}
#endif
