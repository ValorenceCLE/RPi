#System Power
#Naming Convention: Rpi Serial Number - Sensor Name
#i.e: 10000000357d707e-INA260
import time
import board
import adafruit_ina260

class INA260System:
    def __init__(self):
        i2c = board.I2C()  # Setup I2C connection
        self.ina260 = adafruit_ina260.INA260(i2c, address=0x42)  # Initialize INA260 sensor (Make sure the address is correct for the system sensor {Not Installed yet})

    def get_current_amps(self):
        # Get current in Amps, with one decimal place
        return round(self.ina260.current / 1000, 3)  # Convert mA to A and round

    def get_voltage_volts(self):
        # Get voltage in Volts, with one decimal place
        return round(self.ina260.voltage, 2)

    def get_power_watts(self):
        # Get power in Watts, with one decimal place
        return round(self.ina260.power / 1000, 2)  # Convert mW to W and round

    def print_measurements(self):
        while True:
            try:
                current_A = self.get_current_amps()
                voltage_V = self.get_voltage_volts()
                power_W = self.get_power_watts()
                print(f"Current: {current_A} A, Voltage: {voltage_V} V, Power: {power_W} W")
                time.sleep(3)
            except OSError:
                print("Failed to read sensor data. Check the sensor connection.")
                break
            
#Poll sensor every 30 seconds
#Only save changes in the data
#What should I do to handle extreme values such as power loss?

#This script is going to detect main power loss so it needs to be able to send actions to other services if that happens so the script can send a final message before it goes down
