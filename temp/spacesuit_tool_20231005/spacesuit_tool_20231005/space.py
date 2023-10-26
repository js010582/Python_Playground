#!/usr/bin/env python3

"""Library for manipulating SPACE protocol messages.

This implements the SPACE (Serial Protocol for ACE) communications interface
and its higher-level command structure. More information may be found in
these two design docs:

* https://docs.google.com/document/d/10m6soKngZC6NPZSTEondkgAo78iheKSaCIwD1tIoUi4

* https://docs.google.com/document/d/1ubxcPF__EAEKWYdPicY2YRF4y8Y2wsH61LEIfDUPw0E
"""

__copyright__ = "Copyright 2020, Apollo Fusion Inc."

import ast
import binascii  # for CRC-16
import dataclasses
import re
import struct
import time

import serial  # Get this library with: pip3 install pyserial


# Special command format for an empty ping packet.
SPACE_PING = 'ping'
# Default deadline for commands.
MINIMUM_DEADLINE = 0.002  # 2 msec


class SpaceError(Exception):
  """Base exception class for errors in the SPACE library.

  This is not directly instantiated, but can be used to catch all of the
  derived library exceptions. Note that library functions may throw other
  generic Python exceptions too.
  """

class InitializationError(SpaceError):
  """Some sort of inconsistent setup of the command structure."""

class ParseError(SpaceError):
  """The structure of the message is bad, such as a wrong length."""

class IdentifierUnknown(SpaceError):
  """An identifier used in a message isn't recognized."""

class ParameterInvalid(SpaceError):
  """A message parameter cannot be understood, like using 2 for a tristate."""

class ParameterOutOfRange(SpaceError):
  """A message parameter is the correct format but out of the allowed range."""


class SpaceData:
  """Base class for representing parsed pieces of a message.

  Once parsed, the object can be output as either a binary or a text
  representation, which may involve recursive calls for compound objects.
  The inner structure can be accessed via the .value or (in subclasses) the
  .fields attributes if necessary.
  """
  # TODO(edkeyes): Consider whether it makes sense to implement this as an
  # abstract base class, which would let us do things like check whether an
  # unknown object conforms to the right method signature.

  def __init__(self, value=None):
    self.value = value

  def to_binary(self):
    """Renders the data object as a binary string in wire format.

    Args: None

    Returns:
      The data as a bytes() array, including any recursive fields.
    """
    raise NotImplementedError

  def to_text(self):
    """Renders the data object as a text string in human-readable format.

    Args: None

    Returns:
      The data as a string, including any recursive fields. The format
      should be suitable to be re-parsed back to a SpaceData object.
    """
    raise NotImplementedError

  def __str__(self):
    return self.to_text()

  def __repr__(self):
    hex_str = self.to_binary().hex(' ')
    return f"{self.to_text()}({hex_str})"


class SpaceParser:
  """Base class for parsing messages from binary or text.

  This constructs an internal representation of a piece of a message, which
  is returned as some SpaceData subclass.

  The sep value is used in the text parser to know when to stop parsing the
  initial value and ignore the remainder of the string.
  """
  # TODO(edkeyes): Ditto on whether this should be an abstract base class.

  def __init__(self, sep=' '):
    self.sep = sep

  def from_binary(self, binary):
    """Parses a wire-format binary string into the object representation.

    Args:
      binary: the data to parse as a bytes() array

    Returns:
      A tuple, containing a SpaceData object with the parsed data plus a
      bytes() array containing the remaining unparsed data, if any.
    """
    raise NotImplementedError

  def from_text(self, text):
    """Parses a text-format string into the object representation.

    Args:
      text: the data to parse as a string

    Returns:
      A tuple, containing a SpaceData object with the parsed data plus a
      string containing the remaining unparsed data, if any.
    """
    raise NotImplementedError


class EmptyData(SpaceData):
  """Special case for things like zero-length ping packets."""

  def __init__(self, label=''):
    super().__init__()
    self.label = label

  def to_binary(self):
    return b''

  def to_text(self):
    return self.label


