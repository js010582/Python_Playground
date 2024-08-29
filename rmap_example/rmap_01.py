import struct

# Constants for RMAP commands
RMAP_WRITE_COMMAND = 0x20  # Simplified example command code for write operation
RMAP_PROTOCOL_ID = 0x01  # Protocol ID for RMAP

# Example SpaceWire node addresses
OBC_ADDRESS = 0x01  # Onboard Computer Address
PAYLOAD_ADDRESS = 0x02  # Payload Address

# Example memory address in payload to write to
PAYLOAD_MEMORY_ADDRESS = 0x00000000

# Example data to write (4 bytes of data)
data_to_write = [0xDE, 0xAD, 0xBE, 0xEF]  # Example data

# Helper function to calculate RMAP header CRC
def calculate_crc(data):
    crc = 0x00
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ 0x07
            else:
                crc <<= 1
            crc &= 0xFF
    return crc

# Construct the RMAP Write Command Packet
def construct_rmap_write_command():
    # RMAP command header (simplified, no options)
    header = [
        RMAP_PROTOCOL_ID,        # Protocol ID
        RMAP_WRITE_COMMAND,      # Command
        OBC_ADDRESS,             # Source logical address (OBC)
        PAYLOAD_ADDRESS,         # Destination logical address (Payload)
        (PAYLOAD_MEMORY_ADDRESS >> 24) & 0xFF,  # Memory address (MSB)
        (PAYLOAD_MEMORY_ADDRESS >> 16) & 0xFF,
        (PAYLOAD_MEMORY_ADDRESS >> 8) & 0xFF,
        PAYLOAD_MEMORY_ADDRESS & 0xFF,           # Memory address (LSB)
        len(data_to_write)                       # Data length (assuming small data for simplicity)
    ]

    # Calculate the header CRC
    header_crc = calculate_crc(header)
    header.append(header_crc)

    # Add the data and calculate the data CRC
    data_crc = calculate_crc(data_to_write)
    payload = data_to_write + [data_crc]

    # Final RMAP packet
    rmap_packet = header + payload
    return rmap_packet

# Send the RMAP write command
def send_rmap_write_command(spacewire_interface):
    rmap_packet = construct_rmap_write_command()
    spacewire_interface.send_packet(rmap_packet)
    print("RMAP Write Command Sent:", rmap_packet)

# Receive the response (if any)
def receive_rmap_response(spacewire_interface):
    response_packet = spacewire_interface.receive_packet()
    if response_packet:
        print("Received Response:", response_packet)
        # Process the response (e.g., check for errors)
    else:
        print("No response received or timeout occurred.")

# Mock SpaceWire interface (replace with actual interface)
class MockSpaceWireInterface:
    def send_packet(self, packet):
        # Mock sending packet (replace with actual implementation)
        print(f"Mock sending packet: {packet}")

    def receive_packet(self):
        # Mock receiving packet (replace with actual implementation)
        # Here, we'll just simulate a simple acknowledgment response
        return [0x00, 0x01]  # Example response packet

# Main function to demonstrate the RMAP operation
def main():
    spacewire_interface = MockSpaceWireInterface()
    send_rmap_write_command(spacewire_interface)
    receive_rmap_response(spacewire_interface)

if __name__ == "__main__":
    main()
