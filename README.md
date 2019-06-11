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



Establish Communication
-----------------------
1. Start the ICS Server
2. Start 3D Slicer
3. In the MRTracking, click the "Connector" menu, and select"Create new IGTLConnector".
4. Set hostname and port number.
5. Click "Active" check box. Once it is connected, 3D Slicer will send "INITIALIZATION" command to the ICS.

Start Tracking
--------------


Send Surface Model
------------------


Registration
------------


















