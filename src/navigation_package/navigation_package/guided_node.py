#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from mavros_msgs.srv import SetMode
from std_msgs.msg import String, Bool
from mavros_msgs.msg import State

class GuidedModeNode(Node):
    def __init__(self):
        super().__init__('guided_mode_node')
        
        # Service client for mode changes
        self.mode_client = self.create_client(SetMode, '/mavros/set_mode')
        
        # Publishers for status updates
        self.status_publisher = self.create_publisher(String, '/navigation/mode_status', 10)
        self.success_publisher = self.create_publisher(Bool, '/navigation/guided_ready', 10)
        
        # Subscriber to monitor current vehicle state
        self.state_subscriber = self.create_subscription(
            State, 
            '/mavros/state', 
            self.state_callback, 
            10
        )
        
        # Timer for periodic status publishing
        self.status_timer = self.create_timer(1.0, self.publish_status)
        
        # Internal state tracking
        self.current_mode = None
        self.guided_mode_set = False
        self.service_available = False
        
        # Wait for service and set mode
        self.check_service_and_set_mode()
        
        self.get_logger().info('Guided Mode Node started')
    
    def check_service_and_set_mode(self):
        """Check if service is available and attempt to set GUIDED mode"""
        if self.mode_client.wait_for_service(timeout_sec=1.0):
            self.service_available = True
            self.get_logger().info('MAVROS set_mode service available')
            self.set_guided_mode()
        else:
            self.get_logger().warn('Waiting for MAVROS set_mode service...')
            # Retry in 2 seconds
            self.create_timer(2.0, self.check_service_and_set_mode)
    
    def set_guided_mode(self):
        """Send request to set GUIDED mode"""
        request = SetMode.Request()
        request.base_mode = 0
        request.custom_mode = 'GUIDED'
        
        future = self.mode_client.call_async(request)
        future.add_done_callback(self.mode_response_callback)
    
    def mode_response_callback(self, future):
        """Handle response from mode change service"""
        try:
            response = future.result()
            if response.mode_sent:
                self.get_logger().info('GUIDED mode command sent successfully')
                # Don't mark as set until we confirm via state topic
            else:
                self.get_logger().error('Failed to send GUIDED mode command')
                self.publish_status_message('FAILED: Mode command rejected')
        except Exception as e:
            self.get_logger().error(f'Service call failed: {e}')
            self.publish_status_message('FAILED: Service call error')
    
    def state_callback(self, msg):
        """Monitor vehicle state changes"""
        self.current_mode = msg.mode
        
        # Check if we successfully switched to GUIDED
        if msg.mode == 'GUIDED' and not self.guided_mode_set:
            self.guided_mode_set = True
            self.get_logger().info('Vehicle confirmed in GUIDED mode!')
            self.publish_success(True)
            self.publish_status_message('SUCCESS: GUIDED mode active')
    
    def publish_status(self):
        """Periodic status updates"""
        if not self.service_available:
            status = 'WAITING: Service not available'
        elif not self.guided_mode_set:
            status = f'SETTING: Current mode is {self.current_mode}'
        else:
            status = f'READY: GUIDED mode confirmed'
        
        self.publish_status_message(status)
    
    def publish_status_message(self, message):
        """Publish status message"""
        msg = String()
        msg.data = message
        self.status_publisher.publish(msg)
    
    def publish_success(self, success):
        """Publish success/failure flag"""
        msg = Bool()
        msg.data = success
        self.success_publisher.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    
    node = GuidedModeNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Guided Mode Node stopped')
    
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()