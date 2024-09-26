
Summary of Steps to Flash firmware to ESP32:


1. Check if Arduino CLI is installed, if not install it.

2.Get the firmware by copying the contents of [client.ino](https://github.com/OpenInterpreter/01/blob/main/software/source/clients/esp32/src/client/client.ino) from the 01 repository. save it as client.ino in a folder called client.

3. install the esp32 board for the Arduino CLI

4. Install M5Atom by M5Stack, WebSockets by Markus Sattler, AsyncTCP by dvarrel, and ESPAsyncWebServer by lacamera

5. Compile the Sketch:
   - Usedarduino-cli compile --fqbn esp32:esp32:m5stack_atom client to compile the sketch.

6. Identify the Serial Port:
   - Listed available serial ports and identifiedCOM5 as the USB Serial Port.

7. Upload the Sketch:
   - Used Arduino-cli upload -p COM5 --fqbn esp32:esp32:m5stack_atom client to upload the sketch to the ESP32 device.
