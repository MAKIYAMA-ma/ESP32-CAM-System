#ifndef _MQTT_H_
#define _MQTT_H_

void mqtt_init();
void mqtt_task(void);
void mqtt_retry_connect(void);
void pub_image(const byte *image_data, unsigned int length);

#endif // _MQTT_H_
