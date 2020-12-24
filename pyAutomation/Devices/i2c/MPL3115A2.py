# http://cache.freescale.com/files/sensors/doc/data_sheet/MPL3115A2.pdf

from .linuxi2c3 import IIC
from pyAutomation.Devices.i2c.i2cPrototype import i2cPrototype
from pyAutomation.Supervisory.PointHandler import PointHandler

# Freescale MPL3115A2 Barometer
ADDRESS = 0x60

# Register addresses
REG_SENSOR_STATUS_REGISTER = 0x00  # Read only
REG_PRESSURE_MSB = 0x01
REG_PRESSURE_MSB = 0x02
REG_PRESSURE_CSB = 0x03
REG_TEMPERATURE_MSB = 0x04
REG_TEMPERATURE_LSB = 0x05
REG_DR_STATUS = 0x06
REG_PRESSURE_DELTA_MSB = 0x07
REG_PRESSURE_DELTA_CSB = 0x08
REG_PRESSURE_DELTA_LSB = 0x09
REG_TEMPERATURE_DELTA_MSB = 0x0A
REG_TEMPERATURE_DELTA_LSB = 0x0B
REG_DEVICE_IDENTIFIER = 0x0C
REG_FIFO_STATUS = 0x0D
REG_FIFO_DATA = 0x0E
REG_FIFO_SETUP = 0x0F  # ReadWrite
REG_TIME_DLEAY = 0x10  # Time since FIFO overflow
REG_SYSTEM_MODE = 0x11  # System mode register
REG_INT_SOURCE = 0x12
REG_PT_DATA_CONFIG = 0x13

REG_CONTROL_1 = 0x26    # Modes, Over-sampling
REG_CONTROL_2 = 0x27    # Aquisition Time Step
REG_CONTROL_3 = 0x28    # Interrupt Pin Configuration
REG_CONTROL_4 = 0x29    # Interrupt Enables
REG_CONTROL_5 = 0x30    # Interrupt output pin assignment


