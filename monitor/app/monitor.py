"""
Read on the TCP server for data
"""

import socket
import json
import time
from datetime import datetime
from can_data import Signal, DBC
from influx_writer import write_signal

class Monitor:
    def __init__(self, server_address: str, server_port: int, dbc_path: str):
        self.server_address: str = server_address
        self.server_port: int = server_port
        self.dbc: DBC = DBC(dbc_path)

    def read_tcp(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # Connect to the server
            s.connect((self.server_address, self.server_port))
            print("Connected to server at %s on port %s", self.server_address, self.server_port)
            
            while True:
                # Receive message from the server
                data = s.recv(1024)
                print(data)
                if not data:
                    # No more data from server, can happen if the server closes the connection
                    print("Disconnected from server")
                    break

                # Assuming the message is in JSON format

                # data = data.decode().replace("'", '"')
                # message = json.loads(data)
                # print("Received JSON message: %s", message)

                
                # Sleep for a second to manage timing and avoid spamming
                time.sleep(1)
    
    def read_log_csv(self, log_path: str, loops: int = 1):
        """Test method to read signals from CAN logs"""
        def convert_value(value):
            # Attempt to convert the value to an int, float, or leave as string
            try:
                if '.' in value:
                    return float(value)
                return int(value)
            except ValueError:
                return value

        initial_timestamp = None
        total_offset = 0

        for _ in range(loops):
            with open(log_path, 'r') as file:
                for line in file:
                    parts = line.strip().split(',')
                    timestamp_str, signal_name = parts[:2]
                    value = ','.join(parts[2:])

                    original_timestamp = float(timestamp_str)

                    if initial_timestamp is None:
                        # Set the initial timestamp based on the first log entry
                        initial_timestamp = original_timestamp

                    # Adjust the timestamp for current line including the total offset from previous loops
                    timestamp = original_timestamp - initial_timestamp + total_offset

                    value = convert_value(value)

                    signal = Signal(signal_name, value, timestamp, self.dbc)
                    write_signal(signal)


            # After finishing each loop through the file, update the total_offset
            # This offset will be applied to timestamps in the next iteration
            total_offset = timestamp + (original_timestamp - initial_timestamp) - total_offset


    def simulate_telemetry(self, log_path: str):
        """Test method to simulate telemetry data"""
        def convert_value(value):
            try:
                if '.' in value:
                    return float(value)
                return int(value)
            except ValueError:
                return value

        # Get the current time
        start_time = datetime.now().timestamp()

        # Initialize variables to store the initial and last timestamps from the log file
        initial_timestamp_log = None
        last_timestamp_log = 0

        with open(log_path, 'r') as file:
            for line in file:
                parts = line.strip().split(',')
                timestamp_str, signal_name = parts[:2]
                value = ','.join(parts[2:])

                original_timestamp = float(timestamp_str)

                if initial_timestamp_log is None:
                    initial_timestamp_log = original_timestamp

                # Calculate the time difference from the last log entry
                time_difference = original_timestamp - initial_timestamp_log

                # Calculate the real-time timestamp adjustment
                adjusted_timestamp = start_time + time_difference

                # Calculate the delay needed before sending the next data
                delay = adjusted_timestamp - (start_time + last_timestamp_log)

                # Wait for the time offset from the last entry before proceeding
                if delay > 0:
                    time.sleep(delay)

                last_timestamp_log = time_difference

                value = convert_value(value)

                # Call the send_data function with the adjusted timestamp

                signal = Signal(signal_name, value, adjusted_timestamp, self.dbc)
                write_signal(signal)