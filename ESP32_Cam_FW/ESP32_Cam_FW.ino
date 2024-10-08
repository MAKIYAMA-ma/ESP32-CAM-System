/**********************************************************************
  Filename    : Camera Web Serrver
  Description : ESP32 connects to WiFi and prints a url through a serial port.
                Users visit the site to view the image data ESP32 camera.
  Auther      : www.freenove.com
  Modification: 2021/12/01
**********************************************************************/
#include "esp_camera.h"
#include "esp_timer.h"
#include "mqtt.h"
#include "lcd.h"
#include <WiFi.h>
#include <stdlib.h>
#include <string>
#include <ArduinoJson.h>
#include "config.h"
#ifdef SAVE_IMAGE_TO_SDCARD
#include "sd_read_write.h"
#include "SD_MMC.h"
#endif

#ifdef USE_BLT_CMD
    #include "bluetooth.h"
#endif

#define INI_INTERVAL_SHOT false
#define INI_CAPTURE_INTERVAL 10*1000  // once per 10 sec
#define INI_HUMAN_SENSOR false

// ===================
// Select camera model
// ===================
#define CAMERA_MODEL_WROVER_KIT // Has PSRAM
//#define CAMERA_MODEL_ESP_EYE // Has PSRAM
//#define CAMERA_MODEL_ESP32S3_EYE // Has PSRAM
//#define CAMERA_MODEL_M5STACK_PSRAM // Has PSRAM
//#define CAMERA_MODEL_M5STACK_V2_PSRAM // M5Camera version B Has PSRAM
//#define CAMERA_MODEL_M5STACK_WIDE // Has PSRAM
//#define CAMERA_MODEL_M5STACK_ESP32CAM // No PSRAM
//#define CAMERA_MODEL_M5STACK_UNITCAM // No PSRAM
//#define CAMERA_MODEL_AI_THINKER // Has PSRAM
//#define CAMERA_MODEL_TTGO_T_JOURNAL // No PSRAM
// ** Espressif Internal Boards **
//#define CAMERA_MODEL_ESP32_CAM_BOARD
//#define CAMERA_MODEL_ESP32S2_CAM_BOARD
//#define CAMERA_MODEL_ESP32S3_CAM_LCD

#define SD_MMC_CMD 15 //Please do not modify it.
#define SD_MMC_CLK 14 //Please do not modify it.
#define SD_MMC_D0  2  //Please do not modify it.

#define HUMAN_SENSOR  33
// #define HIGH 1
// #define LOW  0

#include "camera_pins.h"
#include "camera_app.h"

camera_config_t config;

//void startCameraServer();
void config_init();
#ifdef SAVE_IMAGE_TO_SDCARD
static void sdcard_init(void);
#endif

void setup() {
    pinMode(HUMAN_SENSOR, INPUT);
    Serial.begin(115200);
    Serial.setDebugOutput(true);
    Serial.println();

    config_init();

    // camera init
    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
        Serial.printf("Camera init failed with error 0x%x", err);
        return;
    }

    sensor_t * s = esp_camera_sensor_get();
    s->set_vflip(s, 0);        //1-Upside down, 0-No operation
    s->set_hmirror(s, 0);      //1-Reverse left and right, 0-No operation
    s->set_brightness(s, 1);   //up the blightness just a bit
    s->set_saturation(s, -1);  //lower the saturation

#if 0
    // Camera Server
    WiFi.begin(ssid_Router, password_Router);
    while (WiFi.isConnected() != true) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("");
    Serial.println("WiFi connected");

    startCameraServer();

    Serial.print("Camera Ready! Use 'http://");
    Serial.print(WiFi.localIP());
    Serial.println("' to connect");
#endif

#ifdef SAVE_IMAGE_TO_SDCARD
    sdcard_init();
#endif

    // MQTT
    mqtt_init();
#ifdef USE_BLT_CMD
    bt_init();
#endif

#ifndef SAVE_IMAGE_TO_SDCARD
    lcd_init();
#endif

    // publish initial settings
    pub_setting(INI_INTERVAL_SHOT, INI_CAPTURE_INTERVAL, INI_HUMAN_SENSOR);
}

