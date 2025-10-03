#!/usr/bin/env python3
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='navigation_package',
            executable='guided_node',
            name='guided_mode_client',
            output='screen'
        ),
        Node(
            package='navigation_package',
            executable='downwards_node',
            name='downward_movement',
            output='screen'
        ),
        Node(
            package='navigation_package',
            executable='rotation_node',
            name='rotation_search',
            output='screen'
        ),
        Node(
            package='navigation_package',
            executable='forward_node',
            name='forward_movement',
            output='screen'
        )
    ])