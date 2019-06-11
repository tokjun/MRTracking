MRTracking
==============
Slicer Module for MR Tracking


Prerequisite
============

This module has been tested only on Slicer 4.8.1. The latest version (4.10.x) may not work due to the implementation of the OpenIGTLink module.
- [Download Page for Slicer 4.8.1](http://slicer.kitware.com/midas3/folder/274)

Installation
============

3D Slicer Extensions
--------------------

After installing 3D Slicer, add the following extensions (plug-ins) from the Extension Manager:

- CurveMaker
- SlicerIGT

After adding those extensions, you will be asked to restart 3D Slicer.

MR Tracking Module
------------------

[MR Tracking Module](https://github.com/tokjun/MRTracking) is currently not listed in the Extension Manager, and will need to be installed manually with the following steps:

- Download the source code by either:
  - downloading a zipped archive from [this link](https://github.com/tokjun/MRTracking/archive/master.zip)
  - Cloning the repository using the Git command:

~~~~
$ git clone https://github.com/tokjun/MRTracking
~~~~

- Extract the source tree if you have downloaded the zipped archive. Save the source tree in your local disk.
- Launch 3D Slicer and open "Application Settings" form the "Edit" menu.
- Choose "Modules" from the list on the left of the Application Setting window.
- In the "Additional module paths," click the "Add" button. If "Add" button is hiddne, click the ">>" button on the right edge of the module list.
- Choose the "MRTracking" under the source tree. Note that there is a child "MRTracking" folder under the parent "MRTracking" folder. Choose the child one.
- The module path that shows up on the list would look like: "/Users/junichi/modules/MRTracking/MRTracking" (Confirm that there is "MRTracking" under "MRTracking".
- Restart 3D Slicer.
- If the module is installed properly, it should be listed under "IGT" on the Modules menu.

Usage
=====

Network Setting
---------------
The following network configuration is assumed:
- Siemens MRI Host: 192.168.2.1
- Slicer Workstation: 192.168.2.5

Make sure that port 18944 TCP is open. To check the network connection, open the command prompt on the MRI host (Advanced User required), and ping the Slicer workstation:

~~~~
> PING 192.168.2.5
~~~~


Setting Up 3D Slicer
--------------------
- Open 3D Slicer
- Choose "IGT" -> "MRTracking" under the modules menu.
- Click the "Connector" pull-down menu and choose "Create new IGTLConnector"
- Make sure to specify "18944" (default) for the Port.
- Click the "Active" check box.


Starting MR Tracking Sequence
-----------------------------
Setup the tracking sequence and start the scan. If the tracking sequence is connected to the 3D Slicer properly, the catheter model should appear on the screen. You may not seen the model during prescan or while the catheter is outside the imaging volume.


Testing with Simulator
======================

You can test the MRTracking module using [Tracking Simulator](https://github.com/tokjun/MRCatheterTrackingSim) with the following steps. We assume that both simulator and 3D Slicer are running on the same computer.


Setting Up 3D Slicer
--------------------
- Open 3D Slicer
- Choose "IGT" -> "MRTracking" under the modules menu.
- Click the "Connector" pull-down menu and choose "Create new IGTLConnector"
- Make sure to specify "18944" (default) for the Port.
- Click the "Active" check box.


Starting Simulator
------------------
To start the simulator from the terminal on Linux/Mac

~~~~
$ cd <SIMULATOR_PATH>/
$ ./TrackingDataClient localhost 18944 5 <DATA_PATH>/TestTracking.log
~~~~

"SIMULATOR_PATH" is the path to the folder where the executable file is placed, whereas "DATA_PATH" is the path to the folder where the tracking log file ("TestTracking.log") is placed. "TestTracking.log" comes along with the source code for the simulator.

On Windows,

~~~~
> cd <path to the simulator>
> TrackingDataClient localhost 18944 5 <path to the test tracking data>\TestTracking.log
~~~~




















