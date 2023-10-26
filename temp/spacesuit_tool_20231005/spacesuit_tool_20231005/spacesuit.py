#!/usr/bin/env python3

"""Command-line utility for sending SPACE protocol messages.

SPACESUIT: Serial Protocol for ACE Scriptable User Interface Tool

This can send individual commands from the command line, can execute scripted
commands from an input file, or can drop into an interactive mode to send
user-typed commands. It saves the commands and replies into a timestamped
log file, which can later be replayed as a script input file.

In addition, this may be used as a library to facilitate more complex
command scripts. The typical pattern would look like:

   import spacesuit

   parser = spacesuit.get_arg_parser()
   # Possibly add your own additional command-line options.
   arguments = parser.parse_args()
   protocol = spacesuit.get_protocol(arguments)
   for command in my_script:
     protocol.run_line(command)
   last_value = protocol.telemetry(my_field)

This tool supports a macro file for abbreviating complex commands or sequences
of commands. The format just uses simple whitespace indents:

   macro 1
     command a
     command b
   macro 2
     command c
"""

__copyright__ = "Copyright 2020, Apollo Fusion Inc."

import argparse
import glob
import os.path
import re
import readline  # modifies the behavior of input() to have line history
import sys
import time
import traceback

import ace_max
import ace_radhard
import space


