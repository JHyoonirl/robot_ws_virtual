from FT_SENSOR import FTSensor
import rclpy
import sys
from rclpy.node import Node
from rclpy.qos import QoSProfile
# from std_msgs.msg import String, Float64

from rclpy.qos import QoSProfile
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QSpinBox, QLabel
from threading import Thread

from geometry_msgs.msg import Vector3
from custominterface.srv import Status

class Sensor(Node):
    def __init__(self):
        super().__init__('FT_data')
        self.declare_parameter('usb_port', '/dev/ttyUSB0')
        usb_port = self.get_parameter('usb_port').get_parameter_value().string_value

        self.sensor = FTSensor(port=usb_port)
        self.serial_port = self.sensor.ser
        self.init_status = self.init_sensor()

        # 데이터 퍼블리싱을 위한 퍼블리셔 설정
        self.force_publisher = self.create_publisher(Vector3, 'force_data', 10)
        self.torque_publisher = self.create_publisher(Vector3, 'torque_data', 10)
        self.data_on = False

        if self.init_status:
            # 0.005초 간격으로 publish_sensor 호출
            self.timer = self.create_timer(0.0001, self.publish_sensor)
        
    def init_sensor(self):
        if not self.sensor.ft_sensor_init():
            self.get_logger().error('Failed to initialize sensor')
            return False
        else:
            return True

    def publish_sensor(self):
        if not self.data_on:
            return  # 데이터 전송이 활성화되지 않았다면 종료
        
        force = Vector3()
        torque = Vector3()
        try:
            data = self.serial_port.read(1)  # 1바이트 읽기
            if data and data[0] == 0x0B:  # 특정 데이터 값 확인
                data_received = self.serial_port.read(13)  # 추가 데이터 읽기
                decoded_force, decoded_torque = self.sensor.decode_received_data(data_received)
                force.x, force.y, force.z = decoded_force
                torque.x, torque.y, torque.z = decoded_torque
                # self.get_logger().info(f'data: {force, torque}')
                self.force_publisher.publish(force)  # 데이터 퍼블리시
                self.torque_publisher.publish(torque)
        except Exception as e:
            pass
            # self.get_logger().error(f'Error reading sensor data: {e}')

class SensorApp(QWidget):
    def __init__(self, node):
        super().__init__()
        self.node = node
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        self.btn_bias = QPushButton('Set Bias', self)
        self.btn_on = QPushButton('Turn On Data', self)
        self.btn_off = QPushButton('Turn Off Data', self)
        self.btn_bias.clicked.connect(self.set_bias)
        self.btn_on.clicked.connect(self.turn_on)
        self.btn_off.clicked.connect(self.turn_off)

        layout.addWidget(self.btn_bias)
        layout.addWidget(self.btn_on)
        layout.addWidget(self.btn_off)

        self.setLayout(layout)
        self.setWindowTitle('Sensor UI')
        self.show()

    def set_bias(self):
        if self.node.init_status:
            bias_result = self.node.sensor.ft_sensor_bias_set()

    def turn_on(self):
        if self.node.sensor.ft_sensor_continuous_data():
            self.btn_bias.setDisabled(True)
            self.node.data_on = True

    def turn_off(self):
        if self.node.sensor.ft_sensor_stop_data():
            self.btn_bias.setEnabled(True)
            self.node.data_on = False

def main(args=None):
    rclpy.init(args=args)
    node = Sensor()
    thread = Thread(target=rclpy.spin, args=(node,), daemon=True)
    thread.start()

    app = QApplication(sys.argv)
    ex = SensorApp(node)
    app.exec_()
    
    node.destroy_node()
    rclpy.shutdown()
    thread.join()

if __name__ == '__main__':
    main()
