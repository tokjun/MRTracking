MRTracking
==============
Slicer Module for MR Tracking


Prerequisite
============

This module has been tested on Slicer 4.11.x (2020-03-15).

Installation
============

3D Slicer Extensions
--------------------

After installing 3D Slicer, add the following extensions (plug-ins) from the Extension Manager:

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

NavX IGTL (Optional) 
--------------------

[NavXIGTL](https://github.com/tokjun/NavXIGTL) is a message converter that imports tracking data from the NavX system and send them to 3D Slicer using [the OpenIGTLink messaging protocol](http://openigtlink.org/). The MRTracking module can recieve tracking data directory from NavXIGTL. See the NavXIGTL repository for the detail.


NavX IGTL (Optional) 
--------------------

[NavXIGTL](https://github.com/tokjun/NavXIGTL) is a message converter that imports tracking data from the NavX system and send them to 3D Slicer using [the OpenIGTLink messaging protocol](http://openigtlink.org/). The MRTracking module can recieve tracking data directory from NavXIGTL. See the NavXIGTL repository for the detail.



Usage
=====

Network Setting
---------------
The following network configuration is assumed:
- Siemens MRI Host: 192.168.2.1
- Slicer Workstation: 192.168.2.5
- NavXIGTL: same as the Slicer workstation (192.168.2.5)


Make sure that port 18944 TCP is open. To check the network connection, open the command prompt on the MRI host (Advanced User required), and ping the Slicer workstation:

~~~~
> PING 192.168.2.5
~~~~


Setting Up 3D Slicer
--------------------
- Open 3D Slicer
- Choose "IGT" -> "MRTracking" under the modules menu.
- MRI Connection
  - Under the "Connection (OpenIGTLink) -> Connector 1 (MRI)" section, click the "Connector" pull-down menu and choose "Create new IGTLConnector"
  - Make sure to specify "18944" (default) for the Port.
  - Click the "Active" check box.
- NavX Connection 
  - Under the "Connection (OpenIGTLink) -> Connector 2 (NavX)" section, click the "Connector" pull-down menu and choose "Create new IGTLConnector"
  - Make sure to specify "18945" (default) for the Port.
  - Click the "Active" check box.
  
If you are running 3D Slicer with a simulator offline, please set up  the MRI connection only. The simulator will connect to the same port, and stream both MRI and NavX tracking data through the same connection.


Starting NavX
-------------
Please refer to [NavXIGTL](https://github.com/tokjun/NavXIGTL) (The page is in a private repository - contact [Junichi Tokuda](tokuda@bwh.harvard.edu) to obtain access). NavXIGTL will connect to the NavX connection set up above.

Starting MR Tracking Sequence
-----------------------------
Setup the tracking sequence and start the scan. If the tracking sequence is connected to the 3D Slicer properly, the catheter model should appear on the screen. You may not seen the model during prescan or while the catheter is outside the imaging volume.


Testing with Simulator
======================

You can test the MRTracking module using [Tracking Simulator](https://github.com/tokjun/MRCatheterTrackingSim) with the following steps. We assume that both simulator and 3D Slicer are running on the same computer.

First, prepare a log file. An example file is available [here](https://github.com/tokjun/MRCatheterTrackingSim/raw/master/ExampleCombinedLog.txt) or can be found in the Tracking Simulator repository. Each line of the file must follow the following format:

~~~~
<Tracking Device Name> <Time Stamp> <Coil #0 X> <Coil #0 Y> <Coil #0 Z> <Coil #1 X> <Coil #1 Y> <Coil #1 Z> <Coil #2 X> <Coil #2 Y> <Coil #2 Z> <Coil #3 X> <Coil #3 Y> <Coil #3 Z>
~~~~

Values are separated by ' ' (space). The following example sends tracking data from two NavX catheters ("NavX-Cho0" and "NavX-Cho1") and one MR tracking catheter ("WWTracker").

~~~~
"NavX-Ch0" 1583473028.478 12.23725 -143.580765 1.973752 22.735201 -144.134094 5.221673 61.540863 -132.797699 21.337418 77.927071 -122.453781 33.634754
"NavX-Ch1" 1583473028.478 15.621306 -13.048416 -321.403259 12.890963 -12.624561 -325.807037 13.740788 -13.582432 -323.989197 5.547066 -14.034599 -338.358307
"WWTracker" 1583473028.516 -11.146388 108.658325 -12.138319 1.921456 110.202103 -17.619915 12.683863 106.303223 -24.614313 15.378861 102.014465 -35.059078
"NavX-Ch0" 1583473028.527 12.23725 -143.580765 1.973752 22.735201 -144.134094 5.221673 61.540863 -132.797699 21.337418 77.927071 -122.453781 33.634754
"NavX-Ch1" 1583473028.528 15.621306 -13.048416 -321.403259 12.890963 -12.624561 -325.807037 13.740788 -13.582432 -323.989197 5.547066 -14.034599 -338.358307
"NavX-Ch0" 1583473028.529 12.23725 -143.580765 1.973752 22.735201 -144.134094 5.221673 61.540863 -132.797699 21.337418 77.927071 -122.453781 33.634754
"NavX-Ch1" 1583473028.529 15.621306 -13.048416 -321.403259 12.890963 -12.624561 -325.807037 13.740788 -13.582432 -323.989197 5.547066 -14.034599 -338.358307
"WWTracker" 1583473028.557 -11.531088 108.270836 -11.745233 2.305668 110.588936 -18.014011 11.916069 105.531418 -23.827183 14.22732 100.859711 -33.882656
"WWTracker" 1583473028.559 -11.531088 108.270836 -11.745233 1.537006 111.362717 -18.802317 11.531258 105.917931 -24.219872 13.457215 101.631363 -34.664532

...

~~~~

Make sure to have the log file ('ExampleCombinedLog.txt') in your working folder. Also it would be convenient if the executable file 'TrackingDataClient' in a directory registered in the PATH environment variable, or set up an alias. On the console, run the following commands to start the tracking simulator.

~~~~
$ cd <working directory>
$ TrackingDataClient -f t -m 1111 -D ExampleCombinedLog.txt
~~~~

The simulator will start streaming the tracking data as soon as it is connected to 3D Slicer.


Configuring Catheters
---------------------

Once 3D Slicer has recieved the first frame a tracking device, you can configure the catheter tracked by the device. Please note that, even if multiple tracking devices (e.g., MR and NavX) track the same catheter, this plug-in module treat them separately as independent catheters. The catheters can be registered using the Point-to-Point registration feature described below.

To configure the catheter:
- In "Tracking Node" -> "Tracking Node":
  - Click the "TrackingData" pull-down menu and choose the name of the tracking device you would like to configure.
  - Click the "Active" check box.
- In "Tracking Node -> "Coil Selection":
  - Click the check boxes for "CH 1" - "CH 4" for "Cath 0 Active Coils"
  - Make sure that the other check boxes are unchecked.
  - Check "Show Coil Labels," if you want to see the label for each coil in the viewer.
The catheter should appear on the 3D viewer.

There are other parameters you can configure:

- In "Tracking Node" -> "Catheter Configuration":
  - Diameter
  - Opacity 
  - The position of each coil on the catheter (as the distance along the catheter from the tip). This information will be used for point-to-point registration.
- In "Tracking Node" -> "Coordinate System":
  - The direction of the coordinate in each direction.


