# Information printed by the interactive help command.
COMMAND_HELP = {
  'igniter': """Igniter control
Syntax: igniter [duration in seconds]
Activates the igniter circuit for the given time interval. Subsequent
commands will override previous ones, so an activation may be terminated
by sending a duration of 0.""",

  'discharge': """Discharge control
Syntax: discharge [on/off]
Starts or stops the discharge controller with the currently-configured
(default) parameters. If a health condition prevents attempting startup,
the reply will be 'off' instead of mirroring the request.""",

  'thrust': """Thruster high-level control
Syntax: thrust [on/off] [current] [pressure] [empty time] [fill time]
This performs all the necessary steps to run the thruster: pressurizing the
plenum, turning on the discharge converter, triggering the igniter, and
regulating the thrust. The four optional parameters are:

   current: the discharge current setpoint, which controls the thrust
   pressure: the setpoint for the initial plenum pressurization (or 0 to
     skip this control loop)
   empty time: if provided, vent the plenum contents first for this interval
     to start from a better known pressure state
   fill time: if provided, fill the plenum first with a pulse of this interval,
     in the case where the pressure sensor might be problematic""",

  'tele': """Retrieve telemetry fields
Syntax: tele [field 1] ... [field N]
This returns the current value of one or more numeric telemetry fields.
The list of known fields is:

  adc_ain0: volts
  adc_ain1: volts
  adc_ain2: volts
  adc_ain3: volts
  adc_ain4: volts
  adc_ain5: volts
  adc_ain6: volts
  adc_ain7: volts
  adc_amux00: volts
  adc_amux01: volts
  adc_amux02: volts (uncalibrated)
  adc_amux03: volts
  adc_amux04: volts
  adc_amux10: volts
  adc_amux11: volts
  adc_amux12: volts (uncalibrated)
  adc_amux13: volts
  adc_amux14: volts
  cpu_delay: seconds
  cpu_temp: degrees C
  cpu_usage: CPU utilization (0.0-1.0)
  discharge_cathode: volts
  discharge_current: output amps
  discharge_current_mean: output amps, filtered
  discharge_current_stddev: output amps variation
  discharge_on: active (1) or inactive (0)
  discharge_period: PWM half-period in timer clock ticks
  discharge_setpoint: target volts
  discharge_voltage: anode-cathode volts
  edu_load_current: simulated-load amps
  edu_load_power: simulated-load watts
  edu_load_temp: heatsink degrees C
  edu_fan_on: active (1) or inactive (0)
  feed_target_current: discharge current setpoint, amps
  feed_target_pressure: plenum pressure setpoint, PSIA
  flow_control_current: proportional flow-control valve current, amps
  igniter_on: active (1) or inactive (0)
  lvps_voltage: low-voltage power supply volts
  lvps_duty: low-voltage power supply PWM duty cycle (0.0-1.0)
  plenum_pressure: PSIA
  rtd1_discharge_q3: degrees C
  rtd2_discharge_q2: degrees C
  rtd3_discharge_q1: degrees C
  rtd4_discharge_transformer: degrees C
  scrubber_sbe: single-bit memory error count
  scrubber_mbe: multi-bit memory error count
  tank_pressure: PSIA
  thrust_duration: seconds
  thruster_attempts: count
  thruster_state: enum
  thruster_temp: degrees C
  valve_latching_0_on: active (1) or inactive (0)
  valve_latching_0_time: cumulative activation seconds
  valve_latching_1_on: active (1) or inactive (0)
  valve_latching_1_time: cumulative activation seconds
  valve_nonlatching_0_on: active (1) or inactive (0)
  valve_nonlatching_0_time: cumulative activation seconds
  valve_nonlatching_1_on: active (1) or inactive (0)
  valve_nonlatching_1_time: cumulative activation seconds
  valve_nonlatching_2_on: active (1) or inactive (0)
  valve_nonlatching_2_time: cumulative activation seconds
  valve_nonlatching_3_on: active (1) or inactive (0)
  valve_nonlatching_3_time: cumulative activation seconds
  vbus_current: input power rail amps
  vbus_voltage: input power rail volts

There are also some special debugging fields:
  forty_two: the number 42.0
  time: seconds since system boot
  zero: the number 0.0""",

  'telexl': """Retrieve many telemetry fields
Syntax: telexl [field 1] ... [field N]
This has the same function as the 'tele' command, so see that for more
information. The only difference is that this has a longer deadline, so it can
be used to retrieve up to about 25 fields at once.""",

  'telefreq': """Send telemetry field in high-speed logging
Syntax: telefreq [field 1]=[frequency in Hz] ... [field N]=[frequency in Hz]
In addition to on-demand telemetry requests, designated data can be streamed
on a second serial port to capture high-speed behavior. This gives the maximum
sampling frequency for a given field (see 'help tele' for a list of fields).
A frequency of 0 will stop streaming that field.""",

  'telechan': """Send extra channels in high-speed logging
Syntax: telechan [channel 1]=[on/off] ... [channel N]=[on/off]
In addition to telemetry fields, the high-speed logging stream on the second
serial port can contain extra bulk data, like console output or copies of
SPACE packet traffic. The list of known channels is:

  console_input
  console_output
  space_command
  space_reply""",

  'telestart': """Start high-speed logging stream on a serial port
Syntax: telestart [serial ID] [baud rate]
This starts or restarts the high-speed logging stream, possibly taking over
the current SPACE interface. The list of known serial ports is:

  uart0: console / debug port
  uart1: default SPACE interface
  uart2: logging port / optional redundant SPACE interface""",

  'teleset': """Manually set a telemetry field value
Syntax: teleset [field 1]=[value 1] ... [field N]=[value N]
On EDU firmware versions, this command will override a telemetry field with a
manual value, which could cause a trip condition if out of range. Some fields
will retain the value over time, whereas others will be updated quickly.""",

  'valve': """Control feed-system valves
Syntax: valve [id 1]=[duration in seconds] ... [id N]=[duration]
This activates (opens) one or more valves for a specific time interval, then
returns each to the inactive (closed) state. Subsequent commands for a given
valve will override a previous one, and a duration of 0 will inactivate it
immediately. The list of known valve IDs is:

  latch0
  latch1
  nonlatch0
  nonlatch1
  nonlatch2
  nonlatch3""",

  'ping': """Send an empty SPACE packet
Syntax: ping
This just sends an empty packet to the PPU, with the expectation that it will
reply the same way in order to test the remote protocol.""",

  'echo': """Repeat the same packet data
Syntax: echo [byte 1] ... [byte N]
The PPU should reply with the same sequence of data bytes in the command
message, to test packets of different lengths.""",

  'delay': """Get a reply after a delay
Syntax: delay [interval in seconds]
This requests the PPU to pause for a time delay before sending a reply to
the command, in order to test the protocol deadline behavior. The command
has a deadline of 0.1 seconds, so delays larger than that should result in
no reply.""",

  'sysver': """Retrieve the firmware build version
Syntax: sysver
This returns a human-readable string describing the firmware target settings,
the git commit it was built from, and the build timestamp.""",

  'sysreset': """Request a system reset
Syntax: sysreset [delay in seconds]
The system will reboot at the end of the delay interval, unless superceded by
another sysreset command before then. A delay of 0 is immediate, and a negative
delay will cancel a pending reset.""",

  'henable': """Enable or disable health checks
Syntax: henable [id 1]=[on/off] ... [id N]=[on/off]
This enables or disables one or more selected health checks. The special ID
'all' may be used to select every check. The reply will contain a list of all
the currently enabled checks. The list of known checks is:

  all: special value matching every health check
  config_error
  cpu_rebooted
  cpu_temp
  discharge_cathode
  discharge_current
  discharge_overcurrent
  discharge_voltage
  edu_load_temp
  feed_ignited
  feed_valve
  lvps_voltage
  plenum_pressure
  rtd_1_temp
  rtd_2_temp
  rtd_3_temp
  rtd_4_temp
  thrust_duration
  thruster_attempts
  thruster_temp
  vbus_current
  vbus_voltage""",

  'htrip': """Retrieve health checks that have tripped
Syntax: htrip [id 1] ... [id N]
This queries for the status of particular health checks (or 'all'), returning
the value at which they exceeded their monitoring range, if they have. See
'henable' for the list of known checks.""",

  'hreset': """Resets the trip status of health checks
Syntax: hreset [id 1] .. [id N]
This resets the tripped status of particular health checks (or 'all'). It
returns a list of those checks whose status was reset, omitting those that
weren't actually tripped in the first place. See 'henable' for the list of
known checks.""",

  'hconfig': """Configures the monitoring range of a health check
Syntax: hconfig [id] [minimum value] [maximum value] [interval in seconds]
A health check trips when the monitored value exceeds an allowed range
consistently for a time interval. This command sets those parameters, or can
query for them if you only provide the ID. See 'henable' for the list of
known checks.""",

  'feedpres': """Sets the feed-system target plenum pressure
Syntax: feedpres [psia]
This enables the feed-system control loop, which actuates the tank valves
to maintain a target pressure in the plenum. A value of 0 stops the loop.""",

  'feedcur': """Sets the feed-system target discharge current
Syntax: feedcur [discharge current in amps]
This enables the feed-system control loop, which actuates the tank valves
to maintain a target discharge current. A value of 0 stops the loop. Note
that it is an operational error if the thruster is not ignited or the
plenum-thruster latching valve is not open to permit gas flow.""",

  'cvalue': """Updates a numeric configuration parameter
Syntax: cvalue [parameter ID] [live value] [local value]
The current value of the configuration parameter will be set to the live
value, if provided, and the nonvolatile override value will be set to the
local value, if provided. With no values, the command will just return the
live, default, and local values from the thruster. The known IDs are:

  edu_load_disable
  feed_delta_psi
  feed_ignition_amps
  feed_ignition_psi
  feed_stddev_amps
  flow_ignition_amps
  plenum_0psi_volts
  plenum_ref_volts
  plenum_ref_psi
  space_address
  tank_0psi_volts
  tank_ref_volts
  tank_ref_psi
  vbus_offset_amps""",

  'cstring': """Updates a string configuration parameter
Syntax: cstring [parameter ID] [live value] [local value]
The current value of the configuration parameter will be set to the live
value, if provided, and the nonvolatile override value will be set to the
local value, if provided. With no values, the command will just return the
live, default, and local values from the thruster. Note that strings must
be single- or double-quoted to distinguish them from identifiers, and can
have embedded spaces and some escape sequences. The known IDs are:

  hw_variant
  part_number
  serial_num""",

  'cerase': """Removes a nonvolatile configuration parameter override
Syntax: cerase [parameter ID]
If a configuration parameter has previously been stored in nonvolatile
memory, this command will remove that record, so it will return to its
default value at the next reboot. See cvalue and cstring for the lists of
known parameter IDs, and in addition this command supports the 'all'
identifier to initialize all of nonvolatile memory.""",

  'syspeek': """Reads data from memory or flash
Syntax: syspeek [address] [length]
This is a very low-level command which can inspect arbitrary memory locations
to read out variables or processor registers. The SPI FRAM is mapped to an
unused memory range starting at 0x80000000.""",

  'syspoke': """Writes data to memory or flash
Syntax: syspeek [address] [byte 1] ... [byte N]
This is a very low-level command which can write arbitrary memory locations
to modify variables or processor registers. It can also write to nonvolatile
storage to flash a new application binary or bootloader. The SPI FRAM is
mapped to an unused memory range starting at 0x80000000.""",

  'pause': """Introduces a local delay in scripts
Syntax: pause [interval in seconds]
This is a SPACESUIT-local macro to add a purposeful delay between scripted
commands. It does not actually send a command to the thruster.""",

  'flash': """Load a new application binary image
Syntax: flash [filename_crc.bin]
This is a special macro which uses a series of syspoke commands in order to
flash a new application binary to the non-volatile storage of the thruster.
It will reset the board afterward to run the new image.""",

  'flashboot': """Load a new bootloader binary image
Syntax: flashboot [filename.bin]
This is a special macro which uses a series of syspoke commands in order to
flash a new bootloader binary to the non-volatile storage of the thruster.
It will reset the board afterward to run the new image.""",

  'cload': """Upload a set of configuration parameters
Syntax: cload [filename.cfg]
This reads a file of configuration parameters which was originally saved by
csave, and uses the cvalue, cstring, and cerase commands to modify the state
of the thruster to match the snapshot file.""",

  'csave': """Save all configuration parameters to a file
Syntax: csave [filename.cfg]
This uses the cvalue and cstring commands to grab a snapshot of the state of
all the thruster's configuration parameters, saving them to a text file. The
file can be edited and later restored to a thruster via cload.""",
}