def struct_format(bits, signed):
  """Returns the struct-library format string for an integer type."""
  # Everything is little-endian.
  if bits == 8:
    return '<b' if signed else '<B'
  elif bits == 16:
    return '<h' if signed else '<H'
  elif bits == 32:
    return '<i' if signed else '<I'
  elif bits == 64:
    return '<q' if signed else '<Q'
  else:
    assert False, f"Unsupported integer type: {bits} bits"


class IntegerData(SpaceData):
  """Representation of an integer value of defined length and signedness."""

  def __init__(self, value, bits=8, signed=False):
    try:
      value = int(value)
    except ValueError:
      raise ParameterInvalid(f"Cannot convert to integer: {value}")
    minimum = 0
    maximum = (1 << bits) - 1
    if signed:
      minimum -= 1 << (bits - 1)
      maximum -= 1 << (bits - 1)
    if not minimum <= value <= maximum:
      raise ParameterInvalid(f"Not a valid {bits}-bit integer: {value}")
    super().__init__(value)
    self.bits = bits
    self.signed = signed

  def to_binary(self):
    return struct.pack(struct_format(self.bits, self.signed), self.value)

  def to_text(self):
    return str(self.value)


class IntegerParser(SpaceParser):
  """Parser for integer numerical values of defined length and signedness."""

  def __init__(self, bits=8, signed=False, **kwargs):
    super().__init__(**kwargs)
    self.bits = bits
    self.signed = signed

  def from_binary(self, binary):
    length = (self.bits + 7) // 8  # Round up
    parse, rest = binary[:length], binary[length:]
    value = struct.unpack(struct_format(self.bits, self.signed), parse)[0]
    return IntegerData(value, bits=self.bits, signed=self.signed), rest

  def from_text(self, text):
    if self.sep in text:
      parse, rest = text.split(self.sep, 1)
    else:
      parse, rest = text, ''
    try:
      # We allow both decimal and hexadecimal representations.
      if parse.startswith('0x') or parse.startswith('0X'):
        value = int(parse[2:], 16)
        if self.signed and value >= (1 << (self.bits - 1)):
          value -= 1 << self.bits
      else:
        value = int(parse)
    except ValueError:
      raise ParseError(f"Cannot parse as integer: {parse}")
    return IntegerData(value, bits=self.bits, signed=self.signed), rest


class ByteData(IntegerData):
  """Representation of a discrete value such as an identifier.

  Simple byte fields are used in several places in the message structure:
  message types, telemetry identifiers, and tristate values.
  """

  def __init__(self, value, label=None):
    super().__init__(value, bits=8, signed=False)
    self.label = label

  def to_text(self):
    if self.label is not None:
      return self.label
    return super().to_text()


class ByteParser(IntegerParser):
  """Parser for byte-sized numerical values."""

  def __init__(self, **kwargs):
    super().__init__(bits=8, signed=False, **kwargs)


class FloatData(SpaceData):
  """Representation of a floating-point number such as a telemetry value.

  For generality we also allow the physical units of the quantity to be
  annotated, since this could be useful for some user interfaces to know,
  but this is not part of the binary or canonical text format.
  """

  def __init__(self, value, units=None):
    try:
      value = float(value)
    except ValueError:
      raise ParameterInvalid(f"Cannot convert to float: {value}")
    super().__init__(value)
    self.units = units

  def to_binary(self):
    return struct.pack('<f', self.value)

  def to_text(self):
    # Take advantage of the %g pretty-printing format to avoid having
    # a lot of useless decimal places.
    return f"{self.value:g}"

  def __repr__(self):
    result = super().__repr__()
    if self.units is not None:
      result += f"({self.units})"
    return result


class FloatParser(SpaceParser):
  """Parser for floating-point numerical values.

  We allow for the physical units to be internally annotated, though this is
  not represented in the binary or canonical text format.
  """

  def __init__(self, units=None, **kwargs):
    super().__init__(**kwargs)
    self.units = units

  def from_binary(self, binary):
    parse, rest = binary[:4], binary[4:]
    value = struct.unpack('<f', parse)[0]
    return FloatData(value, units=self.units), rest

  def from_text(self, text):
    if self.sep in text:
      parse, rest = text.split(self.sep, 1)
    else:
      parse, rest = text, ''
    try:
      value = float(parse)
    except ValueError:
      raise ParseError(f"Cannot parse as float: {parse}")
    return FloatData(value, units=self.units), rest


