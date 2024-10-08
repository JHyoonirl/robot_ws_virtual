import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile
from custominterface.srv import Status


class PwmServer(Node):

    def __init__(self):
        super().__init__('pwm_status')
        qos_profile = QoSProfile(depth=10)
        self.resolution = 16
        # self.pwm_range = pow(2,16)
        # pwm initialize
        self.pwm_neut = int(50)
        self.pwm = self.pwm_neut
        self.srv = self.create_service(
            Status,
            'pwm_status',
            self.pwm_server
        )
        
        # self.timer = self.create_timer(0.01, self.publish_pwm)

    def pwm_server(self, request, response):
        if request.pwm_switch == True:
            response.pwm_result == True
            
        elif request.pwm_switch == False:
            response.pwm_result == False
        print(response)
        return response



    # def publish_pwm(self):
    #     msg = Float64()
    #     msg.data = float(self.pwm)
    #     self.pwm_publisher.publish(msg)
    #     self.get_logger().info('Published pwm: {0}'.format(msg.data))


def main(args=None):
    rclpy.init(args=args)
    node = PwmServer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Keyboard Interrupt (SIGINT)')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()