def device_address(string):
  """Parses and range-checks the device address command-line argument."""
  try:
    address = int(string)
    if not 0 <= address <= 15:
      raise ValueError
  except ValueError as err:
    raise argparse.ArgumentTypeError("Device address range is 0-15") from err
  return address


def get_arg_parser():
  """Return an argparse parser for processing the command-line arguments."""
  desc = "SPACESUIT: Serial Protocol for ACE Scriptable User Interface Tool"
  parser = argparse.ArgumentParser(description=desc)
  parser.add_argument('--port', '-p', action='store',
                      default='/dev/ttyUSB0',
                      help='serial port device to use')
  parser.add_argument('--address', '--addr', '-a', action='store',
                      type=device_address, default=5,
                      help='SPACE device address, range 0-15')
  parser.add_argument('--thruster', '-t', action='store',
                      choices=['ace_radhard', 'ace_max'],
                      default='ace_radhard',
                      help='thruster product name')
  parser.add_argument('--logname', '--log', '-l', action='store',
                      default='suit',
                      help='prefix for log filename')
  parser.add_argument('--macro_file', '--macro', '-m', action='store',
                      type=argparse.FileType('r'),
                      help='file containing script macro definitions')
  parser.add_argument('--debug', '-d', action='store_true',
                      help='output additional packet debugging information')
  return parser


