import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyAutomation",
    version="0.0.1",
    author="Bruce Link",
    author_email="bruce.j.e.link@gmail.com",
    description="A automation framework for building control and automation projects.",
    long_description="pyAutomation is a library of classes that allows for building of " + \
        "complex control systems. It provides data structures, process " + \
        "supervision utilities, and I/O drivers for various protocols." ,
    long_description_content_type="text/markdown",
    url="https://github.com/BruceJL/pythonAutomationFramework",
    # packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GPL v3",
        "Operating System :: OS Independent",
    ],
    packages=[
      'pyAutomation.DataObjects',
      'pyAutomation.Devices',
      'pyAutomation.Hmi',
      'pyAutomation.Supervisory',
      'pyAutomation.tests',
    ],
    scripts=[
      'bin/Supervisor.py',
      'bin/hmi.py',
    ],
    py_modules=[
      "email",
      "smtplib",
      "typing",
      "datetime",
      "logging",
      "ruamel",
    ],
)
