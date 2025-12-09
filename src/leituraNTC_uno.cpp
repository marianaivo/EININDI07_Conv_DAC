// This library works only with the following circuit topology
// Vcc---NTC---ADC---SERIES_RESISTOR---GND
#include <Arduino.h>
#define ADC_RESOLUTION 1023
#define TEMPERATURENOMINAL 25
#define NTC_PIN A5

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
  Serial.begin(115200); // INICIALIZA A SERIAL
  delay(1000);          // INTERVALO DE 1 SEGUNDO
}

#define TIME_DELAY_MS1 1000 //Aguarda um segundo 
uint64_t previousTimeMS1 = 0;

void loop()
{
  const uint64_t currentTimeMS = millis();
  if ((currentTimeMS - previousTimeMS1) >= TIME_DELAY_MS1)
  {
    uint16_t adc = analogRead(NTC_PIN);
    float temperature1 = getTempTermistorNTCBeta(adc,                    // Analog Value
                                                 10000,                  // Nominal resistance at 25 ºC
                                                 3455,                   // thermistor's beta coefficient
                                                 10000);                 // Value of the series resistor
    float temperature2 = getTempTermistorNTCSteinhart(adc,               // Analog Value
                                                      10000,             // Value of the series resistor
                                                      0.001129241,       // a
                                                      0.0002341077,      // b
                                                      0.00000008775468); // c
    Serial.print(">Temp Beta: ");                                        // IMPRIME O TEXTO NO MONITOR SERIAL
    Serial.println(temperature1);                                        // IMPRIME NO MONITOR SERIAL A TEMPERATURA MEDIDA
    Serial.print(">Temp Steinhart: ");                                   // IMPRIME O TEXTO NO MONITOR SERIAL
    Serial.println(temperature2);                                        // IMPRIME NO MONITOR SERIAL A TEMPERATURA MEDIDA
  }
}