class LoggingSpaceProtocol(space.SpaceProtocol):
  """Wrapper for the SPACE protocol which also logs all traffic.

  The log format includes timestamped commands and their replies, including
  status bytes. The log files can be replayed as scripts as well.

  It also captures any telemetry replies for easier querying.
  """

  STATUS_FLAGS = {
    0x80: 'SYSTEM_FAULT',
    0x40: 'OPERATIONAL_FAULT',
    0x20: '[reserved]',
    0x10: '[reserved]',
    0x08: '[reserved]',
    0x04: '[reserved]',
    0x02: 'THRUSTING',
    0x01: 'BUSY',
    0x00: 'IDLE',
  }

  def __init__(self, *args, log_prefix="", macro_dict=None, echo=False,
               **kwargs):
    super().__init__(*args, **kwargs)
    filename = f"{log_prefix}{self.timestamp()}.log"
    self.logfile = open(filename, 'w')
    self.macros = macro_dict if macro_dict is not None else {}
    self.echo = echo
    self.telemetry = {}

  def run_line(self, line, echo_input=True, logged=True):
    """Processes a line entered interactively or through a script file.

    It will be skipped if it's a comment, or executed if it's a command.
    """
    line = line.strip()
    if not line or line.startswith("#") or line.startswith("<"):
      return None  # comment or recorded output
    elif line.startswith(">"):
      line = line[1:].strip()
    if self.echo and echo_input:
      print(f"> {line}")
    if line in self.macros:
      if logged:
        self.logfile.write(f"# MACRO: {line}\n")
      return self.run_script(self.macros[line], logged=logged)
    elif line.startswith("pause "):
      try:
        delay = float(line[6:])
      except ValueError:
        raise space.ParseError(f"Cannot parse pause delay: {line[6:]}")
      if logged:
        self.logfile.write(f"# {self.timestamp()}\n")
        self.logfile.write(f"> pause {delay:g}\n\n")
      time.sleep(delay)
      if self.echo:
        print()
      return None
    elif line.startswith("flash "):
      if logged:
        self.logfile.write(f"# {self.timestamp()}\n")
        self.logfile.write(f"# {line}\n\n")
      try:
        data = open(line[6:], 'rb').read()
      except FileNotFoundError:
        raise space.SpaceError(f"Cannot find file: {line[6:]}")
      if len(data) < 64 * 1024 or len(data) >= (256 - 32) * 1024:
        raise space.SpaceError(f"Unexpected firmware file size: {len(data)}")
      # Firmware binaries have an embedded length and CRC32 checksum.
      length = int.from_bytes(data[32:36], "little", signed=False)
      crc = int.from_bytes(data[-4:], "little", signed=False)
      if length != len(data) - 4 or crc != self.crc32(data[:-4]):
        raise space.SpaceError("Invalid firmware checksum")
      address = 0x80008000  # 32KB offset in FRAM memory
      self.flash_binary(address, data, progress=self.echo, logged=logged)
      return self.run_line('sysreset 0.1', logged=logged)  # Reboot
    elif line.startswith("flashboot "):
      if logged:
        self.logfile.write(f"# {self.timestamp()}\n")
        self.logfile.write(f"# {line}\n\n")
      try:
        data = open(line[10:], 'rb').read()
      except FileNotFoundError:
        raise space.SpaceError(f"Cannot find file: {line[10:]}")
      if len(data) < 8 * 1024 or len(data) >= 32 * 1024:
        raise space.SpaceError(f"Unexpected bootloader file size: {len(data)}")
      address = 0x80000000  # Start of FRAM memory
      self.flash_binary(address, data, progress=self.echo, logged=logged)
      return self.run_line('sysreset 0.1', logged=logged)  # Reboot
    elif line.startswith("cload "):
      if logged:
        self.logfile.write(f"# {self.timestamp()}\n")
        self.logfile.write(f"# {line}\n\n")
      try:
        config = open(line[6:], 'r').read()
        self.load_config(config, logged=logged)
        return None
      except FileNotFoundError:
        raise space.SpaceError(f"Cannot find file: {line[6:]}")
    elif line.startswith("csave "):
      if logged:
        self.logfile.write(f"# {self.timestamp()}\n")
        self.logfile.write(f"# {line}\n\n")
      try:
        config = self.save_config(logged=logged)
        open(line[6:], 'w').write(config)
        return None
      except FileNotFoundError:
        raise space.SpaceError(f"Cannot write file: {line[6:]}")
    return self.send_text(line, logged=logged)

  def run_script(self, script_data, logged=True):
    """Processes a series of commands as read from a script file or macro."""
    try:
      for line in script_data.split('\n'):
        self.run_line(line, logged=logged)
      # An exception will abort the script loop at the bad command.
    except space.SpaceError as err:
      print(err)
      print("Script aborted.")

  @staticmethod
  def crc32(data, polynomial=0x82F63B78):
    """Calculates the specific CRC32 checksum used by firmware binaries."""
    crc = 0xFFFFFFFF
    for b in data:
      crc = crc ^ b
      for i in range(8):
        if crc & 0x01:
          crc = (crc >> 1) ^ polynomial
        else:
          crc >>= 1
    return crc ^ 0xFFFFFFFF

  def flash_binary(self, address, data, progress=False, logged=True):
    """Sends a series of syspoke commands to flash an app or bootloader."""
    PROGRESS_BAR = '[----1----2----3----4----5----6----7----8----9----]'
    PIECE_SIZE = 64  # Limited to 123 by maximum packet size
    orig_echo = self.echo
    self.echo = False  # Temporarily suppress command console output
    try:
      if progress:
        # TODO(edkeyes): Investigate the tqdm module, which was recommended as
        # a convenient progress-bar library.
        print('Flashing... ', end='')
        last_progress = 0
      for offset in range(0, len(data), PIECE_SIZE):
        piece = data[offset:offset + PIECE_SIZE]
        piece_str = ' '.join(str(x) for x in piece)
        command = f"syspoke 0x{address + offset:08x} {piece_str}"
        reply = self.run_line(command, logged=logged)
        expected = f"syspoke_ack {address + offset} {len(piece)}"
        if reply != expected:
          raise space.SpaceError(f"Unexpected syspoke reply: {reply}")
        if progress:
          new_progress = last_progress + len(piece)
          print(PROGRESS_BAR[last_progress * len(PROGRESS_BAR) // len(data):
                             new_progress * len(PROGRESS_BAR) // len(data)],
                end='')
          sys.stdout.flush()
          last_progress = new_progress
      if progress:
        print('  Done!\n')
    finally:
      self.echo = orig_echo  # Restore original console output mode

  def load_config(self, config, logged=True):
    """Parses a config file and writes the parameters to the thruster."""
    orig_echo = self.echo
    self.echo = False  # Temporarily suppress command console output
    try:
      for line in config.split('\n'):
        if not line or line.startswith('#'):
          continue
        match = re.match(r'(.*?): (.*?) \((.*?)(?: -> (.*))?\)$', line)
        if not match:
          raise space.SpaceError(f"Cannot parse line: {line}")
        print(line)
        if match.group(2).startswith('"') or match.group(2).startswith("'"):
          command = 'cstring'
        else:
          command = 'cvalue'
        command += f" {match.group(1)} {match.group(2)}"
        default = match.group(3)
        if match.group(4):
          command += f" {match.group(4)}"
        else:
          reply = self.run_line(f"cerase {match.group(1)}", logged=logged)
          if not reply or reply == 'cerase_ack ':
            # A blank identifier means the erase didn't happen.
            raise space.SpaceError(f"Error erasing {match.group(1)}")
        reply = self.send_message(self.parser.from_text(command)[0],
                                  logged=logged)
        if not reply:
          raise space.SpaceError(f"No reply to command: {command}")
        try:
          # Grab the default value from the reply to compare against.
          new_default = reply[1][1][1].to_text()
        except IndexError:
          raise space.SpaceError(f"Unexpected reply: {reply.to_text()}")
        if new_default != default:
          print(f"WARNING: {match.group(1)} default does not match.")
          print(f"  Config file value: {default}")
          print(f"  Thruster firmware: {new_default}")
        # TODO(edkeyes): Warning if the live or local value wasn't changed?
    finally:
      self.echo = orig_echo  # Restore original console output mode

  def save_config(self, logged=True):
    """Reads all thruster parameters and returns them as a config file."""
    orig_echo = self.echo
    self.echo = False  # Temporarily suppress command console output
    try:
      sysver = self.run_line("sysver", logged=logged)
      config = ("# SPACESUIT thruster configuration parameters snapshot\n" +
                f"# Created: {self.timestamp()}\n" +
                f"# {sysver}\n")
      # HACK: We shouldn't be peeking under the hood of the command definitions
      # like this, but there's not a good way to otherwise get a list of all
      # known configuration fields.
      # TODO(edkeyes): Expose this in some more principled way.
      cerase_code = self.parser.first_parser._label_to_code['cerase']
      config_fields = self.parser._second_parsers[cerase_code]._code_to_label
      for _, label in sorted(config_fields.items()):
        if label == 'all':
          continue
        # We don't know if the parameter is numeric or string, so we try both.
        command = self.parser.from_text(f"cvalue {label}")[0]
        reply = self.send_message(command, logged=logged)
        if not reply:
          # The thruster doesn't seem to know about this parameter, but that's
          # not necessarily a problem if we're supporting different products.
          # It could also be a sign of general communication problems, though.
          print(f"WARNING: no value for parameter: {label}")
          continue
        try:
          params = reply[1][1]  # after the message type and field ID
          if not params:
            # Missing values mean the parameter is known but the type is wrong,
            # so retry as a string.
            command = self.parser.from_text(f"cstring {label}")[0]
            reply = self.send_message(command, logged=logged)
            if not reply:
              raise space.SpaceError(f"No reply to command: {command}")
            params = reply[1][1]
        except IndexError:
          raise space.SpaceError(f"Unexpected reply: {reply.to_text()}")
        if len(params) == 2:
          line = f"{label}: {params[0].to_text()} ({params[1].to_text()})"
        elif len(params) == 3:
          line = (f"{label}: {params[0].to_text()} " +
                  f"({params[1].to_text()} -> {params[2].to_text()})")
        else:
          raise space.SpaceError(f"Unexpected reply: {reply.to_text()}")
        config += line + '\n'
        print(line)
      return config
    finally:
      self.echo = orig_echo  # Restore original console output mode

  @staticmethod
  def timestamp():
    """Returns an ASCII date and time suitable for logging."""
    seconds = time.time()
    milliseconds = int(seconds * 1000) % 1000
    # Basic ISO 8601 date-time format with fractional seconds.
    time_str = time.strftime("%Y%m%dT%H%M%S", time.gmtime(seconds))
    return f"{time_str}.{milliseconds:03d}Z"

  def status_label(self, status):
    """Returns a human-readable version of the status byte flags."""
    labels = []
    for mask, label in sorted(self.STATUS_FLAGS.items(), reverse=True):
      if mask and mask & status:
        labels.append(label)
    if not labels:
      labels.append(self.STATUS_FLAGS[0])
    return ','.join(labels)

  def send_message(self, command, logged=True, **kwargs):
    """Wrapper message function which also logs the command and reply."""
    if logged:
      self.logfile.write(f"# {self.timestamp()}\n")
      self.logfile.write(f"> {command.to_text()}\n")
    reply = super().send_message(command, **kwargs)
    if reply is not None:
      status = self.get_status()
      output = f"# Status: {status} ({self.status_label(status)})\n"
      output += f"< {reply.to_text()}\n\n"
      if len(reply) == 2 and reply[0].value in (0x21, 0x23):
        # This is a tele_ack or telexl_ack, so add all of the telemetry
        # values to our dict.
        for field in reply[1]:
          self.telemetry[field[0].label] = field[1].value
    else:
      output = "# No reply received\n\n"
    if logged:
      self.logfile.write(output)
    # The command will have already been printed by the caller.
    if self.echo:
      print(output, end="")
    return reply


def get_protocol(arguments, echo=False):
  """Returns an instance of the SPACE protocol from command-line arguments.

  If echo is True, the commands and their replies will be output to the
  console. The debug flag will also trigger this mode.
  """
  if arguments.thruster == 'ace_radhard':
    commands = ace_radhard.COMMANDS
  elif arguments.thruster == 'ace_max':
    commands = ace_max.COMMANDS
  else:
    assert False
  message_type_parser = space.IdentifierParser()
  for command in commands:
    message_type_parser.add(command.command_code, command.command_str)
    message_type_parser.add(command.reply_code, command.reply_str)
  message_parser = space.MessageParser(message_type_parser)
  for command in commands:
    message_parser.add(command.command_code, command.command_parser,
                       deadline=command.deadline)
    message_parser.add(command.reply_code, command.reply_parser)
  macros = {}
  if arguments.macro_file:
    current_key = None
    for line in arguments.macro_file:
      if line.startswith('#'):
        continue
      elif line.startswith(' ') or line.startswith('\t'):
        if current_key in macros:
          macros[current_key] += '\n' + line.strip()
        else:
          macros[current_key] = line.strip()
      else:
        current_key = line.strip()
  if arguments.debug:
    echo = True
  protocol = LoggingSpaceProtocol(arguments.port, arguments.address,
                                  message_parser, debug=arguments.debug,
                                  log_prefix=f"{arguments.logname}_",
                                  macro_dict=macros, echo=echo)
  return protocol


def tab_completer(text, state):
  """Tab completion of filenames for the various commands."""
  if ' ' not in text:
    return None
  command, path = text.split(' ', 1)
  if command not in ('flash', 'flashboot', 'cload', 'csave'):
    return None
  if '~' in path:
    path = os.path.expanduser(path)
  if os.path.isdir(path):
    path += '/'
  options = glob.glob(path + '*')
  if state < len(options):
    return f"{command} {options[state]}"
  return None


def main():
  """Main executable entry point.

  See get_arg_parser() above for more command-line arguments.
  """
  readline.parse_and_bind('tab: complete')
  readline.set_completer_delims('')  # Only consider a whole command
  readline.set_completer(tab_completer)
  parser = get_arg_parser()
  group = parser.add_mutually_exclusive_group(required=True)
  # TODO(edkeyes): In general it might be nice to be able to specify multiple
  # command and script options, and have them all execute in sequence. This
  # would probably require a custom argparse action to preserve the order.
  group.add_argument('--command', '--cmd', '-c', action='store',
                     help='SPACE command string to execute')
  group.add_argument('--script', '--scr', '-s', action='store',
                     type=argparse.FileType('r'),
                     help='log file containing SPACE commands to execute')
  group.add_argument('--interactive', '--int', '-i', action='store_true',
                     help='start interactive command prompt')
  # TODO(edkeyes): It might be useful to be able to read some options from
  # a config file instead of always needing to provide them.
  arguments = parser.parse_args()
  protocol = get_protocol(arguments, echo=True)

  # TODO(edkeyes): We probably should support some sort of script-local
  # metacommands, such as a 'pause' function to introduce delays, or even
  # a 'wait for telemetry field to be equal to X' loop.
  if arguments.command:
    try:
      protocol.run_line(arguments.command)
    except space.SpaceError as err:
      print(err)
  elif arguments.script:
    protocol.run_script(arguments.script.read())
  elif arguments.interactive:
    print("Enter 'quit' to exit. Type 'help' for more info.\n")
    while True:
      try:
        line = input("> ").strip()
      except EOFError:
        # User entered CTRL-D, an alternate means of quitting.
        break
      if not line:
        # A blank line used to quit the interactive mode, so we try to be
        # helpful to people who were accustomed to that.
        print("Enter 'quit' to exit. Type 'help' for more info.\n")
      elif line == 'quit':
        break
      elif line == 'telemetry':
        for field, value in sorted(protocol.telemetry.items()):
          print(f"{field}={value:g}")
        print()
      elif line == 'help':
        print("Known commands:")
        for command, help_text in sorted(COMMAND_HELP.items()):
          first_line, _ = help_text.split('\n', 1)
          print(f"  {command}: {first_line}")
        print("Type 'help [command]' for more info on each one.\n")
      elif line.startswith('help '):
        command = line[5:].strip()
        try:
          print(f"{COMMAND_HELP[command]}\n")
        except KeyError:
          print(f"Unknown command: {command}")
          print("Type 'help' for a list of known commands.\n")
      else:
        try:
          protocol.run_line(line, echo_input=False)
        except space.SpaceError as err:
          print(f"{err}\n")
        except Exception as err:
          # Record the commented-out exception in the logs.
          err_str = ''.join(traceback.format_exception(type(err), err,
                                                       err.__traceback__))
          err_str = '# ' + '\n# '.join(err_str.split('\n'))
          protocol.logfile.write(f"# Fatal error encountered:\n{err_str}\n")
          protocol.logfile.close()
          raise err


if __name__ == '__main__':
  main()