class StringData(SpaceData):
  """Representation of a variable-length string.

  The internal representation is as a bytes array, without the wire-format
  null termination. The textual representation requires quotes (single or
  double) and allows some types of escape sequences in Python format.
  """

  def to_binary(self):
    return self.value + b'\0'

  def to_text(self):
    return repr(self.value.decode('utf-8'))


class StringParser(SpaceParser):
  """Parser for variable-length strings."""

  def from_binary(self, binary):
    if b'\0' not in binary:
      raise ParseError(f"Null terminator not found: {repr(binary)}")
    value, rest = binary.split(b'\0', 1)
    return StringData(value), rest

  def from_text(self, text):
    # We require strings to be quoted (single or double) to distinguish them
    # from identifiers. Within the quotes, some escape sequences are allowed,
    # though we will get confused by escaped quotes of the same type.
    regex = r"""('[^']*'|"[^"]*")(.*)"""
    match = re.match(regex, text)
    if not match:
      raise ParseError(f"Cannot parse string value: {repr(text)}")
    try:
      value = ast.literal_eval(match.group(1))
    except:  # Not sure what exceptions literal_eval() might throw.
      raise ParseError(f"Cannot parse escape sequence: {repr(text)}")
    rest = match.group(2)
    if rest:
      if rest.startswith(self.sep):
        rest = rest[len(self.sep):]
      else:
        raise ParseError(f"Unexpected data after string: {repr(text)}")
    return StringData(value.encode('utf-8')), rest


class IdentifierParser(SpaceParser):
  """Parser for discrete values such as identifiers.

  This class contains a lookup table of the different possible values, which
  are parsed into a specific ByteData object. There are likely to be multiple
  instantiations of this class, each covering a group of identifiers such as
  coils, valves, message types, telemetry fields, etc.

  In addition to a canonical text representation, we allow for multiple
  aliases that parse to the same value in order to be friendlier to human
  console use cases.
  """

  def __init__(self):
    super().__init__()
    self._code_to_label = {}
    self._label_to_code = {}

  def add(self, code, label, aliases=()):
    """Registers a new identifier to be recognized by the parser.

    Args:
      code: unique numerical value for the identifier, as a single byte
      label: canonical text-format value for the identifier, as a string
      aliases: an iterator of additional text-format values which should
          also be recognized as an abbreviation for the same identifier

    Returns: None
    """
    code = int(code)
    if not 0 <= code <= 0xFF:
      raise ParameterInvalid(f"Not a valid byte: {code}")
    # Make sure we're not adding contradictory information.
    if code in self._code_to_label:
      if label != self._code_to_label[code]:
        raise InitializationError(f"Conflicting identifier for {code}: {label}")
    self._code_to_label[code] = label
    # We also include the decimal number as an allowed alias.
    for alias in (label, str(code), *aliases):
      if alias in self._label_to_code and code != self._label_to_code[alias]:
        raise InitializationError(f"Conflicting identifier for {code}: {alias}")
      self._label_to_code[alias] = code

  def from_binary(self, binary):
    code, rest = binary[0], binary[1:]
    if code not in self._code_to_label:
      raise IdentifierUnknown(f"Unrecognized identifier code: {code}")
    label = self._code_to_label[code]
    return ByteData(code, label), rest

  def from_text(self, text):
    if self.sep in text:
      label, rest = text.split(self.sep, 1)
    else:
      label, rest = text, ''
    if label not in self._label_to_code:
      raise IdentifierUnknown(f"Unrecognized identifier label: {label}")
    code = self._label_to_code[label]
    # Convert back to the canonical label from a possible alias.
    label = self._code_to_label[code]
    return ByteData(code, label), rest


