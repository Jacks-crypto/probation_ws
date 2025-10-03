#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import String, Bool, Float64
import time

class ForwardMovementNode(Node):
    def __init__(self):
        super().__init__('forward_movement_node')
        
        # Publishers
        self.velocity_publisher = self.create_publisher(
            Twist,
            '/mavros/setpoint_velocity/cmd_vel_unstamped',
            10
        )
        self.status_publisher = self.create_publisher(String, '/navigation/forward_status', 10)
        self.progress_publisher = self.create_publisher(Float64, '/navigation/forward_progress', 10)
        self.complete_publisher = self.create_publisher(Bool, '/navigation/forward_complete', 10)
        
        # Subscribers
        self.detection_subscriber = self.create_subscription(
            Bool,
            '/navigation/detection_complete',
            self.detection_complete_callback,
            10
        )
        
        # Parameters
        self.declare_parameter('forward_speed', 1.0)     # m/s (positive = forward)
        self.declare_parameter('forward_duration', 3.0)  # seconds
        self.declare_parameter('wait_for_detection', True)  # Wait for gate detection
        
        # State variables
        self.detection_complete = False
        self.movement_active = False
        self.movement_complete = False
        self.start_time = None
        
        # Timers
        self.movement_timer = self.create_timer(0.1, self.movement_control_loop)  # 10Hz
        self.status_timer = self.create_timer(1.0, self.publish_status_update)  # 1Hz
        
        self.get_logger().info('Forward Movement Node started')
        
        # Start immediately if not waiting for detection
        if not self.get_parameter('wait_for_detection').value:
            self.start_movement()
    
    def detection_complete_callback(self, msg):
        """Callback when gate detection is complete"""
        if msg.data and not self.detection_complete:
            self.detection_complete = True
            self.get_logger().info('Gate detected - starting forward movement')
            self.start_movement()
    
    def start_movement(self):
        """Initialize forward movement sequence"""
        if self.movement_active or self.movement_complete:
            return
            
        self.movement_active = True
        self.start_time = time.time()
        self.get_logger().info('Starting forward movement towards gate')
        self.publish_status('STARTED: Forward movement initiated')
    
    def movement_control_loop(self):
        """Main movement control loop - CONTINUOUS FORWARD MOVEMENT"""
        if not self.movement_active:
            return
        
        # Continue forward movement FOREVER (no time limit)
        vel_msg = Twist()
        vel_msg.linear.x = self.get_parameter('forward_speed').value  # Forward
        vel_msg.linear.y = 0.0
        vel_msg.linear.z = 0.0
        vel_msg.angular.x = 0.0
        vel_msg.angular.y = 0.0
        vel_msg.angular.z = 0.0
        
        self.velocity_publisher.publish(vel_msg)
        
        # Calculate elapsed time and distance for status updates
        current_time = time.time()
        elapsed_time = current_time - self.start_time
        distance_moved = self.get_parameter('forward_speed').value * elapsed_time
        
        # Publish continuous progress (just for status, no stopping)
        self.publish_progress(min(1.0, elapsed_time / 60.0))  # Progress over 60 seconds for display
    
    def stop_movement(self):
        """Stop all movement and mark as complete"""
        if self.movement_complete:
            return
            
        # Send stop command
        stop_msg = Twist()  # All zeros
        self.velocity_publisher.publish(stop_msg)
        
        # Update state
        self.movement_active = False
        self.movement_complete = True
        
        # Calculate final stats
        total_time = time.time() - self.start_time if self.start_time else 0
        distance_moved = self.get_parameter('forward_speed').value * total_time
        
        self.get_logger().info(f'Forward movement complete - Time: {total_time:.1f}s, Distance: {distance_moved:.2f}m')
        self.publish_status(f'COMPLETE: Moved {distance_moved:.2f}m forward in {total_time:.1f}s')
        self.publish_progress(1.0)
        self.publish_completion(True)
        
        # Mission complete message
        self.get_logger().info('🎉 AUTONOMOUS NAVIGATION MISSION COMPLETE! 🎉')
    
    def publish_status_update(self):
        """Periodic status updates"""
        if not self.movement_active:
            if self.get_parameter('wait_for_detection').value and not self.detection_complete:
                status = 'WAITING: For gate detection signal'
            else:
                status = 'IDLE: Ready to start forward movement'
        elif self.movement_active:
            elapsed = time.time() - self.start_time
            distance = self.get_parameter('forward_speed').value * elapsed
            status = f'MOVING CONTINUOUSLY: {elapsed:.1f}s elapsed, {distance:.2f}m forward - NO TIME LIMIT'
        else:
            status = 'STOPPED: Movement interrupted'
        
        self.publish_status(status)
    
    def publish_status(self, message):
        """Publish status message"""
        msg = String()
        msg.data = message
        self.status_publisher.publish(msg)
    
    def publish_progress(self, progress):
        """Publish movement progress (0.0 to 1.0)"""
        msg = Float64()
        msg.data = progress
        self.progress_publisher.publish(msg)
    
    def publish_completion(self, complete):
        """Publish completion flag"""
        msg = Bool()
        msg.data = complete
        self.complete_publisher.publish(msg)
    
    def emergency_stop(self):
        """Emergency stop for external triggers"""
        self.get_logger().warn('Emergency stop triggered')
        stop_msg = Twist()
        self.velocity_publisher.publish(stop_msg)
        self.movement_active = False
        self.publish_status('STOPPED: Emergency stop')


def main(args=None):
    rclpy.init(args=args)
    
    node = ForwardMovementNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Forward Movement Node stopped')
        node.emergency_stop()
    
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()