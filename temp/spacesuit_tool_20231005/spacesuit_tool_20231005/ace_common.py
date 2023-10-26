#!/usr/bin/env python3

"""SPACE protocol definitions common to all ACE thrusters.

The canonical reference for the commands is this design doc:
    https://docs.google.com/document/d/1ubxcPF__EAEKWYdPicY2YRF4y8Y2wsH61LEIfDUPw0E
"""

__copyright__ = "Copyright 2020, Apollo Fusion Inc."

import space


# Convenience abbreviation since we'll use it a lot
CMD = space.SpaceCommand


# Parameter identifiers
TRISTATE = space.IdentifierParser()
TRISTATE.add(0, 'off', aliases=('disable', 'disabled', 'dis', 'idle', '0'))
TRISTATE.add(1, 'on', aliases=('enable', 'enabled', 'en', 'active', '1'))
TRISTATE.add(0xFF, 'n/a', aliases=('?', 'unchanged', 'ignore', 'unknown', '-1'))

VALVE_ID = space.IdentifierParser()
VALVE_ID.add(0, 'latch0')
VALVE_ID.add(1, 'latch1')
VALVE_ID.add(16, 'nonlatch0', aliases=('momentary0', 'non0', 'mom0'))
VALVE_ID.add(17, 'nonlatch1', aliases=('momentary1', 'non1', 'mom1'))
VALVE_ID.add(18, 'nonlatch2', aliases=('momentary2', 'non2', 'mom2'))
VALVE_ID.add(19, 'nonlatch3', aliases=('momentary3', 'non3', 'mom3'))

VALVE_STATE = space.IdentifierParser()
VALVE_STATE.add(0, 'closed', aliases=('close', 'deenergize', 'deenergized'))
VALVE_STATE.add(1, 'open', aliases=('opened', 'energize', 'energized'))

UART_ID = space.IdentifierParser()
UART_ID.add(0, 'uart0')
UART_ID.add(1, 'uart1')
UART_ID.add(2, 'uart2')

# To avoid confusion, telemetry field IDs are universal across all products,
# even if some values are only relevant to particular variants.
TELEMETRY_ID = space.IdentifierParser()
TELEMETRY_ID.add(1, 'igniter_on', aliases=('ig_en',))
TELEMETRY_ID.add(2, 'lvps_voltage', aliases=('lvps_v',))
TELEMETRY_ID.add(3, 'lvps_duty')
TELEMETRY_ID.add(4, 'vbus_voltage', aliases=('vbus_v',))
TELEMETRY_ID.add(5, 'vbus_current', aliases=('vbus_a',))
TELEMETRY_ID.add(6, 'scrubber_sbe')
TELEMETRY_ID.add(7, 'scrubber_mbe')
TELEMETRY_ID.add(8, 'cpu_usage')
TELEMETRY_ID.add(9, 'cpu_delay')
TELEMETRY_ID.add(10, 'discharge_on')
TELEMETRY_ID.add(11, 'discharge_setpoint')
TELEMETRY_ID.add(12, 'discharge_period')
TELEMETRY_ID.add(13, 'discharge_voltage', aliases=('discharge_v',))
TELEMETRY_ID.add(14, 'discharge_cathode')
TELEMETRY_ID.add(15, 'discharge_current', aliases=('discharge_a',))
TELEMETRY_ID.add(16, 'thruster_state')
TELEMETRY_ID.add(17, 'thruster_attempts')
TELEMETRY_ID.add(18, 'discharge_current_mean')
TELEMETRY_ID.add(19, 'discharge_current_stddev')
TELEMETRY_ID.add(20, 'rtd1_discharge_q3', aliases=('rtd1', 'rtd_1_temp'))
TELEMETRY_ID.add(21, 'rtd2_discharge_q2', aliases=('rtd2', 'rtd_2_temp'))
TELEMETRY_ID.add(22, 'rtd3_discharge_q1', aliases=('rtd3', 'rtd_3_temp'))
TELEMETRY_ID.add(23, 'rtd4_discharge_transformer',
                 aliases=('rtd4', 'rtd_4_temp'))