void loop() {
    static int64_t latest_time = esp_timer_get_time();
    int64_t i;
    static int64_t snap_cnt = 0;
    std::string rcvd_cmd;
    uint8_t *rcvd_img;
    size_t rcvd_img_size;
    int64_t current_time;
    static int64_t interval = INI_CAPTURE_INTERVAL;
    static bool interval_shot = INI_INTERVAL_SHOT;
    static bool human_sensor = INI_HUMAN_SENSOR;
    bool capture = false;

    static int64_t latest_level = LOW;
    int64_t cur_level;

#ifdef USE_BLT_CMD
    // get received command via bluetooth
    bt_chk_command();
    rcvd_cmd = bt_get_command();
    if(rcvd_cmd != "") {
        Serial.print("cmd:[" + String(rcvd_cmd.c_str()) + "]\n");

        if(rcvd_cmd == "shot") {
            capture = true;
        }
    }
#endif

    rcvd_cmd = mqtt_get_command();
    if(rcvd_cmd != "") {
        StaticJsonDocument<10> doc;
        DeserializationError error = deserializeJson(doc, rcvd_cmd);

        // エラーのチェック
        if (error) {
            Serial.print(F("deserializeJson() failed: "));
            Serial.println(error.f_str());
        } else {
            if(doc.containsKey("shot")) {
                capture = doc["shot"];
            }
            if(doc.containsKey("interval_shot")) {
                interval_shot = doc["interval_shot"];
                if(interval_shot) {
                    Serial.println("enable interval shot");
                    latest_time = esp_timer_get_time();
                } else {
                    Serial.println("disable interval shot");
                }
            }
            if(doc.containsKey("interval")) {
                interval = doc["interval"];
            }
            if(doc.containsKey("human_sensor")) {
                human_sensor = doc["human_sensor"];
                if(human_sensor) {
                    Serial.println("enable human_sensor shot");
                    latest_level = LOW;
                } else {
                    Serial.println("disable human_sensor shot");
                }
            }
            if(doc.containsKey("reqset")) {
                if(doc["reqset"]) {
                    pub_setting(interval_shot, interval, human_sensor);
                }
            }
#ifndef SAVE_IMAGE_TO_SDCARD
#if (SHOW_RESULT == SHOW_TEXT)
            if(doc.containsKey("text")) {
                lcd_setText(doc["text"]);
            }
#endif
#endif
        }
    }

#if ((SHOW_RESULT == SHOW_IMG) || (SHOW_RESULT == SHOW_IMG_SCALE))
    rcvd_img = mqtt_get_img();
    if(rcvd_img != NULL) {
        rcvd_img_size = mqtt_get_img_size();
#ifdef SAVE_IMAGE_TO_SDCARD
        char filename[32] = "";
        sprintf(filename, "/capture_%d.jpg", snap_cnt);
        writeBinFile(SD_MMC, filename, rcvd_img, rcvd_img_size);
#else
        lcd_displayJpg(rcvd_img, rcvd_img_size);
        //lcd_displayBmp(rcvd_img, rcvd_img_size);
#endif
        mqtt_del_img();
    }
#endif

    if(interval_shot) {
        current_time = esp_timer_get_time();
        if(((current_time - latest_time) / 1000) > interval) {
            Serial.printf("Current time[%d]\n", current_time);
            capture = true;
        }
    }

    if(human_sensor) {
        cur_level = digitalRead(HUMAN_SENSOR);
        if((latest_level == LOW) && (cur_level == HIGH)) {
            Serial.printf("New motion is detected\n");
            capture = true;
        }

        latest_level = cur_level;
    }

    if(capture) {
        uint8_t *buf = NULL;
        size_t data_size = 0;

        latest_time = current_time;

        if(camera_capture(&buf, &data_size) == ESP_OK) {
            Serial.printf("Captured[%d][%d Bytes]\n", snap_cnt, data_size);
#ifndef SAVE_IMAGE_TO_SDCARD
            lcd_setText("capture:[" + String(snap_cnt) + "]");
#endif
#ifdef SAVE_IMAGE_TO_SDCARD
            char filename[32] = "";
            sprintf(filename, "/capture_%d.jpg", snap_cnt);
            writeBinFile(SD_MMC, filename, buf, data_size);
#endif
            pub_image(buf, data_size);
            free(buf);
            snap_cnt++;
        } else {
            Serial.printf("Fail to capture\n");
        }
    }

    mqtt_task();

    delay(50);
}

void config_init() {
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.frame_size = FRAMESIZE_QVGA;
  config.pixel_format = PIXFORMAT_JPEG; // for streaming
  //config.pixel_format = PIXFORMAT_RGB565; // for face detection/recognition
  config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.jpeg_quality = 12;
  config.fb_count = 1;
}

#ifdef SAVE_IMAGE_TO_SDCARD
static void sdcard_init(void)
{
    // SD Card initialize
    SD_MMC.setPins(SD_MMC_CLK, SD_MMC_CMD, SD_MMC_D0);
    if (!SD_MMC.begin("/sdcard", true, true, SDMMC_FREQ_DEFAULT, 5)) {
        Serial.println("Card Mount Failed");
        return;
    }
    uint8_t cardType = SD_MMC.cardType();
    if(cardType == CARD_NONE){
        Serial.println("No SD_MMC card attached");
        return;
    }

    Serial.print("SD_MMC Card Type: ");
    if(cardType == CARD_MMC){
        Serial.println("MMC");
    } else if(cardType == CARD_SD){
        Serial.println("SDSC");
    } else if(cardType == CARD_SDHC){
        Serial.println("SDHC");
    } else {
        Serial.println("UNKNOWN");
    }

    uint64_t cardSize = SD_MMC.cardSize() / (1024 * 1024);
    Serial.printf("SD_MMC Card Size: %lluMB\n", cardSize);

    listDir(SD_MMC, "/", 0);

    createDir(SD_MMC, "/mydir");
    listDir(SD_MMC, "/", 0);

    removeDir(SD_MMC, "/mydir");
    listDir(SD_MMC, "/", 2);
}
#endif
