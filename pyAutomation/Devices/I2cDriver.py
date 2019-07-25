#! /usr/bin/python3
# This thread is the only thread allowed to write to the i2c bus.

import datetime
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
        self.min_sleep_time = datetime.timedelta(milliseconds=10)
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

                    if "address" in config:
                        address = config["address"]
                    else:
                        address = None

                    device_instance = attribute(
                      name=device,
                      logger=config[device]["logger"],
                      bus=int(self.bus))

                    if 'points' in config[device]:
                        for p in config[device]["points"]:
                            if "name" in config[device]["points"][p]:
                                if 'access' in config[device]["points"][p]:
                                    db_rw = config[device]["points"][p]['access']
                                else:
                                    db_rw = None

                                self.logger.info("assigning point: " + config[device]["points"][p]["name"] + " to " + p)
                                PointManager.assign_point(
                                  target=device_instance,
                                  object_point_name=p,
                                  database_point_name=config[device]["points"][p]["name"],
                                  db_rw=db_rw)

                    # Populate module parameter
                    PointManager().assign_parameters(
                      target=device_instance,
                      d=config[device])

                    device_instance.config()
                    self.devices.append(device_instance)

        for d in self.devices:
            for p in d.interrupt_points:
                p.add_observer(self.name, self)

        self.current_read_device = self.devices[0]

    def loop(self):
        self.logger.debug("Entering function")

        now = datetime.datetime.now()
        device_to_run = None
        longest_wait_time = datetime.timedelta.min

        for device in self.devices:
            if device.has_write_data:
                # data writes get pushed to the front of the queue by 1 second.
                i = now - device.last_io_attempt + datetime.timedelta(seconds=1)
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
            self.logger.debug("doing I/O for " + device_to_run.name)

            try:
                device_to_run.do_io()

            except Exception as e:
                self.logger.error(traceback.format_exc())
                self.logger.error("Shutting down " + device_to_run.name)
                self.devices.remove(device_to_run)

        # Figure out which device will be read next.
        next_read_time = datetime.datetime.max  # The earliest next read time
        longest_wait_time = datetime.timedelta.min  # the longest time that a device has been waiting.
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
        self.logger.debug(self.current_read_device.name + " will be read at " +
          str(next_read_time))

        if next_read_time != datetime.datetime.max:
            sleep_time = next_read_time - datetime.datetime.now()
        else:
            sleep_time = datetime.timedelta(seconds=5)

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