TELEMETRY_ID.add(24, 'thruster_temp')
TELEMETRY_ID.add(25, 'cpu_temp')
TELEMETRY_ID.add(26, 'thrust_duration', aliases=('duration',))
TELEMETRY_ID.add(27, 'flow_control_current', aliases=('flow_c', 'pfcv'))
TELEMETRY_ID.add(30, 'valve_latching_0_on', aliases=('latch0',))
TELEMETRY_ID.add(31, 'valve_latching_1_on', aliases=('latch1',))
TELEMETRY_ID.add(32, 'valve_nonlatching_0_on', aliases=('nonlatch0',))
TELEMETRY_ID.add(33, 'valve_nonlatching_1_on', aliases=('nonlatch1',))
TELEMETRY_ID.add(34, 'tank_pressure', aliases=('tank_p',))
TELEMETRY_ID.add(35, 'plenum_pressure', aliases=('plenum_p',))
TELEMETRY_ID.add(36, 'feed_target_pressure', aliases=('feed_tar_p',))
TELEMETRY_ID.add(37, 'feed_target_current', aliases=('feed_tar_a',))
TELEMETRY_ID.add(38, 'valve_nonlatching_2_on', aliases=('nonlatch2',))
TELEMETRY_ID.add(39, 'valve_nonlatching_3_on', aliases=('nonlatch3',))
TELEMETRY_ID.add(40, 'adc_ain0')
TELEMETRY_ID.add(41, 'adc_ain1')
TELEMETRY_ID.add(42, 'adc_ain2')
TELEMETRY_ID.add(43, 'adc_ain3')
TELEMETRY_ID.add(44, 'adc_ain4')
TELEMETRY_ID.add(45, 'adc_ain5')
TELEMETRY_ID.add(46, 'adc_ain6')
TELEMETRY_ID.add(47, 'adc_ain7')
TELEMETRY_ID.add(50, 'adc_amux00')
TELEMETRY_ID.add(51, 'adc_amux01')
TELEMETRY_ID.add(52, 'adc_amux02')
TELEMETRY_ID.add(53, 'adc_amux03')
TELEMETRY_ID.add(54, 'adc_amux04')
TELEMETRY_ID.add(55, 'adc_amux10')
TELEMETRY_ID.add(56, 'adc_amux11')
TELEMETRY_ID.add(57, 'adc_amux12')
TELEMETRY_ID.add(58, 'adc_amux13')
TELEMETRY_ID.add(59, 'adc_amux14')
TELEMETRY_ID.add(60, 'valve_latching_0_time', aliases=('latch0_time',))
TELEMETRY_ID.add(61, 'valve_latching_1_time', aliases=('latch1_time',))
TELEMETRY_ID.add(62, 'valve_nonlatching_0_time', aliases=('nonlatch0_time',))
TELEMETRY_ID.add(63, 'valve_nonlatching_1_time', aliases=('nonlatch1_time',))
TELEMETRY_ID.add(64, 'valve_nonlatching_2_time', aliases=('nonlatch2_time',))
TELEMETRY_ID.add(65, 'valve_nonlatching_3_time', aliases=('nonlatch3_time',))
TELEMETRY_ID.add(70, 'edu_load_current', aliases=('load_a',))
TELEMETRY_ID.add(71, 'edu_load_power', aliases=('load_w',))
TELEMETRY_ID.add(72, 'edu_load_temp', aliases=('load_t',))
TELEMETRY_ID.add(73, 'edu_fan_on', aliases=('fan_on',))
# Some extra debugging telemetry fields.
TELEMETRY_ID.add(0xF0, 'zero')
TELEMETRY_ID.add(0xF1, 'forty_two')
TELEMETRY_ID.add(0xF2, 'time')

# By default a telemetry field is just a single floating-point value, but
# in general they can be more complex, so the parser can vary depending on
# the identifier.
TELEMETRY_FIELD = space.PairParser(TELEMETRY_ID, space.FloatParser())

CHANNEL_ID = space.IdentifierParser()
CHANNEL_ID.add(0, 'description')
CHANNEL_ID.add(1, 'console_input')
CHANNEL_ID.add(2, 'console_output')
CHANNEL_ID.add(3, 'space_command')
CHANNEL_ID.add(4, 'space_reply')

