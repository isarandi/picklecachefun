from setuptools import setup

setup(
    name='picklecachefun',
    version='0.1.0',
    author='István Sárándi',
    author_email='istvan.sarandi@uni-tuebingen.de',
    packages=['picklecachefun'],
    license='LICENSE',
    description='Cache function call results to disk using pickle',
    python_requires='>=3.6',
    install_requires=['loguru']
)
