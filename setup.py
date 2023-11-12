from setuptools import setup, Command

from distutils.command.build_py import build_py

from amlfs_hsm_tools import __version__

setup(name='amlfs_hsm_tools',
      version=__version__,
      description='Python package to allow AMLFS HSM operations',
      long_description='',
      url='https://github.com/wolfgang-desalvador/amlfs-hsm-tools',
      license='MIT License',
      author='Wolfgang De Salvador',
      author_email='',
      packages=['amlfs_hsm_tools'],
      provides=['amlfs_hsm_tools'],
      install_requires=['azure-storage-blob', 'azure-identity'],
      cmdclass={'build_py': build_py},
      entry_points={'console_scripts': ['amlfs_hsm_tools = amlfs_hsm_tools.main:main']},
      classifiers=[
                   'Development Status :: 3 - Alpha',
                   'Programming Language :: Python',
                   'License :: OSI Approved :: MIT License',
                  ],
     )