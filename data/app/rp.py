#Router Power
#Naming Convention: Router Serial Number - Sensor Name
#i.e: 192F10E882C7-INA260
import time
import board
import adafruit_ina260

class INA260Router:
	def __init__(self):
		i2c = board.I2C()  # Setup I2C connection
		self.ina260 = adafruit_ina260.INA260(i2c, address=0x40)  # Initialize INA260 sensor for router

	def get_current_amps(self):
		return round(self.ina260.current / 1000, 2)  # Convert mA to A and round

	def get_voltage_volts(self):
		return round(self.ina260.voltage, 1)

	def get_power_watts(self):
		return round(self.ina260.power / 1000, 1)  # Convert mW to W and round

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

	def rp_test(self):
		for i in range(5):
			current_A = self.get_current_amps()
			voltage_V = self.get_voltage_volts()
			power_W = self.get_power_watts()
			print(f"Router Power- Current: {current_A} A, Voltage: {voltage_V} V, Power: {power_W} W")
			time.sleep(5)
	

#Poll sensor every 30 seconds
#Only save changes in the data
#What should I do to handle extreme values such as power loss?
