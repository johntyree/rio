from setuptools import setup

setup(name='rio',
      version='0.0.1',
      packages=['rio'],
      author='John Tyree',
      author_email='johntyree@gmail.com',
      license='GPLv3+',
      url='http://github.com/johntyree/rio',
      description="Stream ShoutCast stations, skipping ad content.",
      keywords="shoutcast radio",
      long_description=open('README.md').read(),
      entry_points={
          'console_scripts': [
              'rio = rio.rio:main',
          ],
      },
      classifiers=[
          "Development Status :: 3 - Alpha",
          "License :: OSI Approved :: "
          "GNU General Public License v3 or later (GPLv3+)",
          "Topic :: Multimedia :: Sound/Audio :: Analysis",
          "Topic :: Multimedia :: Sound/Audio :: Capture/Recording",
          "Topic :: Utilities",
      ],
      )
