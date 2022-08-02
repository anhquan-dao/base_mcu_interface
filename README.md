## base_mcu_interface
Simple interface between laptop and MCU. The package is being tested on Ubuntu 18.04 as a ROS package. The test MCU is an [ESP-C3-32S](https://hshop.vn/products/kit-rf-thu-phat-wifi-ble-risc-v-esp32-c3-nodemcu-c3-32s-ai-thinker)

## Usage
The base class **BaseDriver** can currently handle:
 - Reading message with payload of (5+n) bytes with the format as shown below. The default length of data is 4 bytes. The n bytes data are fixed based on the parameter **data_len** of **readMessage**. The base class can handle uint16_t and float at the moment. However, the user can specify how the n bytes data to be processed by setting **data_cb** parameter in **readMessage** to the wanted data callback function.
 
 - Message format:      ID | HEADER | MESSAGE COUNTER | STATE | ERROR | DATA (n bytes)
 
 - Interruption in connection. The MCU can be disconnected and re-connected without crashing the program. The user should use the **read** methods of **BaseDriver** to avoid crashing the program when there is disconnection.
 
## What it cannot do (at the moment):
  - Write to the MCU

## TODO:
 - [ ] Write requirements.txt
 - [ ] Handle dynamic message length.
 - [ ] Log status and errors in an easy-to-read format
 - [ ] Test Windows integration
 - [ ] Writing examples 
