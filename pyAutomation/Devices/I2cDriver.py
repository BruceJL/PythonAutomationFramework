# This thread is the only thread allowed to write to the i2c bus.

from datetime import datetime
from datetime import timedelta
import traceback
from importlib import import_module
import inspect
from pyAutomation.Devices.i2c.i2cPrototype import i2cPrototype
from pyAutomation.Supervisory.SupervisedThread import SupervisedThread
from pyAutomation.Supervisory.PointManager import PointManager


class I2cDriver(SupervisedThread):

    parameters = {
      'bus': 'int',
    }

    def __init__(self, name, logger):
        self.devices = []
        self.min_sleep_time = timedelta(milliseconds=10)
        self.bus = None
        self.period = None
        self.current_read_device = None

        super().__init__(
          name=name,
          logger=logger,
          loop=self.loop,
          period=self.period)

    def config(self, config: dict):
        self.logger.debug("Entering function")

        for device in config:
            self.logger.info("I2C: attempting to import " + device)
            imported_module = import_module(
              config[device]["module"],
              config[device]["package"])

            for i in dir(imported_module):
                attribute = getattr(imported_module, i)
                if inspect.isclass(attribute) \
                  and issubclass(attribute, i2cPrototype) \
                  and attribute != i2cPrototype:

                    device_instance = attribute(
                      name=device,
                      logger=config[device]["logger"],
                      bus=int(self.bus)
                    )

                    # Assign points to the module.
                    PointManager().assign_points(
                      data=config[device],
                      target=device_instance,
                      target_name=device,
                      thread=self,
                    )

                    # Populate module parameters.
                    PointManager().assign_parameters(
                      target=device_instance,
                      data=config[device])

                    device_instance.config()
                    self.devices.append(device_instance)

        for d in self.devices:
            for p in d.interrupt_points:
                p.add_observer(self.name, self)

        self.current_read_device = self.devices[0]

    def loop(self):
        self.logger.debug("Entering function")

        now = datetime.now()
        device_to_run = None
        longest_wait_time = timedelta.min

        for device in self.devices:
            if device.is_setup and device.has_write_data:
                # data writes get pushed to the front of the queue by 1 second.
                i = now - device.last_io_attempt + timedelta(seconds=1)
                if i > longest_wait_time:
                    longest_wait_time = i
                    device_to_run = device

        # check and see if the next device to read is ready.
        if self.current_read_device.next_update is not None:
            if self.current_read_device.next_update <= now:
                i = now - self.current_read_device.last_io_attempt
                if i > longest_wait_time:
                    device_to_run = self.current_read_device

        if device_to_run is not None:
            self.logger.debug("doing I/O for %s", device_to_run.name)
            try:
                device_to_run.last_io_attempt = datetime.now()
                if not device_to_run.is_setup:
                    device_to_run.setup()
                if device_to_run.is_setup:
                    if device_to_run.has_write_data:
                        device_to_run.write_data()
                    else:
                        device_to_run.read_data()
                else:
                    # the setup failed. Cool down for a few seconds
                    t = datetime.now() + timedelta(seconds=5.0)
                    self.logger.error(
                      " %s can't be setup. Delaying until %s",
                      device_to_run.name, str(t))
                    device_to_run.delay_until = t

            except Exception as e:
                self.logger.error(traceback.format_exc())
                self.logger.error("Shutting down %s", device_to_run.name)
                self.devices.remove(device_to_run)

        # Figure out which device will be read next.
        next_read_time = datetime.max  # The earliest next read time
        longest_wait_time = timedelta.min  # the longest time that a device has been waiting.
        device_next_read = None

        for device in self.devices:
            i = device.next_update
            if i is not None:

                # if i is in the past, then pick the device that's been waiting the longest.
                if i < now:
                    i = now - device.last_io_attempt
                    if i > longest_wait_time:
                        longest_wait_time = i
                        device_next_read = device
                        next_read_time = now

                # if i is in the future, select the shortest wait time among the devices
                elif i < next_read_time:
                    next_read_time = i
                    device_next_read = device

        if device_next_read is not None:
            self.current_read_device = device_next_read
        self.logger.debug(self.current_read_device.name + " will be read at "
          + str(next_read_time))

        if next_read_time != datetime.max:
            sleep_time = next_read_time - datetime.now()
        else:
            sleep_time = timedelta(seconds=5)

        # Looks like we're all done. Check if we're done writing
        # before we go to sleep.
        for device in self.devices:
            if device.has_write_data:
                return 0

        if sleep_time > self.min_sleep_time:
            self.logger.debug("Sleeping " + str(sleep_time.total_seconds()))
            return sleep_time.total_seconds()
        else:
            self.logger.debug("Not Sleeping")
            return 0