class MPL3115A2(i2cPrototype, PointHandler):

    _points_list = {
      'point_pressure':    {'type': 'PointAnalog', 'access': 'rw'},
      'point_temperature': {'type': 'PointAnalog', 'access': 'rw'},
    }

    parameters = {}

    def __init__(self, name: str,  bus: int, logger: str) -> None:
        self.point_temperature = None
        self.point_pressure = None
        self.temperature_val = -999
        self.pressure_val = -999

        self.bus = bus   # type: IIC
        self.dev = None  # type: int

        super().__init__(
          name=name,
          logger=logger)

    def reset(self):
        self.bus.write_byte_data(ADDRESS, REG_CONTROL_1, 0x04)  # 00111000

        # TODO: Fix the reset logic for here.
        # wait for reset to complete.
        # while(self.bus.read_byte(self.ADDRESS, self.REG_CONTROL,1) | 0x04):

        # self.setup()

    def setup(self):
        try:
            # ------------
            # bit 0 = SBYB
            # This bit is sets the mode to ACTIVE, where the system will make
            # measurements at periodic times based on the value of ST bits.
            #     Default value: 0 (STANDBY)
            #     0: Part is in STANDBY mode
            #     1: Part is ACTIVE
            bit_0 = 1

            # ------------
            # bit 1 = OST
            # OST bit will initiate a measurement immediately. If the SBYB bit
            # is set to active, setting the OST bit will initiate an immediate
            # measurement, the part will then return to acquiring data as per
            # the setting of the ST bits in CTRL_REG2. In this mode, the OST bit
            # does not clear itself and must be cleared and set again to
            # initiate another immediate measurement.

            # One Shot: When SBYB is 0, the OST bit is an auto-clear bit. When
            # OST is set, the device initiates a measurement by going into
            # active mode. Once a Pressure/Altitude and Temperature measurement
            # is completed, it clears the OST bit and comes back to STANDBY
            # mode. User shall read the value of the OST bit before writing to
            # this bit again
            bit_1 = 0

            # -----------
            # bit 2 = RST Software Reset. This bit is used to activate the
            # software reset. The Boot mechanism can be enabled in STANDBY and
            # ACTIVE mode. When the Boot bit is enabled the boot mechanism
            # resets all functional block registers and loads the respective
            # internal registers with default values. If the system was already
            # in STANDBY mode, the reboot process will immediately begin; else
            # if the system was in ACTIVE mode, the boot mechanism will
            # automatically transition the system from ACTIVE mode to STANDBY
            # mode, only then can the reboot process begin.

            # The I2C communication system is reset to avoid accidental
            # corrupted data access. At the end of the boot process the RST bit
            # is de-asserted to 0. Reading this bit will return a value of zero.

            # Default value: 0
            # 0: Device reset disabled
            # 1: Device reset enabled
            bit_2 = 0

            # -----------
            # bits 3-5 OS Oversample Ratio. These bits select the oversampling
            # ratio. Value is 2^OS. The default value is 000 for a ratio of 1.
            # 111 = 512ms sample time.
            bit_345 = 7

            # -----------
            # bit 6 RAW RAW output mode. RAW bit will output ADC data with no
            # post processing, except for oversampling. No scaling or offsets
            # will be applied in the digital domain. The FIFO must be disabled
            # and all other functionality: Alarms, Deltas, and other interrupts
            # are disabled.
            bit_6 = 0

            # -----------
            # bit 7 ALT
            # Altimeter-Barometer mode.
            # Default value: 0
            # 1: Part is in Altimeter Mode
            # 0: Part is in Barometer mode
            bit_7 = 0

            # Configures the #Freescale MPL3115A2 to work in polled mode.
            # REG_CONTROL_1 = 0x38 = 0011 1000
            byte = \
                bit_7 << 7 \
              | bit_6 << 6 \
              | bit_345 << 3 \
              | bit_2 << 2 \
              | bit_1 << 1 \
              | bit_0
            self.dev = IIC(ADDRESS, self.bus)
            self.dev.i2c(byte, REG_CONTROL_1, byte)

            # -----------
            # bit 0 TDEFE Data event flag enable on new Temperature data.
            # Default value: 0 0: Event detection disabled 1: Raise event flag
            # on new Temperature data
            #
            # -----------
            # bit 1 PDEFE Data event flag enable on new Pressure/Altitude data.
            # Default value: 0 0: Event detection disabled 1: Raise event flag
            # on new Pressure/Altitude data
            #
            # -----------
            # bit 2 DREM Data ready event mode. If the DREM bit is set logic 1
            # and one or more of the data ready event flags (PDEFE, TDEFE) are
            # enabled, then an event flag will be raised upon change in state of
            # the data. If the DREM bit is cleared logic 0 and one or more of
            # the data ready event flags are enabled, then an event flag will be
            # raised whenever the system acquires a new set of data.

            # Default value: 0.
            #     0: Event detection disabled
            #     1: Generate data ready event flag on new Pressure/Altitude or
            #     Temperature data

            self.bus.write_byte_data(
              self.ADDRESS,
              self.REG_PT_DATA_CONFIG,
              0x00,
            )

            self.is_setup = True

        except Exception as e:
            self.is_setup = False

        finally:
            if self.dev is not None:
                self.dev.close()
            return self.is_setup

    def read_data(self):

        try:
            drStatus= self.bus.read_byte_data(
              self.ADDRESS,
              self.REG_SENSOR_STATUS_REGISTER,
            )

            if drStatus & 0x04:  # new Pressure data is ready to be read
                OUT_P_MSB = self.bus.read_byte_data(
                  self.ADDRESS,
                  self.REG_PRESSURE_MSB,
                )

                OUT_P_CSB = self.bus.read_byte_data(
                  self.ADDRESS,
                  self.REG_PRESSURE_CSB,
                )

                OUT_P_LSB = self.bus.read_byte_data(
                  self.ADDRESS,
                  self.REG_PRESSURE_LSB,
                )

                i = (OUT_P_MSB << 16 | OUT_P_CSB << 8 | OUT_P_LSB)
                self.point_pressure.raw_value = i/64

            if drStatus & 0x02:  # new Temperature data is ready to be read
                OUT_T_MSB = self.bus.read_byte_data(
                  self.ADDRESS,
                  self.REG_TEMPERATURE_MSB,
                )

                OUT_T_LSB = self.bus.read_byte_data(
                  self.ADDRESS,
                  self.REG_TEMPERATURE_LSB,
                )

                i = OUT_T_MSB << 8 | OUT_T_LSB
                self.point_temperature.raw_value = i / 256
            self.alarm_comm_fail.reset()

        except OSError as e:
            self.logger.warn("Communication fault: " + str(e))
            self.alarm_comm_fail.activate()

        finally:
            if self.alarm_comm_failla.active:
                self.point_pressure.quality = False
                self.point_temperature.quality = False

    def write_data(self):
        return 0

    def get_remaining_states(self):
        return 0

    def config(self):
        self.device_points = [
            self.point_pressure,
            self.point_temperature]
