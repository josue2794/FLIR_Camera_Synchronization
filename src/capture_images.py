# Este script inicializa las cámaras y captura las imágenes
# con las cámaras FLIR.

import os
import sys
import PySpin
import threading
import time

def configure_main_camera_trigger(cam):
    cam.Init()
    # Ensure trigger mode off
    # The trigger must be disabled in order to configure whether the source
    # is software or hardware.

    cam.LineSelector.SetValue(PySpin.LineSelector_Line2)

    cam.V3_3Enable.SetValue(True)
    
    cam.DeInit()

def configure_secundary_camera(cam):
    cam.Init()
    cam.TriggerSource.SetValue(PySpin.TriggerSource_Line3)
    cam.TriggerOverlap.SetValue(PySpin.TriggerOverlap_ReadOut)
    cam.TriggerMode.SetValue(PySpin.TriggerMode_On)
    cam.DeInit()

def retrieve_timestamp(image, nodemap):

    node_device_information = PySpin.CCategoryPtr(nodemap.GetNode('DeviceInformation'))
    #Timestamp
    chunk_data = image.GetChunkData()
    timestamp = chunk_data.GetTimestamp()

    #Camera ID
    cam_id = ''
    if PySpin.IsAvailable(node_device_information) and PySpin.IsReadable(node_device_information):
        features = node_device_information.GetFeatures()
        node_feature = PySpin.CValuePtr(features[0])
        cam_id = node_feature.GetName()

    return ('%s_%s' % (cam_id, timestamp))

def acquire_images(cam_list):
    """
    Acquires all the images from the three cameras
    Uses the hardware trigger to capture the images
    Saves the images to disk with the format cam_id_timestamp
    """

    try:
        result = True

        for i, cam in  enumerate(cam_list.reverse()):
            # Reverse the list so the master camera will be the last to begin the acquisition.
            # Set the acquisition mode to continuous.
            node_acquisition_mode = PySpin.CEnumerationPtr(cam.GetNodeMap().GetNode('AcquisitionMode'))
            if not PySpin.IsAvailable(node_acquisition_mode) or not PySpin.IsWritable(node_acquisition_mode):
                return False

            node_acquisition_mode_continuous = node_acquisition_mode.GetEntryByName('Continuous')
            if not PySpin.IsAvailable(node_acquisition_mode_continuous) or not PySpin.IsReadable(
                    node_acquisition_mode_continuous):
                print('Unable to set acquisition mode to continuous (entry \'continuous\' retrieval %d). \
                Aborting... \n' % i)
                return False

            acquisition_mode_continuous = node_acquisition_mode_continuous.GetValue()
            node_acquisition_mode.SetIntValue(acquisition_mode_continuous)

            cam.BeginAcquisition()

        while (True):
            

def capture (cam_list, rate):
    result = True
    cam_0 = cam_list[0] #main camera
    cam_1 = cam_list[1]
    #cam_2 = cam_list[2]

    for i, cam in enumerate(cam_list):
        # Initialize camera
        cam.Init()

    result &= acquire_images(cam_list)

    for cam in cam_list:
        cam.DeInit()

    return result



def main():
    #Capture the arguments
    #time = sys.argv[1]
    rate = sys.argv[2]

    result = True

    #Setup the FLIR environment
    system = PySpin.System.GetInstance()
    cam_list = system.GetCameras()
    num_cams = cam_list.GetSize()

    print ("There are %d cameras connected", num_cams)

    if (num_cams == 0):
        print ("Connect some FLIR cameras")
        cam_list.Clear()
        system.ReleaseInstance()
        return False

    #Configure the trigger of the cameras
    cam_list [0].configure_main_camera_trigger()
    for i, cam in enumerate(cam_list[1:]):
        cam.configure_secundary_camera()

    #Once the cameras are configured, images can begin to be captured
    #Once we  know the cameras exist and the trigger is configured
    #We can begin to capture
    fps = 30 # This should be decided from the user
    capture (cam_list, fps)



    del cam
    cam_list.Clear()
    system.ReleaseInstance()

    return result


if __name__ == '__main__':
    main()