class ListData(SpaceData):
  """Representation of a list (or often a pair) of parameter values.

  For lists, this could be an entire message payload. For pairs, it will
  typically be an identifier and a floating-point or tristate value. The
  latter case also encompasses the "pair" of a message type and payload.
  The contents of the list can be accessed through usual Python indexing
  operations, with each element being a SpaceData object.
  """

  def __init__(self, fields, sep=' '):
    super().__init__()
    self.fields = tuple(fields)
    self.sep = sep

  def to_binary(self):
    return b''.join(x.to_binary() for x in self.fields)

  def to_text(self):
    return self.sep.join(x.to_text() for x in self.fields)

  def __repr__(self):
    return self.sep.join(repr(x) for x in self.fields)

  def __iter__(self):
    return iter(self.fields)

  def __len__(self):
    return len(self.fields)

  def __bool__(self):
    return bool(self.fields)

  def __getitem__(self, i):
    return self.fields[i]


class ListParser(SpaceParser):
  """Parser for a list of possibly variable-length message parameters.

  This breaks a larger message structure into a list of pieces, calling a
  given parser on each one in turn. The number of fields can be limited,
  in which case the extra data is left unparsed, but without a limit, the
  data must be evenly divisible into parsable fields.
  """

  def __init__(self, parser, max_length=None, **kwargs):
    super().__init__(**kwargs)
    self.parser = parser
    self.max_length = max_length

  def from_binary(self, binary):
    fields = []
    while binary and (self.max_length is None or
                      len(fields) < self.max_length):
      data, binary = self.parser.from_binary(binary)
      fields.append(data)
    return ListData(fields, sep=self.sep), binary

  def from_text(self, text):
    fields = []
    while text and (self.max_length is None or
                    len(fields) < self.max_length):
      data, text = self.parser.from_text(text)
      fields.append(data)
    return ListData(fields, sep=self.sep), text


class PairParser(SpaceParser):
  """Parser for an identifier and an identifier-dependent value.

  This sort of structure occurs for message types and payloads, or for
  things like telemetry fields and their values. There is a fixed initial
  parser which looks at the beginning of the data, and based on the value
  it sees, it runs a second parser (which could be a default) on the
  remainder of the data.

  Note that aliases should be added as part of the first parser. The lookup
  table constructed by add() in this object is keyed by the unique byte
  identifier value.
  """

  def __init__(self, first_parser, default_parser=None, sep='='):
    super().__init__(sep=sep)
    self.first_parser = first_parser
    self.default_parser = default_parser
    self._second_parsers = {}

  def add(self, code, parser=None):
    """Registers a new identifier to be recognized, with its associated parser.

    Args:
      code: unique numerical value for the identifier, as a single byte
      parser: a SpaceParser object to be used to parse the data following
          the identifier when it is present

    Returns: None
    """
    # Make sure we're not adding contradictory information.
    if (code in self._second_parsers and
        parser != self._second_parsers[code]):
      raise InitializationError(
          f"Conflicting parser for pair identifier code: {code}")
    self._second_parsers[code] = parser

  def from_binary(self, binary):
    first, binary = self.first_parser.from_binary(binary)
    parser = self._second_parsers.get(first.value, self.default_parser)
    if parser is None:
      if not binary:
        # Empty second half, and that's okay.
        return ListData((first,), sep=self.sep), binary
      raise IdentifierUnknown(f"Unknown identifier value: {first.value}")
    second, rest = parser.from_binary(binary)
    return ListData((first, second), sep=self.sep), rest

  def from_text(self, text):
    # Note that the first_parser will not necessarily know about our own
    # separator, so we do our own splitting before passing it a subset of
    # the data to parse. However, the second_parser is expected to be able
    # to know where its value stops.
    if self.sep in text:
      first_text, second_text = text.split(self.sep, 1)
    else:
      first_text, second_text = text, ''
    first, rest = self.first_parser.from_text(first_text)
    if rest:
      raise ParseError(f"Cannot parse as an identifier: {first_text}")
    parser = self._second_parsers.get(first.value, self.default_parser)
    if parser is None:
      if not second_text:
        # Empty second half, and that's okay.
        return ListData((first,), sep=self.sep), second_text
      raise IdentifierUnknown(f"Unknown identifier value: {first.value}")
    second, rest = parser.from_text(second_text)
    return ListData((first, second), sep=self.sep), rest


class MessageData(ListData):
  """Representation of a message as its type and payload.

  This just extends the ListData to also store the message type's deadline,
  since that's convenient to have when sending it.
  """

  def __init__(self, fields, sep=' ', deadline=None):
    super().__init__(fields, sep=sep)
    self.deadline = deadline


