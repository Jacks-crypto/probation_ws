from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'navigation_package'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
    ('share/ament_index/resource_index/packages',
        ['resource/' + package_name]),
    ('share/' + package_name, ['package.xml']),
    (os.path.join('share', package_name, 'launch'), ['launch/navigation.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='samson',
    maintainer_email='samson@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'guided_node = navigation_package.guided_node:main',
            'downwards_node = navigation_package.downwards_node:main',
            'rotation_node = navigation_package.rotation_node:main',
            'forward_node = navigation_package.forward_node:main',
        ],
    },
)