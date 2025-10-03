#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import String, Bool, Float64
from sensor_msgs.msg import NavSatFix
import time

class DownwardMovementNode(Node):
    def __init__(self):
        super().__init__('downward_movement_node')
        
        # Publishers
        self.velocity_publisher = self.create_publisher(
            Twist,
            '/mavros/setpoint_velocity/cmd_vel_unstamped',
            10
        )
        self.status_publisher = self.create_publisher(String, '/navigation/movement_status', 10)
        self.progress_publisher = self.create_publisher(Float64, '/navigation/movement_progress', 10)
        self.complete_publisher = self.create_publisher(Bool, '/navigation/movement_complete', 10)
        
        # Subscribers
        self.guided_ready_subscriber = self.create_subscription(
            Bool,
            '/navigation/guided_ready',
            self.guided_ready_callback,
            10
        )
        self.altitude_subscriber = self.create_subscription(
            Float64,  # Or whatever altitude topic you have
            '/mavros/global_position/rel_alt',
            self.altitude_callback,
            10
        )
        
        # Parameters
        self.declare_parameter('downward_speed', -2.2)  # m/s (negative = down)
        self.declare_parameter('movement_duration', 2.6)  # seconds
        self.declare_parameter('wait_for_guided', True)  # Wait for guided mode confirmation
        
        # State variables
        self.guided_ready = False
        self.movement_active = False
        self.movement_complete = False
        self.start_time = None
        self.initial_altitude = None
        self.current_altitude = None
        
        # Timers
        self.movement_timer = self.create_timer(0.1, self.movement_control_loop)  # 10Hz
        self.status_timer = self.create_timer(1.0, self.publish_status_update)  # 1Hz
        
        self.get_logger().info('Downward Movement Node started')
        
        # Start immediately if not waiting for guided mode
        if not self.get_parameter('wait_for_guided').value:
            self.start_movement()
    
    def guided_ready_callback(self, msg):
        """Callback when guided mode is ready"""
        if msg.data and not self.guided_ready:
            self.guided_ready = True
            self.get_logger().info('Received guided ready signal - starting movement')
            self.start_movement()
    
    def altitude_callback(self, msg):
        """Track altitude changes"""
        self.current_altitude = msg.data
        if self.initial_altitude is None:
            self.initial_altitude = msg.data
            self.get_logger().info(f'Initial altitude recorded: {self.initial_altitude:.2f}m')
    
    def start_movement(self):
        """Initialize movement sequence"""
        if self.movement_active or self.movement_complete:
            return
            
        self.movement_active = True
        self.start_time = time.time()
        self.get_logger().info('Starting downward movement')
        self.publish_status('STARTED: Downward movement initiated')
    
    def movement_control_loop(self):
        """Main movement control loop"""
        if not self.movement_active or self.movement_complete:
            return
        
        current_time = time.time()
        elapsed_time = current_time - self.start_time
        duration = self.get_parameter('movement_duration').value
        
        # Check if movement should continue
        if elapsed_time < duration:
            # Continue downward movement
            vel_msg = Twist()
            vel_msg.linear.x = 0.0
            vel_msg.linear.y = 0.0
            vel_msg.linear.z = self.get_parameter('downward_speed').value
            vel_msg.angular.x = 0.0
            vel_msg.angular.y = 0.0
            vel_msg.angular.z = 0.0
            
            self.velocity_publisher.publish(vel_msg)
            
            # Publish progress
            progress = elapsed_time / duration
            self.publish_progress(progress)
            
        else:
            # Movement complete - stop
            self.stop_movement()
    
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
        depth_moved = self.initial_altitude - self.current_altitude if self.initial_altitude and self.current_altitude else 0
        
        self.get_logger().info(f'Movement complete - Time: {total_time:.1f}s, Depth: {depth_moved:.2f}m')
        self.publish_status(f'COMPLETE: Moved {depth_moved:.2f}m in {total_time:.1f}s')
        self.publish_progress(1.0)
        self.publish_completion(True)
    
    def publish_status_update(self):
        """Periodic status updates"""
        if not self.movement_active and not self.movement_complete:
            if self.get_parameter('wait_for_guided').value and not self.guided_ready:
                status = 'WAITING: For guided mode confirmation'
            else:
                status = 'IDLE: Ready to start movement'
        elif self.movement_active:
            elapsed = time.time() - self.start_time
            duration = self.get_parameter('movement_duration').value
            remaining = duration - elapsed
            depth = self.initial_altitude - self.current_altitude if self.initial_altitude and self.current_altitude else 0
            status = f'MOVING: {elapsed:.1f}s elapsed, {remaining:.1f}s remaining, {depth:.2f}m depth'
        else:
            status = 'COMPLETE: Movement finished'
        
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
    
    node = DownwardMovementNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Downward Movement Node stopped')
        node.emergency_stop()
    
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()