class MessageParser(PairParser):
  """Parser for a whole SPACE message.

  This first recognizes the message type, and then calls a registered
  parser in order to handle the payload data based on the type. It is mostly
  just a subclass of the PairParser, with a little override logic to handle
  the non-pair 'ping' packets, change the default pair separator, and keep
  track of message deadlines.
  """

  def __init__(self, type_parser, second_parser=None, sep=' '):
    # Note we are overriding the default '=' pair separator.
    super().__init__(type_parser, default_parser=second_parser, sep=sep)
    self._deadlines = {}

  def add(self, code, parser=None, deadline=None):
    super().add(code, parser)
    self._deadlines[code] = deadline

  def from_binary(self, binary):
    # Handle the special case of pings.
    if binary == b'':
      return (MessageData([EmptyData(SPACE_PING)], deadline=MINIMUM_DEADLINE),
              b'')
    message, rest = super().from_binary(binary)
    # Add the deadline and re-wrap as a MessageData class.
    return (MessageData(message.fields, sep=self.sep,
                        deadline=self._deadlines[message[0].value]),
            rest)

  def from_text(self, text):
    # Handle the special case of pings.
    if text == SPACE_PING:
      return (MessageData([EmptyData(SPACE_PING)], deadline=MINIMUM_DEADLINE),
              b'')
    message, rest = super().from_text(text)
    # Add the deadline and re-wrap as a MessageData class.
    return (MessageData(message.fields, sep=self.sep,
                        deadline=self._deadlines[message[0].value]),
            rest)


@dataclasses.dataclass
class SpaceCommand:
  """Simple container class to define a command message and its reply."""

  command_code: int
  command_str: str
  deadline: float
  command_parser: SpaceParser
  reply_parser: SpaceParser
  #TODO(edkeyes): Should we support an aliases list?

  @property
  def reply_code(self):
    """Reply message types are typically one higher than the command."""
    return self.command_code + 1

  @property
  def reply_str(self):
    """Reply message names are typically the command with a suffix."""
    return self.command_str + '_ack'


