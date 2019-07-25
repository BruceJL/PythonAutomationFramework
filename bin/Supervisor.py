#!/usr/bin/python3

import os
import sys
sys.path.insert(0, os.getcwd())

import logging
from logging.handlers import RotatingFileHandler
import signal

import inspect
import threading
from importlib import import_module
import ruamel
from rpyc.utils.server import ThreadedServer
from typing import List, Dict

import pyAutomation
from pyAutomation.DataObjects.Alarm import Alarm
from pyAutomation.Supervisory.AlarmHandler import AlarmHandler
from pyAutomation.Supervisory.SupervisedThread import SupervisedThread
from pyAutomation.Supervisory.PointManager import PointManager
from pyAutomation.Supervisory.AlarmNotifier import AlarmNotifier
from pyAutomation.Supervisory.RpcServer import RpcServer

# build the formatter
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(module)s.%(funcName)s() - %(message)s')

logger_supervisory = None


class Supervisor(object):

    def __init__(self, logic: str, point_database: str) -> None:

        #load the point database.

        self.threads = []  # type: List[SupervisedThread]
        PointManager().load_points(point_database)

        yml = ruamel.yaml.YAML(typ='safe', pure=True)
        yml.default_flow_style = False
        yml.indent(sequence=4, offset=2)

        # open the supplied logic yaml file.
        with open(logic, 'r') as ymlfile:
            cfg = yml.load(ymlfile)

        # Import all the loggers
        section = "loggers"
        for logger in cfg[section]:
            # self.logger.info("attempting to create logger: " + logger)
            # setup the device logger
            l = logging.getLogger(logger)
            l.setLevel(cfg[section][logger]['level'])
            fh = RotatingFileHandler(
              filename = cfg[section][logger]['file'],
              maxBytes=cfg[section][logger]['maxBytes'],
              backupCount=cfg[section][logger]['backupCount'],
              encoding=None,
              delay=False)
            fh.setFormatter(formatter)
            l.addHandler(fh)

        self.logger = logging.getLogger('supervisory')
        PointManager().logger = self.logger

        # Setup the alarm notifiers.
        section = "AlarmNotifiers"
        for notifier in cfg[section]:
            self.logger.info("attempting import AlarmNotifier " + notifier)

            imported_module = import_module(
              cfg[section][notifier]["module"],
              cfg[section][notifier]["package"])

            assert 'logger' in cfg[section][notifier], \
              "No logger entry defined for " + notifier
            logger = cfg[section][notifier]["logger"]

            for i in dir(imported_module):
                attribute = getattr(imported_module, i)
                if    inspect.isclass(attribute) \
                  and issubclass(attribute, AlarmNotifier) \
                  and attribute != AlarmNotifier:
                    concrete_notifier = attribute(
                      name=notifier,
                      logger=logger)
                    self.logger.info("adding " + imported_module.__name__ +  " "
                      + str(attribute) + " to alarm notifiers list" )
                    Alarm._get_notifiers().append(concrete_notifier)

                    # Populate module assign_parameters
                    PointManager().assign_parameters(
                      d = cfg[section][notifier],
                      target = concrete_notifier)

        self.logger.info("Starting Supervisor")

        # Create the signleton alarm handler thread.
        # The alarm handler is not an option.
        self.alarm_handler = AlarmHandler(
            name="alarm processer",
            logger="supervisory"
        )

        Alarm.set_alarm_handler(self.alarm_handler)
        self.threads.append(self.alarm_handler)

        # Create all of the custom threads.
        section = 'SupervisedThreads'
        for thread_name in cfg[section]:
            self.logger.info("attempting to import " + cfg[section][thread_name]["module"])
            imported_module = import_module(
              cfg[section][thread_name]["module"],
              cfg[section][thread_name]["package"])
            for i in dir(imported_module):
                attribute = getattr(imported_module, i)
                if    inspect.isclass(attribute) \
                  and issubclass(attribute, SupervisedThread) \
                  and attribute != SupervisedThread:
                    # Everything looks valid, import the instansiate the module.

                    concrete_thread = attribute(
                      name=thread_name,
                      logger=cfg[section][thread_name]["logger"]
                    )

                    self.logger.info("added " + thread_name +  " " + str(attribute))

                    # Populate module points
                    if 'points' in cfg[section][thread_name]:
                        for point_name in cfg[section][thread_name]['points']:
                            self.logger.info("assigning point " + point_name)
                            if 'access' in cfg[section][thread_name]['points'][point_name]:
                                db_rw = cfg[section][thread_name]['points'][point_name]['access']
                            else:
                                db_rw = None

                            assert 'name' in cfg[section][thread_name]['points'][point_name],\
                              "Couldn't find database point name field for " + thread_name + ": " + point_name
                            PointManager().assign_point(
                              target=concrete_thread,
                              object_point_name=point_name,
                              database_point_name=cfg[section][thread_name]['points'][point_name]['name'],
                              db_rw=db_rw
                            )

                    #populate module alarms
                    if 'alarms' in cfg[section][thread_name]:
                        for alarm_name in cfg[section][thread_name]['alarms']:
                            self.logger.info("assigning point " + alarm_name)
                            if 'access' in cfg[section][thread_name]['alarms'][alarm_name]:
                                db_rw = cfg[section][thread_name]['alarms'][alarm_name]['access']
                            else:
                                db_rw = None

                            PointManager().assign_point(
                              target=concrete_thread,
                              object_point_name=alarm_name,
                              database_point_name=cfg[section][thread_name]['alarms'][alarm_name]['name'],
                              db_rw=db_rw
                            )

                    # Populate module assign_parameters
                    PointManager().assign_parameters(
                      cfg[section][thread_name],
                      concrete_thread)

                    # Now that the points and parameters are assigned. Run any
                    # remaining configuration
                    if "config" in cfg[section][thread_name]:
                        config = cfg[section][thread_name]['config']
                    else:
                        config = None

                    concrete_thread.config(config=config)

            # Append the fully built module to the threads dict.
            self.threads.append(concrete_thread)

        # Fire up all the threads.
        for i in self.threads:
            self.logger.info("starting: " + i.name)
            i.start()

        # Start the point database server
        rpc_object = RpcServer()
        rpc_object.active_alarm_list = self.alarm_handler.active_alarm_list
        rpc_object.global_alarm_list = pyAutomation.DataObjects.Alarm.global_alarms
        rpc_object.point_dict = PointManager().get_global_points()
        rpc_object.thread_list = self.threads
        rpc_object.get_hmi_point = PointManager().get_hmi_point
        print(str(rpc_object.get_hmi_point))

        self.rpc_server = ThreadedServer(
          rpc_object,
          port=18861,
          logger=self.logger,
          protocol_config={"allow_public_attrs": True})

        self.rpc_server_thread = threading.Thread(target=self.rpc_server.start)
        self.rpc_server_thread.start()

        self.logger.info("Completed Supervisor setup")

    def exit(self):
        self.logger.info("Shutdown signal received.")
        # self.simulator_thread.quit()
        for t in self.threads:
            t.quit()

        self.rpc_server.close()

# run the supervisor.
s = Supervisor(logic=sys.argv[1], point_database = sys.argv[2])


# catch TERM and INT signals to cleanly stop the system.
def my_sigterm_handler(signal, fluff):
    s.exit()


signal.signal(signal.SIGTERM, my_sigterm_handler)
signal.signal(signal.SIGINT, my_sigterm_handler)