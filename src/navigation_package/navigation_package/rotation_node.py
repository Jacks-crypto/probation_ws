#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Bool
from vision_msgs.msg import BoundingBoxArray

class RotationNode(Node):
    def __init__(self):
        super().__init__('rotation_node')
        
        # Publishers
        self.velocity_publisher = self.create_publisher(
            Twist, 
            '/mavros/setpoint_velocity/cmd_vel_unstamped', 
            10
        )
        self.detection_complete_publisher = self.create_publisher(
            Bool,
            '/navigation/detection_complete',
            10
        )
        
        # Subscribers
        self.complete_subscriber = self.create_subscription(
            Bool,
            '/navigation/movement_complete',
            self.start_rotation,
            10
        )
        
        # Camera detection subscriber - KEY ADDITION
        self.detection_subscriber = self.create_subscription(
            BoundingBoxArray,
            '/main_camera/detection/bounding_boxes',
            self.detection_callback,
            10
        )
        
        # Parameters for filtering
        self.declare_parameter('target_label', 'gate_04')
        self.declare_parameter('min_confidence', 0.7)
        self.declare_parameter('rotation_speed', -0.5)
        
        self.rotation_timer = None
        self.rotating = False
        
    def start_rotation(self, msg):
        if msg.data and self.rotation_timer is None:
            self.get_logger().info('Starting rotation search')
            self.rotating = True
            self.rotation_timer = self.create_timer(0.1, self.rotate)
    
    def detection_callback(self, msg):
        """Process camera detections - MAIN DETECTION LOGIC"""
        if not self.rotating:
            return
        
        # Check each bounding box for gate
        for bbox in msg.bounding_boxes:
            # Log ALL detections for debugging
            self.get_logger().info(f'Detected: {bbox.label_name}, conf={bbox.conf:.2f}, '
                                  f'center=({bbox.x:.2f},{bbox.y:.2f}), size={bbox.w:.2f}x{bbox.h:.2f}')
            
            if self.is_gate(bbox):
                self.get_logger().info(f'GATE FOUND! Center: ({bbox.x:.2f}, {bbox.y:.2f}), Size: {bbox.w:.2f}x{bbox.h:.2f}')
                self.stop_rotation()
                return
        
        # Log search status if no detections
        if len(msg.bounding_boxes) == 0:
            self.get_logger().info('Searching for gate... No detections')
    
    def is_gate(self, bbox):
        """Specific filter for gate detection"""
        return (
            bbox.label_name == 'gate' and
            bbox.conf >= 0.5 and                      # Confidence threshold
            bbox.x >= 0.40 and bbox.x <= 0.60 and      # Center X range (your: 0.44)
            bbox.y >= 0.30 and bbox.y <= 0.70 and      # Center Y range (your: 0.51)  
            bbox.w >= 0.1 and                         # Minimum width (your: 0.52)
            bbox.h >= 0.4                             # Minimum height (your: 0.68)
        )
    
    def stop_rotation(self):
        """Stop rotation when target found"""
        if self.rotation_timer:
            self.rotation_timer.cancel()
            self.rotation_timer = None
        
        self.rotating = False
        
        # Send stop command
        stop_twist = Twist()
        self.velocity_publisher.publish(stop_twist)
        
        # Signal completion
        complete_msg = Bool()
        complete_msg.data = True
        self.detection_complete_publisher.publish(complete_msg)
        
        self.get_logger().info('Rotation stopped - target detected!')
    
    def rotate(self):
        if self.rotating:
            twist = Twist()
            twist.angular.z = self.get_parameter('rotation_speed').value
            self.velocity_publisher.publish(twist)

def main():
    rclpy.init()
    node = RotationNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()