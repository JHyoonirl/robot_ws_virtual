import serial
import threading
import time
from multiprocessing import Queue

class FTSensor:
    def __init__(self, port='/dev/ttyUSB0'):
        self.sensor = serial.Serial(
            port=port,
            baudrate=115200,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=None  # 블로킹 없이 설정
        )
        self.running = True
        self.data_buffer = bytearray()
        self.lock = threading.Lock()
        self.sample_rate = 0.005  # 200Hz의 주기, 즉 5ms
        self.last_time = time.time()
        self.packet_count = 0

    def ft_sensor_init(self):
        # 초기화 데이터 전송 로직
        initial_commands = [
            [0x11, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],  # Bias
            [0x06, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],  # Baud rate
            [0x08, 0x01, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00],  # Filter
            [0x0F, 0x06, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]   # Output rate
        ]
        for command in initial_commands:
            self.send_data_without_read(command)
            time.sleep(0.2)
        print('FT sensor 초기화 성공')
        return True

    def ft_sensor_continuous_data(self):
        cmd = [0x0B, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]   # Continuous read
        try:
            self.send_data_without_read(cmd)
            time.sleep(0.2)
            print('FT sensor start 성공')
            return True
        except Exception as e:
            print('FT sensor start 실패:', e)
            return False
        
    def ft_sensor_stop_data(self):
        cmd = [0x0C, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]   # Continuous read
        try:
            self.send_data_without_read(cmd)
            time.sleep(0.2)
            print('FT sensor Stop 성공')
            return True
        except Exception as e:
            print('FT sensor Stop 실패:', e)
            return False
        
    def ft_sensor_bias_set(self):
        cmd = [0x11, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        try:
            self.send_data_without_read(cmd)
            time.sleep(0.2)
            print('FT sensor bias 성공')
            return True
        except Exception as e:
            print('FT sensor bias 실패:', e)
            return False

    def start_reading(self):
        next_reading_time = time.time()
        while self.running:
            data = self.sensor.read(100)  # 16바이트 데이터 읽기
            # print(data)
            with self.lock:
                self.data_buffer.extend(data)
                
            next_reading_time += self.sample_rate

    def process_data(self):
        next_process_time = time.time()
        report_interval = 1.0  # 데이터 처리 속도를 보고하는 간격 (1초)
        last_report_time = time.time()

        while self.running:
            with self.lock:
                if len(self.data_buffer) >= 16:
                    if self.data_buffer[0] == 0x0B:
                        packet = self.data_buffer[:16]
                        self.decoded_force, self.decoded_torque = self.decode_received_data(packet[1:13])
                        # print(decoded_force, decoded_torque)
                        self.packet_count += 1
                        self.data_buffer = self.data_buffer[16:]
                    else:
                        self.data_buffer.pop(0)

            # 처리 주파수 보고
            if time.time() - last_report_time >= report_interval:
                # print(f'Processed {self.packet_count} packets in the last second.')
                self.packet_count = 0
                last_report_time = time.time()

            next_process_time += self.sample_rate

    def decode_received_data(self, packet):
        force = [int.from_bytes(packet[i*2:2+i*2], byteorder='big', signed=True) / 50 for i in range(3)]
        torque = [int.from_bytes(packet[6+i*2:8+i*2], byteorder='big', signed=True) / 1000 for i in range(3)]
        return force, torque

    def send_data_without_read(self, data):
        sop = bytes([0x55])
        eop = bytes([0xAA])
        checksum = self.calculate_checksum(data)
        packet = sop + bytes(data) + bytes([checksum]) + eop
        self.sensor.write(packet)

    def calculate_checksum(self, data):
        return sum(data) % 256

    def stop(self):
        self.running = False
        self.sensor.close()

if __name__ == "__main__":
    ft_sensor = FTSensor('/dev/ttyUSB0')
    ft_sensor.ft_sensor_init()
    ft_sensor.ft_sensor_continuous_data()
    read_thread = threading.Thread(target=ft_sensor.start_reading)
    process_thread = threading.Thread(target=ft_sensor.process_data)
    read_thread.start()
    process_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        ft_sensor.stop()
        read_thread.join()
        process_thread.join()