CHANNEL_ENABLE = space.PairParser(CHANNEL_ID, TRISTATE)

# Similiar to telemetry fields, we defined the health-check identifiers
# universally, even if not every product will have all of them.
HEALTH_ID = space.IdentifierParser()
HEALTH_ID.add(2, 'lvps_voltage', aliases=('lvps_v',))
HEALTH_ID.add(4, 'vbus_voltage', aliases=('vbus_v',))
HEALTH_ID.add(5, 'vbus_current', aliases=('vbus_a',))
HEALTH_ID.add(13, 'discharge_voltage', aliases=('discharge_v',))
HEALTH_ID.add(14, 'discharge_cathode')
HEALTH_ID.add(15, 'discharge_current', aliases=('discharge_a',))
HEALTH_ID.add(16, 'discharge_overcurrent')
HEALTH_ID.add(17, 'thruster_attempts')
HEALTH_ID.add(20, 'rtd_1_temp', aliases=('rtd1',))
HEALTH_ID.add(21, 'rtd_2_temp', aliases=('rtd2',))
HEALTH_ID.add(22, 'rtd_3_temp', aliases=('rtd3',))
HEALTH_ID.add(23, 'rtd_4_temp', aliases=('rtd4',))
HEALTH_ID.add(24, 'thruster_temp')
HEALTH_ID.add(25, 'cpu_temp')
HEALTH_ID.add(26, 'thrust_duration', aliases=('duration',))
HEALTH_ID.add(35, 'plenum_pressure')
HEALTH_ID.add(72, 'edu_load_temp', aliases=('load_t',))
HEALTH_ID.add(100, 'feed_valve')
HEALTH_ID.add(101, 'feed_ignited')
HEALTH_ID.add(102, 'cpu_rebooted', aliases=('boot',))
HEALTH_ID.add(103, 'config_error', aliases=('config',))
HEALTH_ID.add(0xFF, 'all')

# There is one common ID space for configuration parameters, even though
# we have separate commands for numeric and string getting/setting.
CONFIG_ID = space.IdentifierParser()
CONFIG_ID.add(1, 'serial_num', aliases=('serial',))
CONFIG_ID.add(2, 'hw_variant', aliases=('variant',))
CONFIG_ID.add(3, 'space_address', aliases=('address',))
CONFIG_ID.add(4, 'part_number', aliases=('part', 'part_num'))
CONFIG_ID.add(10, 'edu_load_disable')
CONFIG_ID.add(20, 'flow_ignition_amps')
CONFIG_ID.add(21, 'feed_ignition_amps')
CONFIG_ID.add(22, 'feed_ignition_psi')
CONFIG_ID.add(23, 'feed_delta_psi')
CONFIG_ID.add(24, 'feed_stddev_amps')
CONFIG_ID.add(30, 'plenum_0psi_volts')
CONFIG_ID.add(31, 'plenum_ref_volts')
CONFIG_ID.add(32, 'plenum_ref_psi')
CONFIG_ID.add(33, 'tank_0psi_volts')
CONFIG_ID.add(34, 'tank_ref_volts')
CONFIG_ID.add(35, 'tank_ref_psi')
CONFIG_ID.add(36, 'vbus_offset_amps')
CONFIG_ID.add(0xFF, 'all')

