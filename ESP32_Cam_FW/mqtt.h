#ifndef _MQTT_H_
#define _MQTT_H_

#include <string>

void mqtt_init();
void mqtt_task(void);
void pub_image(const byte *image_data, unsigned int length);
std::string mqtt_get_command();

#endif // _MQTT_H_
