// This library works only with the following circuit topology
// Vcc---NTC---ADC---SERIES_RESISTOR---GND
#include <iikit.h>
#define ADC_RESOLUTION 1023
#define TEMPERATURENOMINAL 25

double getTempTermistorNTCBeta(const uint16_t analogValue, const uint16_t serialResistance, const uint16_t bCoefficient, const uint16_t nominalResistance)
{
  float resistance, temp;

  // convert the value to resistance
  resistance = (serialResistance / ((float)analogValue)) * ADC_RESOLUTION - serialResistance;
  temp = 1.0 / ((1.0 / (TEMPERATURENOMINAL + 273.15)) + (1.0 / bCoefficient) * log(resistance / nominalResistance)); // 1.0/( (1/To)+(1/B)*ln(R/Ro) )
  return (temp - 273.15);
}

double getTempTermistorNTCSteinhart(const uint16_t analogValue, const uint16_t serialResistance, const float a, const float b, const float c)
{
  float resistance, temp;

  // convert the value to resistance
  resistance = (serialResistance / ((float)analogValue)) * ADC_RESOLUTION - serialResistance;
  resistance = log(resistance);
  temp = 1.0 / (a + b * resistance + c * resistance * resistance * resistance);
  return (temp - 273.15);
}

void setup()
{
  IIKit.setup();
}

#define TIME_DELAY_MS1 1000 //Aguarda um segundo 
uint64_t previousTimeMS1 = 0;

void loop()
{
  IIKit.loop();
  const uint64_t currentTimeMS = millis();
  if ((currentTimeMS - previousTimeMS1) >= TIME_DELAY_MS1)
  {
    uint16_t adc = analogRead(def_pin_ADC1);
    float temperature1 = getTempTermistorNTCBeta(adc,                    // Analog Value
                                                 10000,                  // Nominal resistance at 25 ºC
                                                 3455,                   // thermistor's beta coefficient
                                                 10000);                 // Value of the series resistor
    float temperature2 = getTempTermistorNTCSteinhart(adc,               // Analog Value
                                                      10000,             // Value of the series resistor
                                                      0.001129241,       // a
                                                      0.0002341077,      // b
                                                      0.00000008775468); // c
    IIKit.WSerial.print(">Temp Beta: ");                                        // IMPRIME O TEXTO NO MONITOR SERIAL
    IIKit.disp.setText(2, ("TB:" + String(temperature1)).c_str());
    IIKit.WSerial.println(temperature1);                                        // IMPRIME NO MONITOR SERIAL A TEMPERATURA MEDIDA
    IIKit.WSerial.print(">Temp Steinhart: ");                                   // IMPRIME O TEXTO NO MONITOR SERIAL
    IIKit.disp.setText(2, ("TS:" + String(temperature2)).c_str());
    IIKit.WSerial.println(temperature2);                                        // IMPRIME NO MONITOR SERIAL A TEMPERATURA MEDIDA
  }
}