class SpaceProtocol:
  """Functions as an SPACE protocol master to talk to a specific device.

  It can send commands and receive replies, both as SpaceData objects
  containing the message payload or as the friendly text format.
  """

  # These constants are part of the protocol specification.
  BAUD_RATE = 115200
  SYNC_SEQUENCE = bytes((0x1A, 0xCE))
  COMMAND_BYTE = 0xA0
  REPLY_BYTE = 0xB0
  CRC_INITIAL = 0xFFFF
  CRC_XOR = 0xACE1
  MAX_MESSAGE_SIZE = 127
  # Python isn't great at millisecond timing on various OSes, so we have it
  # wait a little longer than the real command deadline before giving up on
  # a reply.
  EXTRA_DEADLINE = 0.100  # 100 msec

  def __init__(self, port_name, address, message_parser, debug=False):
    if not 0x00 <= address <= 0x0F:
      raise InitializationError(f"Invalid device address: {address}")
    self.serial = serial.Serial(port_name, self.BAUD_RATE, timeout=0,
                                parity=serial.PARITY_NONE,
                                stopbits=serial.STOPBITS_ONE)
    self.address = address
    self.parser = message_parser
    self.debug = debug
    self._status = None

  def send_text(self, command, deadline=None, **kwargs):
    """Sends a message to the device and returns the reply received.

    Args:
      command: message to send as a text string
      deadline: time in seconds that a reply must be received by

    Returns:
      The reply as a text string or None if the deadline expired before a
      valid reply was received.
    """
    message, rest = self.parser.from_text(command)
    if rest:
      raise ParseError(f"Cannot parse command: {command}")
    reply = self.send_message(message, deadline=deadline, **kwargs)
    if reply is None:
      return reply
    return reply.to_text()

  def send_message(self, command, deadline=None):
    """Sends a message to the device and returns the reply received.

    Args:
      command: message to send as a SpaceData object
      deadline: time in seconds that a reply must be received by

    Returns:
      The reply as a SpaceData object, or None if the deadline expired
      before a valid reply was received.
    """
    if deadline is None:
      deadline = command.deadline
    if deadline is None:
      deadline = MINIMUM_DEADLINE
    packet = self._to_packet(command)
    if self.debug:
      print(f"Sending: {command.to_text()}")
      print(f" Packet: {packet.hex(' ')}")
    self.serial.reset_input_buffer()
    self.serial.write(packet)
    self.serial.flush()
    start_time = time.time()
    reply = b''
    while time.time() < start_time + deadline + self.EXTRA_DEADLINE:
      data = self.serial.read(1)
      if not data:
        time.sleep(0.0001)  # about 1 byte's time on the serial port
        continue
      elapsed = time.time() - start_time
      reply += data
      message, status = self._from_packet(reply)
      if message is not None:
        self._status = status
        if self.debug:
          print(f"Elapsed time for reply: {elapsed * 1000:.3f} msec")
          print(f"Received: {message.to_text()}")
          print(f"  Packet: {reply.hex(' ')}")
        return message
    # The deadline expired before we got a valid packet.
    print(f"Deadline of {deadline * 1000:.3f} msec expired.")
    if reply:
      print(f"Partial/invalid packet: {reply.hex(' ')}")
    return None

  def get_status(self):
    """Returns the last-received status byte from a reply message.

    Args: None

    Returns:
      The last-received status value as a byte, or None if no valid replies
      have yet been processed.
    """
    return self._status

  def _crc16(self, data):
    """Calculates the CRC16 checksum for a span of bytes.

    Args:
      data: Iterable of bytes to calculate the checksum over

    Returns:
      The CRC16 checksum as a 16-bit unsigned integer.
    """
    # This library function uses the same 0x1021 polynomial.
    return binascii.crc_hqx(bytes(data), self.CRC_INITIAL) ^ self.CRC_XOR

  def _to_packet(self, message):
    """Renders a SpaceData message into a wire-format packet.

    Args:
      message: message to send as a SpaceData object with type and payload

    Returns:
      The wire-format packet, including sync sequence and checksum, as a
      bytes() array.
    """
    packet = self.SYNC_SEQUENCE
    packet += bytes((self.COMMAND_BYTE | self.address,))
    message_bytes = message.to_binary()
    if len(message_bytes) > self.MAX_MESSAGE_SIZE:
      raise ParseError("Message exceeds allowed packet length: "
                       + message.to_text())
    packet += bytes((len(message_bytes),)) + message_bytes
    # The checksum is calculated over the entire packet minus the fixed
    # sync sequence and the checksum bytes themselves.
    crc = self._crc16(packet[2:])
    packet += struct.pack('<H', crc)
    return packet

  def _from_packet(self, packet):
    """Parses a wire-format reply packet into a SpaceData message.

    Args:
      packet: wire-format packet as a bytes() array

    Returns:
      A tuple containing the message as a SpaceData object plus the reply
      status byte, or (None, None) if the packet is incomplete or invalid.
    """
    # TODO(edkeyes): In theory we should be scanning all of the received
    # data for the sync sequence instead of assuming it is at the beginning,
    # though there really shouldn't be any other data on the bus right now.
    # (We also reset the input buffer in each transaction to clear any
    # leftover bytes from previous packets.)
    if (len(packet) < 7 or  # minimum reply packet size
        packet[:2] != self.SYNC_SEQUENCE or
        packet[2] != (self.REPLY_BYTE | self.address)):
      return None, None
    length = packet[4]
    if length > self.MAX_MESSAGE_SIZE or len(packet) != length + 7:
      # Note we also reject cases where there are extra bytes at the end
      # of an otherwise valid packet, since we only expect one reply.
      return None, None
    # The checksum is calculated over the entire packet minus the fixed
    # sync sequence and the checksum bytes themselves.
    crc = self._crc16(packet[2:5 + length])
    if struct.pack('<H', crc) != packet[5 + length:7 + length]:
      return None, None  # invalid checksum
    # At this point we have an apparently valid packet.
    status = packet[3]
    message, rest = self.parser.from_binary(packet[5:5 + length])
    assert rest == b''
    return message, status


if __name__ == '__main__':
  print("This library isn't intended to be run directly.")
