from pyAutomation.DataObjects.PointAbstract import PointAbstract
from pyAutomation.DataObjects.Point import Point
from pyAutomation.DataObjects.ProcessValue import ProcessValue
from pyAutomation.DataObjects.PointReadOnly import PointReadOnly
from pyAutomation.DataObjects.PointReadOnlyAbstract import PointReadOnlyAbstract
from pyAutomation.DataObjects.Alarm import Alarm

from pyAutomation.DataObjects.PointAnalog import PointAnalog
from pyAutomation.DataObjects.PointAnalogDual import PointAnalogDual
from pyAutomation.DataObjects.PointAnalogScaled import PointAnalogScaled
from pyAutomation.DataObjects.PointDiscrete import PointDiscrete
from pyAutomation.DataObjects.PointEnumeration import PointEnumeration
from pyAutomation.DataObjects.ProcessValue import ProcessValue
from pyAutomation.DataObjects.Alarm import Alarm
from pyAutomation.DataObjects.AlarmAnalog import AlarmAnalog

# import PointDatabase

import logging
import ruamel
import sys
from pathlib import Path

from typing import Dict

global_points = {}  # type: Dict[str, PointAbstract]
global_alarms = {}  # type: Dict[str, Alarm]
global_process = {}  # type: Dict[str, ProcessValue]


class PointManager:

    logger = None

    yml = ruamel.yaml.YAML(typ='safe', pure=True)
    yml.default_flow_style = False
    yml.register_class(PointAnalog)
    yml.register_class(PointAnalogDual)
    yml.register_class(PointAnalogScaled)
    yml.register_class(PointDiscrete)
    yml.register_class(PointEnumeration)
    yml.register_class(ProcessValue)
    yml.register_class(Alarm)
    yml.register_class(AlarmAnalog)

    @staticmethod
    def load_points(file: 'str') -> 'None':

        path = Path(file)
        data = None
        with path.open() as fp:
            data = PointManager().yml.load(fp)

        for k, o in data['points'].items():
            if \
                 isinstance(o, PointAbstract) \
              or isinstance(o, PointAnalogScaled) \
              or isinstance(o, PointAnalogDual) \
              or isinstance(o, ProcessValue):
                if k in global_points:
                    if isinstance(o, ProcessValue):
                        # ProcessValues get priority
                        global_points[k] = o
                else:
                    global_points[k] = o

            elif \
                 isinstance(o, Alarm) \
              or isinstance(o, AlarmAnalog):
                global_alarms[k] = o
                o.name = k

        # now that the dict is fully populated, setup all the point names.
        for k, o in global_points.items():
            print("setting name for " + k)
            o.config(k)

        for k, o in data['alarms'].items():
          if   isinstance(o, Alarm) \
            or isinstance(o, AlarmAnalog):
              global_alarms[k] = o
              o.config(k)

        #print("global alarms:")
        #print(str(global_alarms))

    @staticmethod
    def assign_parameters(d: Dict[str, str], target):
        if 'parameters' in d:
            for parameter_name in d['parameters']:

                assert parameter_name in target.parameters, \
                  "tried to add: " + parameter_name \
                  + " to " + target.name + " but it's not in the parameter list"

                parameter_value = d['parameters'][parameter_name]
                logging.info("assigning " + str(parameter_value) + " to " +
                  parameter_name + " in module " + target.name)

                target.__dict__[parameter_name] = parameter_value

    @staticmethod
    def get_global_points():
        return global_points

    @staticmethod
    def get_hmi_point(s: str) -> PointReadOnlyAbstract:
        return get_point_ro(s)

    @staticmethod
    def assign_point(
      target,
      object_point_name: str,
      database_point_name: str,
      db_rw: str) -> None:

        assert target.point_name_valid(object_point_name), \
          object_point_name + " is not a valid point for " + target.name

        # Determine the access level for this point.
        logic_rw = target.get_point_access(object_point_name)
        assert logic_rw is not None or db_rw is not None, \
          "Neither the config file or " + target.name + \
          " specfiy a access property for " + object_point_name

        if logic_rw is not None and db_rw is not None:
            assert logic_rw == db_rw, \
              " The config file and " + target.name + \
              " disagree on the r/w property for " + object_point_name
            rw = logic_rw

        elif db_rw is None:
            rw = logic_rw

        else:
            rw = db_rw

        type = target.get_point_type(object_point_name)

        if   'PointAnalog'      == type \
          or 'PointDiscrete'    == type \
          or 'PointEnumeration' == type \
          or 'PointAnalogDual'  == type \
          or 'ProcessValue'     == type:

            if 'rw' == rw:
              target.__dict__[object_point_name] = \
                get_point_rw(
                  point_name=database_point_name,
                  writer=target)

            elif 'ro' == rw:
                target.__dict__[object_point_name] = \
                  get_point_ro(
                    point_name=database_point_name)

        elif 'Alarm' == type:
            if 'rw' == rw:
                target.__dict__[object_point_name] = \
                  get_alarm_rw(
                    alarm_name=database_point_name,
                    writer=target)

            elif 'ro' == rw:
                target.__dict__[object_point_name] = \
                  get_alarm_ro(
                    alarm_name=database_point_name)

def get_point_rw(point_name, writer) -> PointAbstract:
    if 'None' != point_name:
    # skip conditions where no point is required e.g. I/O device with
    # spare channels.
        assert point_name in global_points,\
          "Cannot locate " + point_name + " in point database."
        p = global_points[point_name].get_readwrite_object()
        p.writer = writer
        return p

def get_point_ro(point_name: str) -> PointReadOnly:
    if 'None' != point_name:
    # skip conditions where no point is required e.g. I/O device with
    # spare channels.
        assert point_name in global_points
        return global_points[point_name].get_readonly_object()


def get_process_ro(point_name: str) -> ProcessValue:
    if 'None' != point_name:
        assert point_name in global_process
        return global_process[point_name].get_readonly_object()


def get_alarm_rw(alarm_name, writer) -> Alarm:
    if 'None' != alarm_name:
        a = global_alarms[alarm_name]
        a.writer = writer
        return global_alarms[alarm_name]


def get_alarm_ro(alarm_name) -> Alarm:
    if 'None' != alarm_name:
        return global_alarms[alarm_name]
