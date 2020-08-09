from setuptools import setup

setup(
    name='qtile-widget-livefootballscores',
    packages=['livefootballscoresy'],
    version='0.1.0',
    description='A qtile widget to show live football scores.',
    author='elParaguayo',
    url='https://github.com/elparaguayo/qtile-widget-livefootballscores',
    license='MIT',
    install_requires=['qtile>0.14.2', 'dateutil']
)
