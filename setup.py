from setuptools import setup, find_packages

setup(
    name='sentinel-mrhat-cam',
    version='1.1.11',
    description='Testing python code for Starling detection project',
    author='Ferenc Nandor Janky, Attila Gombos, Nyiri Levente, Nyitrai Bence',
    author_email='info@effective-range.com',
    packages=find_packages(),
    scripts=['bin/sentinel_mrhat_cam.sh', 'bin/sentinel_mrhat_cam_main.py'],
    data_files=[('config', ['config/sentinel_app_config.json', 'config/sentinel_log_config.yaml'])],
    install_requires=['picamera2', 'PyYAML', 'pillow', 'pytz', 'paho-mqtt', 'numpy'],
)
