#Temperature/Humidity
#Naming Convention: Rpi Serial Number - Sensor Name
#i.e: 10000000357d707e-AHT10
import time
import smbus2

class AHT10:
    def __init__(self, i2c_bus=1, address=0x38):
        """Initialize AHT10 sensor with given I2C bus and address."""
        self.bus = smbus2.SMBus(i2c_bus)
        self.address = address
        self.init_sensor()

    def init_sensor(self):
        """Send initialization command to the AHT10 sensor."""
        self.bus.write_i2c_block_data(self.address, 0xE1, [0x08, 0x00])
        time.sleep(0.02)

    def read_humidity(self):
        """Read humidity data from the AHT10 sensor."""
        data = self._read_raw_data()
        return round(((data[1] << 12) | (data[2] << 4) | (data[3] >> 4)) * 100 / 1048576, 1)

    def read_temperature(self):
        """Read temperature data from the AHT10 sensor in Fahrenheit."""
        data = self._read_raw_data()
        temperature_c = (((data[3] & 0x0F) << 16) | (data[4] << 8) | data[5]) * 200 / 1048576 - 50
        return round(temperature_c * 9 / 5 + 32, 1)

    def _read_raw_data(self):
        """Fetch raw data from the AHT10 sensor."""
        self.bus.write_i2c_block_data(self.address, 0xAC, [0x33, 0x00])
        time.sleep(5)
        return self.bus.read_i2c_block_data(self.address, 0x00, 6)
    
    def print_measurements(self):
        while True:
            try:
                current_T = self.read_temperature()
                current_H = self.read_humidity()
                print(f"Current Temp.: {current_T} F, Current Hum.: {current_H}%")
                time.sleep(3)
            except OSError:
                print("Failed to read sensor data. Check the sensor connection.")
                break
    def env_test(self):
        for i in range(5):
            current_T = self.read_temperature()
            current_H = self.read_humidity()
            print(f"Current Temp.: {current_T} F, Current Hum.: {current_H}%")
            time.sleep(5)
            
            
#Poll sensor every minute
#Only save changes in the data
#Hard code function to turn on the fan if over 100 F