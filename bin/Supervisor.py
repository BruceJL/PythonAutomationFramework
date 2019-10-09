#!/usr/bin/python3
import logging
from logging.handlers import RotatingFileHandler
import os
import sys
import signal
import argparse
import inspect
import threading
from importlib import import_module
from rpyc.utils.server import ThreadedServer
from typing import List, Dict
import ruamel

import pyAutomation
from pyAutomation.DataObjects.Alarm import Alarm
from pyAutomation.Supervisory.AlarmHandler import AlarmHandler
from pyAutomation.Supervisory.SupervisedThread import SupervisedThread
from pyAutomation.Supervisory.PointManager import PointManager
from pyAutomation.Supervisory.AlarmNotifier import AlarmNotifier
from pyAutomation.Supervisory.RpcServer import RpcServer

sys.path.insert(0, os.getcwd())


# build the formatter
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(module)s.%(funcName)s() - %(message)s')

logger_supervisory = None


class Supervisor(object):

    def __init__(
      self,
      logic_yaml_files: 'List[str]',
      point_database_yaml_files: 'List[str]') -> None:

        self.threads = []  # type: 'List[SupervisedThread]'

        yml = ruamel.yaml.YAML(typ='safe', pure=True)
        yml.default_flow_style = False
        yml.indent(sequence=4, offset=2)

        # open the supplied logic yaml file.
        for file in logic_yaml_files:
            with open(file, 'r') as ymlfile:
                cfg = yml.load(ymlfile)

        # Import all the loggers
        section = "loggers"
        for logger in cfg[section]:
            # self.logger.info("attempting to create logger: " + logger)
            # setup the device logger
            l = logging.getLogger(logger)
            l.setLevel(cfg[section][logger]['level'])
            fh = RotatingFileHandler(
              filename=cfg[section][logger]['file'],
              maxBytes=cfg[section][logger]['maxBytes'],
              backupCount=cfg[section][logger]['backupCount'],
              encoding=None,
              delay=False)
            fh.setFormatter(formatter)
            l.addHandler(fh)

        self.logger = logging.getLogger('supervisory')
        assert self.logger is not None, \
            "The logger didn't assign properly"
        PointManager.logger = self.logger

        # load the point database(s).
        for file in point_database_yaml_files:
            self.logger.info("loading file: " + file)
            PointManager().load_points(file)

        # Setup the alarm notifiers.
        section = "AlarmNotifiers"
        for notifier in cfg[section]:
            self.logger.info("attempting import AlarmNotifier %s ", notifier)

            imported_module = import_module(
              cfg[section][notifier]["module"],
              cfg[section][notifier]["package"])

<<<<<<< HEAD
            assert 'logger' in cfg[section][notifier], \
                "No logger entry defined for " + notifier
=======
>>>>>>> 623a1f6fd41b0b536a1d5328f0c6ec7260c98d3e
            logger = cfg[section][notifier]["logger"]

            for i in dir(imported_module):
                attribute = getattr(imported_module, i)

                # Search the file for an AlarmNotifier object.
                if    inspect.isclass(attribute) \
                  and issubclass(attribute, AlarmNotifier) \
                  and attribute != AlarmNotifier:

                    concrete_notifier = attribute(
                      name=notifier,
                      logger=logger)
<<<<<<< HEAD
                    self.logger.info(
                      "adding %s %s to alarm notifiers list",
                      imported_module.__name__ , str(attribute))

                    Alarm._get_notifiers().append(concrete_notifier)
=======
                    self.logger.info("adding " + imported_module.__name__ +  " "
                      + str(attribute) + " to alarm notifiers list" )
                    Alarm.alarm_notifiers.append(concrete_notifier)
>>>>>>> 623a1f6fd41b0b536a1d5328f0c6ec7260c98d3e

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

        Alarm.alarm_handler = self.alarm_handler
        self.threads.append(self.alarm_handler)

        # Create all of the custom threads.
        section = 'SupervisedThreads'
        for thread_name in cfg[section]:
            self.logger.info(
              "attempting to import %s",  cfg[section][thread_name]["module"])
            imported_module = import_module(
              cfg[section][thread_name]["module"],
              cfg[section][thread_name]["package"])
            for i in dir(imported_module):
                attribute = getattr(imported_module, i)

                # Search the file for the SupervisedThread object.
                if    inspect.isclass(attribute) \
                  and issubclass(attribute, SupervisedThread) \
                  and attribute != SupervisedThread:
                    # Everything looks valid, import the instansiate the module.

                    concrete_thread = attribute(
                      name=thread_name,
                      logger=cfg[section][thread_name]["logger"]
                    )

                    self.logger.info("added %s %s", thread_name, str(attribute))

                    # Populate module points
                    if 'points' in cfg[section][thread_name]:
                        for point_name in cfg[section][thread_name]['points']:
                            self.logger.info("assigning point %s", point_name)
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

                    # populate module alarms
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
            self.logger.info("starting: %s", i.name)
            i.start()

        # Start the point database server
        rpc_object = RpcServer()
        rpc_object.active_alarm_list = self.alarm_handler.active_alarm_list
        rpc_object.global_alarm_list = pyAutomation.DataObjects.Alarm.global_alarms
        rpc_object.point_dict = PointManager().get_global_points()
        rpc_object.thread_list = self.threads
        rpc_object.get_hmi_point = PointManager().get_hmi_point

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


parser = argparse.ArgumentParser(description='Start the pyAutomation system.')

parser.add_argument(
  '--points', '-p',
  action='store',
  nargs='+',
  help='yaml file(s) containing the points database for this system.',
)

parser.add_argument(
  '--logic', '-l',
  action='store',
  nargs='+',
  help='yaml files(s) containing the logic instances to be created for this '
  + 'system.',
)

args = parser.parse_args()


# run the supervisor.
s=Supervisor(
  logic_yaml_files=args.logic,
  point_database_yaml_files=args.points,
)


# catch TERM and INT signals to cleanly stop the system.
def my_sigterm_handler(signal, fluff):
    s.exit()


signal.signal(signal.SIGTERM, my_sigterm_handler)
signal.signal(signal.SIGINT, my_sigterm_handler)