# List of commands to be registered
COMMANDS = [
  # Operational commands
  CMD(0x10, 'igniter', 0.002, space.FloatParser(), space.FloatParser()),
  CMD(0x12, 'discharge', 0.002, TRISTATE, TRISTATE),
  CMD(0x16, 'valve', 0.005,
      space.ListParser(space.PairParser(VALVE_ID, space.FloatParser())),
      space.ListParser(space.PairParser(VALVE_ID, VALVE_STATE))),
  CMD(0x18, 'flow', 0.002,
      space.ListParser(space.FloatParser(), max_length=1),
      space.FloatParser()),
  CMD(0x1A, 'thrust', 0.002,
      space.PairParser(TRISTATE,
                       space.ListParser(space.FloatParser(), max_length=4),
                       sep=' '),
      TRISTATE),
  CMD(0x1C, 'feedpres', 0.002, space.FloatParser(), space.FloatParser()),
  CMD(0x1E, 'feedcur', 0.002, space.FloatParser(), space.FloatParser()),

  # Telemetry commands
  CMD(0x20, 'tele', 0.005,
      space.ListParser(TELEMETRY_ID),
      space.ListParser(TELEMETRY_FIELD)),
  CMD(0x22, 'telexl', 0.020,
      space.ListParser(TELEMETRY_ID),
      space.ListParser(TELEMETRY_FIELD)),
  CMD(0x24, 'telefreq', 0.005,
      space.ListParser(TELEMETRY_FIELD),
      space.ListParser(TELEMETRY_FIELD)),
  CMD(0x26, 'telechan', 0.005,
      space.ListParser(CHANNEL_ENABLE),
      space.ListParser(CHANNEL_ENABLE)),
  CMD(0x28, 'telestart', 0.005,
      space.PairParser(UART_ID, space.IntegerParser(bits=32), sep=' '),
      space.PairParser(UART_ID, space.IntegerParser(bits=32), sep=' ')),
  CMD(0x2E, 'teleset', 0.020,
      space.ListParser(TELEMETRY_FIELD),
      space.ListParser(TELEMETRY_FIELD)),

  # Health-check commands
  CMD(0x30, 'henable', 0.020,
      space.ListParser(space.PairParser(HEALTH_ID, TRISTATE)),
      space.ListParser(HEALTH_ID)),
  CMD(0x32, 'htrip', 0.020,
      space.ListParser(HEALTH_ID),
      space.ListParser(space.PairParser(HEALTH_ID, space.FloatParser()))),
  CMD(0x34, 'hreset', 0.005,
      space.ListParser(HEALTH_ID),
      space.ListParser(HEALTH_ID)),
  CMD(0x36, 'hconfig', 0.005,
      space.PairParser(HEALTH_ID,
                       space.ListParser(space.FloatParser(), max_length=3),
                       sep=' '),
      space.PairParser(HEALTH_ID,
                       space.ListParser(space.FloatParser(), max_length=3),
                       sep=' ')),

  # Configuration commands
  CMD(0x40, 'cvalue', 0.020,
      space.PairParser(CONFIG_ID,
                       space.ListParser(space.FloatParser(), max_length=2),
                       sep=' '),
      space.PairParser(CONFIG_ID,
                       space.ListParser(space.FloatParser(), max_length=3),
                       sep=' ')),
  CMD(0x42, 'cstring', 0.020,
      space.PairParser(CONFIG_ID,
                       space.ListParser(space.StringParser(), max_length=2),
                       sep=' '),
      space.PairParser(CONFIG_ID,
                       space.ListParser(space.StringParser(), max_length=3),
                       sep=' ')),
  CMD(0x44, 'cerase', 0.005,
      CONFIG_ID,
      space.ListParser(CONFIG_ID, max_length=1)),

  # System commands
  CMD(0x02, 'sysver', 0.020, None, space.StringParser()),
  CMD(0x04, 'echo', 0.020,
      space.ListParser(space.ByteParser()),
      space.ListParser(space.ByteParser())),
  CMD(0x06, 'delay', 0.100, space.FloatParser(), space.FloatParser()),
  CMD(0x08, 'sysreset', 0.002, space.FloatParser(), space.FloatParser()),
  CMD(0x0A, 'syspeek', 0.020,
      space.PairParser(space.IntegerParser(bits=32),
                       space.ByteParser(), sep=' '),
      space.PairParser(space.IntegerParser(bits=32),
                       space.ListParser(space.ByteParser()), sep=' ')),
  CMD(0x0C, 'syspoke', 0.020,
      space.PairParser(space.IntegerParser(bits=32),
                       space.ListParser(space.ByteParser()), sep=' '),
      space.PairParser(space.IntegerParser(bits=32),
                       space.ByteParser(), sep=' ')),
  ]


if __name__ == '__main__':
  print("This library isn't intended to be run directly.")
