# Author: Kyle Mede, May 2010. 
# classes moved geminiTools.py->managers.py April 2011

import os, sys

import tempfile
import astrodata
from astrodata.adutils import gemLog
from astrodata.AstroData import AstroData
from astrodata import Errors
from gempy import geminiTools as gt
from gempy import string

class CLManager(object):
    """
    This is a class that will take care of all the preparation and wrap-up 
    tasks needed when writing a primitive that wraps a IRAF CL routine.
        
    """
    # The original names of the files at the start of the 
    # primitive which called CLManager
    _preCLimageNames = None
    _preCLrefnames = None
    # The version of the names for input to the CL script
    imageInsCLdiskNames = None
    refInsCLdiskNames = None
    arrayInsCLdiskNames = None
    # Preparing other 'global' variables to be accessed throughout this class
    # Ins
    imageIns = None
    refIns = None
    arrayIns = None
    imageInsListName = None
    refInsListName = None
    arrayInsListName = None
    # Outs
    imageOuts = None
    refOuts = None
    arrayOuts = None
    numArrayOuts = None
    imageOutsNames = None
    refOutsNames = None
    arrayOutsNames = None
    imageOutsListName = None
    refOutsListName = None
    arrayOutsListName = None
    # Others
    suffix = None
    funcName = None
    status = None
    combinedImages = None
    templog = None
    log = None
     
    def __init__(self, imageIns=None, refIns=None, arrayIns=None, suffix=None,  
                  imageOutsNames=None, refOutsNames=None, numArrayOuts=None,
                 combinedImages=False, funcName=None, log=None):
        """
        This instantiates all the globally accessible variables (within the 
        CLManager class) and prepares the inputs for use in CL scripts by 
        temporarily writing them to disk with temporary names.  
        
        By using temporary filenames for the on disk copies 
        of the inputs, we avoid name collisions and by only temporarily writing
        them to disk, the 'user level functions' that utilize the CLManager
        will appear as if their processing is all done in memory.
       
        NOTE: all input images must have been prepared.
        
        :param imageIns: Input image(s). 
                         Use the imageInsFiles function to return the file names
                         for the temporary disk file versions of these inputs
                         in any desired form for input to IRAF.
        :type imageIns: astrodata object(s); Either as single instance, a list 
                        of them, or None.
        
        :param refIns: Input reference image(s). This may be used for any 
                       second set of input images.
                       Use the refInsFiles function to return the file names
                       for the temporary disk file versions of these inputs
                       in any desired form for input to IRAF.
        :type adIns: astrodata object(s); Either as single instance, a list of 
                     them, or None.
        
        :param arrayIns: Input array(s) of object locations in the images or 
                         any other arrays needed for input to IRAF.
                         Use the arrayInsFiles function to return the file names
                         for the temporary disk file versions of these inputs
                         in any desired form for input to IRAF.
        :type arrayIns: Python list-of-lists with each element of an array being 
                        an entire line to be written to an input file for IRAF; 
                        Either list of input arrays or None.
                        Format: 
                        [[list1-line1,list1-line2,...],[list2-line2,list2-line2,
                        ...],...]
                        another way of looking at it if lists are objects:
                        [LIST1, LIST2,...]
                        Even if only a single list is to be passed in, it MUST  
                        be within another set of [].
        
        :param suffix: Desired suffix to be added to input filenames to create 
                       the output names.
                       Use this option if not using the imageOutsNames/
                       refOutsNames parameters for the output names.
        :type suffix: String
        
        :param imageOutsNames: Desired final name(s) of output image(s) from 
                               IRAF.
                               Use the imageOutsFiles function to return these 
                               file names in any desired form for input to IRAF.
        :type imageOutsNames: String(s); Either a single string, a list of them 
                              of length matching the expected number of output 
                              images from IRAF, or None. If None, the list will 
                              be populated automatically by use of the 
                              'combinedImages' flag and post pending the 
                              'suffix' parameter onto the input image names.
                             
                        
        :param refOutsNames: Desired final name(s) of output reference image(s) 
                             from IRAF. 
                             These could be used to name any second set of 
                             output images.
                             Use the refOutsFiles function to return these 
                             file names in any desired form for input to IRAF.
        :type refOutsNames: String(s); Either a single string, a list of them of 
                            length matching the expected number of output 
                            reference images from IRAF, or None.
                            If None, no reference image outputs from IRAF will 
                            be handled by the CLManager.         
        
        :param numArrayOuts: The number of expected arrays to be output by IRAF.
                             The output array names will be automatically 
                             created.
                             Use the arrayOutsFiles function to return these
                             file names in any desired form for input to IRAF.
        :type numArrayOuts: int or None.
                            If 0 or None, no array outputs from IRAF will be 
                            handled by the CLManager.
        
        :param combinedImages: A flag to indicated that the input images of 
                               imageIns will be combined to form one single 
                               image output from IRAF.
                               The use of this parameter is optional and is  
                               overridden by providing imageOutsNames. 
                               No parallel version of this argument exists for
                               refIns.
        :type combinedImages: Python boolean (True/False)
        
        :param funcName: Name of the Python function using the CLManager. This 
                         is used to name the temporary files on disk for input 
                         to IRAF; so using the function name makes it easier to 
                         track down any errors that might occur.
        :type funcName: String
        
        :param log: logger object to send log messges to
        :type log: A gemLog object from astrodata/adutils/gemLog.py .
                   It is an upgraded version of the Python logger for use 
                   with all new scripts in gemini_python/ .
                   If None, then a null logger object will be created and used
                   (ie, no log file, no messages to screen).  
        
        """
        # Casting the two types of input images to lists for internal use, 
        # if not None
        if imageIns!=None:
            if isinstance(imageIns,list):
                self.imageIns = imageIns
            else:
                self.imageIns = [imageIns]
        if refIns!=None:  
            if isinstance(refIns,list):
                self.refIns = refIns
            else:
                self.refIns = [refIns]
        # Check that the inputs have been prepared, else then CL scripts might
        # not work correctly.
        self.status = True
        if imageIns!=None:
            for ad in self.imageIns:
                if (ad.phu_get_key_value('GPREPARE')==None) and \
                   (ad.phu_get_key_value('PREPARE')==None):
                    self.status = False
        if refIns!=None:
            for ad in self.refIns:
                if (ad.phu_get_key_value('GPREPARE')==None) and \
                   (ad.phu_get_key_value('PREPARE')==None):
                    self.status = False
        # All inputs prepared, then continue, else the False status will trigger
        # the caller to not proceed further.
        if self.status:
            # Create a temporary log file object
            self.templog = tempfile.NamedTemporaryFile() 
            if not log:
                # Get the REAL log file object
                self.log = gemLog.getGeminiLog()
            else:
                self.log = log
            # load these to global early as they are needed below
            self.suffix = suffix
            # start up global lists
            if imageIns!=None:
                self._preCLimageNames = []
                self.imageInsCLdiskNames = []
            if refIns!=None:
                self._preCLrefnames = []
                self.refInsCLdiskNames = []
            if arrayIns!=None:
                self.arrayInsCLdiskNames = []
            # load up the rest of the inputs to being global
            self.imageOutsNames = imageOutsNames
            self.refOutsNames = refOutsNames
            self.combinedImages = combinedImages
            self.funcName = funcName
            self.arrayIns = arrayIns
            self.numArrayOuts = numArrayOuts
            # now that everything is loaded to global make the uniquePrefix
            self.prefix = 'tmp'+ str(os.getpid())+self.funcName
            # now the preCLwrites can load up the input lists and write 
            # the temp files to disk
            self.preCLwrites()
     
    def arrayInsFiles(self, type=''):
        """
        The function to get the file names for the temporary files written to 
        disk for the arrayIns as either a string (or comma-separated string if 
        input was a list), a list of the filenames, or a list file. 
        These files are required to be on disk by IRAF and the file names are 
        automatically created when the CLManager is instantiated based on the 
        funcName parameter and the array location in the 'arrayIns' list.
        
        :param type: Desired form of the temp filenames on disk for arrayIns.
        :type type: 'string' for filenames as a string 
                    (comma-separated if input was a list),
                    'list' for filenames as strings in a python list, or
                    'listFile' for a IRAF type list file.
        """
        if type!='':
            if type=='string':
                return ','.join(self.arrayInsCLdiskNames)
            if type=='list':
                return self.arrayInsCLdiskNames
            if type=='listFile':
                arrayInsListName = gt.listFileMaker(self.arrayInsCLdiskNames,
                                                    listName='arrayList'+\
                                                    str(os.getpid())+\
                                                    self.funcName)
                self.arrayInsListName = arrayInsListName
                return '@'+arrayInsListName
        else:
            raise Errors.ManagersError('Parameter "type" must not be an empty string'+
                           '; choose either "string","list" or "listFile"')    
    
    def arrayOutsFiles(self, type=''):
        """
        This function is used to return the names of the array files to be  
        written to disk by IRAF in the form desired to pass into the IRAF 
        routine call. The names of these files is automatically produced simply 
        based on the funcName parameter, the string '_arrayOut_' and the 
        integer value of the arrays location in the arrayOuts list.
        
        This function is simply for 'convenience' and can be ignored as long
        as the filenames in the CLManger.arrayOutsNames are passed into 
        IRAF properly.
        
        :param type: Desired form of the filenames on disk for refOutsNames.
        :type type: 'string' for filenames as a string 
                    (comma-separated if input was a list),
                    'list' for filenames as strings in a python list, or
                    'listFile' for a IRAF type list file.
        
        """
        # returning the arrayOutsNames contents in the form requested, else 
        # error log messsage
        if type!='':
            if type=='string':
                return ','.join(self.arrayOutsNames)
            if type=='list':
                return self.arrayOutsNames
            if type=='listFile':
                arrayOutsListName = gt.listFileMaker(list=self.arrayOutsNames,
                                    listName='arrayOutsList'+str(os.getpid())+\
                                                                self.funcName)
                self.arrayOutsListName = arrayOutsListName
                return '@'+arrayOutsListName
        else:
            raise Errors.ManagersError('Parameter "type" must not be an empty string'+
                           '; choose either "string","list" or "listFile"')
            
    
         
    def finishCL(self): 
        """ 
         Performs all the finalizing steps after CL script is ran. 
         This function is just a wrapper for postCLloads but might 
         contain more later.
         
        """    
        imageOuts, refOuts, arrayOuts = self.postCLloads()
        return (imageOuts, refOuts, arrayOuts) 
          
    def imageInsFiles(self, type=''):
        """
        The function to get the temporary files written to disk for the imageIns
        as either a string (or comma-separated string if input was a list), a 
        list of the file names, or a list file.  These files are required to 
        be on disk by IRAF and the file names are automatically created when 
        the CLManager is instantiated based on the 'funcName' parameter and 
        the original file names of the 'imageIns' astrodata objects.
        
        :param type: Desired form of the temp filenames on disk for imageIns.
        :type type: 'string' for filenames as a string 
                    (comma-separated if input was a list),
                    'list' for filenames as strings in a python list, or
                    'listFile' for a IRAF type list file.
        """
        if type!='':
            if type=='string':
                return ','.join(self.imageInsCLdiskNames)
            if type=='list':
                return self.imageInsCLdiskNames
            if type=='listFile':
                imageInsListName = gt.listFileMaker(list=self.imageInsCLdiskNames,
                                    listName='imageList'+str(os.getpid())+\
                                                                self.funcName)
                self.imageInsListName = imageInsListName
                return '@'+imageInsListName
        else:
            raise Errors.ManagersError('Parameter "type" must not be an empty string'+
                           '; choose either "string","list" or "listFile"')
            
    def imageOutsFiles(self, type=''):
        """
        This function is used to return the names of the images that will be  
        written to disk by IRAF in the form desired to pass into the IRAF 
        routine call.
        The names of these files can either be defined using
        the imageOutsNames parameter set during the CLManager initial call, or
        automatically created in one of two ways:
        1. Combine case: triggered by,
        imageOutsNames=None, combinedImages=True, suffix=<any string>.
        Then imageOutsNames will be a list with only the filename from the first 
        input of imageIns post pended by the value of suffix.
        2. Non-combine case: triggered by,
        imageOutsNames=None, combinedImages=False, suffix=<any string>.
        Then imageOutsNames will be a list with each file name of the imageIns  
        post pended by the value of suffix.
        
        This function is simply for 'convenience' and can be ignored as long
        as the imageOutsNames is set properly and its filenames are passed into 
        IRAF properly.
        
        :param type: Desired form of the filenames on disk for imageOutsNames.
        :type type: 'string' for filenames as a string 
                    (comma-separated if input was a list),
                    'list' for filenames as strings in a python list, or
                    'listFile' for a IRAF type list file.
        
        """
        # Loading up the imageOutsNames list if not done yet and params are set 
        # correctly, else error log message.
        if self.imageOutsNames==None:
            self.imageOutsNames = []
            if self.combinedImages and (self.suffix!=None):
                name = gt.fileNameUpdater(adIn=self.imageIns[0], 
                                            suffix=self.suffix)
                self.imageOutsNames.append(name)
            elif (not self.combinedImages) and (self.suffix!=None):
                for ad in self.imageIns:
                    name = gt.fileNameUpdater(adIn=ad, suffix=self.suffix)
                    self.imageOutsNames.append(name) 
            else:
                self.log.error('The "automatic" setting of imageOutsNames can '+
                        'only work if at least the suffix parameter is set')
        # The parameter was set, ie not None
        else:
            # Cast it to a list for use below
            if isinstance(self.imageOutsNames,str):
                self.imageOutsNames = [self.imageOutsNames]

        tmp_names = []
        for name in self.imageOutsNames:
            tmp_names.append(self.prefix+name)

        # returning the imageOutsNames contents in the form requested, 
        # else error log messsage
        if type!='':
            if type=='string':
                return ','.join(tmp_names)
            if type=='list':
                return tmp_names
            if type=='listFile':
                imageOutsListName = gt.listFileMaker(list=tmp_names,
                                    listName='imageOutsList'+str(os.getpid())+\
                                                                self.funcName)
                self.imageOutsListName = imageOutsListName
                return '@'+imageOutsListName
        else:
            raise Errors.ManagersError('Parameter "type" must not be an empty string'+
                           '; choose either "string","list" or "listFile"')
    
    def nbiascontam(self, adInputs, biassec=None):
        """
        This function will find the largest difference between the horizontal 
        component of every BIASSEC value and those of the biassec parameter. 
        The returned value will be that difference as an integer and it will be
        used as the value for the nbiascontam parameter used in the gireduce 
        call of the overscanSubtract primitive.
        
        :param adInputs: AstroData instance(s) to calculate the bias 
                         contamination 
        :type adInputs: AstroData instance in a list
        
        :param biassec: biassec parameter of format 
                        '[#:#,#:#],[#:#,#:#],[#:#,#:#]'
        :type biassec: string 
        
        """
        log = gemLog.getGeminiLog() 
            
        try:
            # Prepare a stored value to be compared between the inputs
            retvalue=0
            # Loop through the inputs
            for ad in adInputs:
                # Split up the input triple list into three separate sections
                biassecStrList = biassec.split('],[')
                # Prepare the to-be list of lists
                biassecIntList = []
                for biassecStr in biassecStrList:
                    # Use string.sectionStrToIntList function to convert 
                    # each string version of the list into actual integer tuple 
                    # and load it into the lists of lists
                    # of form [y1, y2, x1, x2] 0-based and non-inclusive
                    biassecIntList.append(
                                    string.sectionStrToIntList(biassecStr))
                
                # Setting the return value to be updated in the loop below    
                retvalue=0
                for ext in ad['SCI']:
                    # Retrieving current BIASSEC value                        #  THIS WHERE THE 
                    BIASSEC = ext.get_key_value('BIASSEC')                      #  bias_section()
                    # Converting the retrieved string into a integer list     #  descriptor
                    # of form [y1, y2, x1, x2] 0-based and non-inclusive      #  would be used!!!!
                    BIASSEClist = string.sectionStrToIntList(BIASSEC)     #
                    # Setting the lower case biassec list to the appropriate 
                    # list in the lists of lists created above the loop
                    biasseclist = biassecIntList[ext.extver()-1]
                    # Ensuring both biassec's have the same vertical coords
                    if (biasseclist[0]==BIASSEClist[0]) and \
                    (biasseclist[1]==BIASSEClist[1]):
                        # If overscan/bias section is on the left side of chip
                        if biasseclist[3]<50: 
                            # Ensuring right X coord of both biassec's are equal
                            if biasseclist[2]==BIASSEClist[2]: 
                                # Set the number of contaminating columns to the 
                                # difference between the biassec's left X coords
                                nbiascontam = BIASSEClist[3]-biasseclist[3]
                            # If left X coords of biassec's don't match, set  
                            # number of contaminating columns to 4 and make a 
                            # error log message
                            else:
                                log.error('right horizontal components of '+
                                          'biassec and BIASSEC did not match, '+
                                          'so using default nbiascontam=4')
                                nbiascontam = 4
                        # If overscan/bias section is on the right side of chip
                        else: 
                            # Ensuring left X coord of both biassec's are equal
                            if biasseclist[3]==BIASSEClist[3]: 
                                # Set the number of contaminating columns to the 
                                # difference between the biassec's right X coords
                                nbiascontam = BIASSEClist[2]-biasseclist[2]
                            else:
                                log.error('left horizontal components of '+
                                          'biassec and BIASSEC did not match, '+
                                          'so using default nbiascontam=4') 
                                nbiascontam = 4
                    # Overscan/bias section is not on left or right side of chip
                    # , so set to number of contaminated columns to 4 and log 
                    # error message
                    else:
                        log.error('vertical components of biassec and BIASSEC '+
                                  'parameters did not match, so using default '+
                                  'nbiascontam=4')
                        nbiascontam = 4
                    # Find the largest nbiascontam value throughout all chips  
                    # and set it as the value to be returned  
                    if nbiascontam > retvalue:  
                        retvalue = nbiascontam
                        
            return retvalue
        # If all the above checks and attempts to calculate a new nbiascontam 
        # fail, make a error log message and return the value 4. so exiting 
        # 'gracefully'.        
        except:
            log.error('An error occurred while trying to calculate the '+
                      'nbiascontam, so using default value = 4')
            return 4 
                 
    def obsmodeAdd(self, ad):
        """This is an internally used function to add the 'OBSMODE' key to the 
           inputs for use by IRAF routines in the GMOS package.
           Modes are: (IMAGE|IFU|MOS|LONGSLIT)
           
           :param ad: AstroData instance to find mode of
           :type ad: AstroData instance
        """
        types = ad.get_types()
        if 'GMOS' in types:
            try:
                if 'GMOS_IMAGE' in types:
                    typeStr = 'IMAGE'
                elif 'GMOS_IFU' in types:
                    typeStr = 'IFU'
                elif 'GMOS_MOS' in types:
                    typeStr = 'MOS'
                elif 'GMOS_LS' in types:
                    typeStr = 'LONGSLIT'
                else:######33
                    typeStr = 'LONGSLIT'##########
                ad.phu_set_key_value('OBSMODE', typeStr , 
                          'Observing mode (IMAGE|IFU|MOS|LONGSLIT)')
            except:
                raise Errors.ManagersError('Input '+ad.filename+' is not of type '+ 
                                 'GMOS_IMAGE or GMOS_IFU or GMOS_MOS or '+
                                 'GMOS_LS.')
        return ad    
    
    def obsmodeDel(self, ad):
        """This is an internally used function to delete the 'OBSMODE' key from
           the outputs from IRAF routines in the GMOS package.
           
           :param ad: AstroData instance to find mode of
           :type ad: AstroData instance
        """
        if 'GMOS' in ad.get_types():
            del ad.get_phu().header['OBSMODE']
        return ad
    
    def postCLloads(self):
        """ This function takes care of loading the image, reference and/or 
            array files output by IRAF back into memory, in the form of the 
            imageOuts, refOuts and arrayOuts variables, and deleting those disk 
            files. 
            Then it will delete ALL the temporary files created by the 
            CLManager.  If the 'OBSMODE' phu key was added during preCLwrites
            to the imageIns and/or refIns, then it will be deleted here.
            
            NOTE: all fits files loaded back into memory in the form of 
            astrodata objects (adOuts, refOuts), will be in 'update' mode.
        
        """
        # Loading any output images into imageOuts and 
        # killing off any disk files caused by them
        if self.imageOutsNames!=None:
            self.imageOuts = []
            self.log.fullinfo('Loading output images into imageOuts and'+
                              ' removing temporary files from disk.')
            for name in self.imageOutsNames:
                tmpname = self.prefix+name
                # Loading the file into an astrodata object
                ad = AstroData(tmpname, mode='update')
                ad.filename = name
                # Removing the 'OBSMODE' phu key if it is in there
                ad = self.obsmodeDel(ad)
                # appending the astrodata object to the imageOuts list to be
                # returned
                self.imageOuts.append(ad)
                # Deleting the file from disk
                os.remove(tmpname)
                self.log.fullinfo(tmpname+' was loaded into memory')
                self.log.fullinfo(tmpname+' was deleted from disk')
            if self.imageOutsListName!=None:
                os.remove(self.imageOutsListName)
                self.log.fullinfo('Temporary list '+self.imageOutsListName+
                                  ' was deleted from disk')
        # Loading any output ref images into refOuts and 
        # killing off any disk files caused by them
        if self.refOutsNames!=None:
            self.refOuts = []
            self.log.fullinfo('Loading output reference images into refOuts'+
                              ' and removing temporary files from disk.')
            for name in self.refOutsNames:
                tmpname = self.prefix+name
                # Loading the file into an astrodata object
                ad = AstroData(tmpname, mode='update')
                ad.filename = name
                # Removing the 'OBSMODE' phu key if it is in there
                ad = self.obsmodeDel(ad)
                # appending the astrodata object to the refOuts list to be
                # returned
                self.refOuts.append(ad)
                # Deleting the file from disk
                os.remove(tmpname)
                self.log.fullinfo(tmpname+' was loaded into memory')
                self.log.fullinfo(tmpname+' was deleted from disk')
            if self.refOutsListName!=None:
                os.remove(self.refOutsListName)
                self.log.fullinfo('Temporary list '+self.refOutsListName+
                                  ' was deleted from disk') 
        # Loading any output arrays into arrayOuts and 
        # killing off any disk files caused by them 
        if self.arrayOutsNames!=None:
            self.arrayOuts = []
            self.log.fullinfo('Loading output reference array into arrayOuts'+
                              ' and removing temporary files from disk.')
            for name in self.arrayOutsNames:
                # read in input array txt file to an array with each line
                # of the file is an element of the array, ie a list of lines.
                fin = open(name,'r')
                lineList = fin.readlines()
                fin.close()                
                # appending the array to the arrayOuts list to be returned
                self.arrayOuts.append(lineList)
                # Deleting the file from disk
                os.remove(name)
                self.log.fullinfo(name+' was loaded into memory')
                self.log.fullinfo(name+' was deleted from disk')
            if self.arrayOutsListName!=None:
                os.remove(self.arrayOutsListName)
                self.log.fullinfo('Temporary list '+self.arrayOutsListName+
                                  ' was deleted from disk') 
        # Killing off any disk files associated with imageIns
        if self.imageIns!=None:
            self.log.fullinfo('Removing temporary files associated with '+
                              'imageIns from disk')
            for name in self.imageInsCLdiskNames:
                # Deleting the file from disk
                os.remove(name)
                self.log.fullinfo(name+' was deleted from disk')
            if self.imageInsListName!=None:
                os.remove(self.imageInsListName)
                self.log.fullinfo('Temporary list '+self.imageInsListName+
                                  ' was deleted from disk') 
        # Killing off any disk files associated with refIns
        if self.refIns!=None:
            self.log.fullinfo('Removing temporary files associated with '+
                              'refIns from disk')
            for name in self.refInsCLdiskNames:
                # Deleting the file from disk
                os.remove(name)
                self.log.fullinfo(name+' was deleted from disk')
            if self.refInsListName!=None:
                os.remove(self.refInsListName)
                self.log.fullinfo('Temporary list '+self.refInsListName+
                                  ' was deleted from disk') 
        # Killing off any disk files associated with arrayIns
        if self.arrayIns!=None:
            self.log.fullinfo('Removing temporary files associated with '+
                              'arrayIns from disk')
            for name in self.arrayInsCLdiskNames:
                # Deleting the file from disk
                os.remove(name)
                self.log.fullinfo(name+' was deleted from disk')
            if self.arrayInsListName!=None:
                os.remove(self.arrayInsListName)
                self.log.fullinfo('Temporary list '+self.arrayInsListName+
                                  ' was deleted from disk') 
                
        return (self.imageOuts, self.refOuts, self.arrayOuts)            

    def preCLimageNames(self):
        """Just a simple function to return the value of the private member
           variable _preCLimageNames that is a list of the filenames of 
           imageIns.
        """
        return self._preCLimageNames
    
    def preCLwrites(self):
        """ The function that writes the files in memory to disk with temporary 
            names and saves the original and temporary names in lists and 
            fills out the output file name lists for any output arrays if   
            needed. The 'OBSMODE' PHU key will also be added to all input GMOS 
            images of imageIns and refIns.
        
        """
        # preparing the input filenames for temporary input image files to 
        # IRAF if needed along with saving the original astrodata filenames    
        if self.imageIns!=None:
            for ad in self.imageIns:            
                # Adding the 'OBSMODE' phu key if needed
                ad = self.obsmodeAdd(ad)
                # Load up the _preCLimageNames list with the input's filename
                self._preCLimageNames.append(ad.filename)
                # Strip off all postfixes and prefix filename with a unique 
                # prefix
                name = gt.fileNameUpdater(adIn=ad, prefix=self.prefix, 
                                                                    strip=True)
                # store the unique name in imageInsCLdiskNames for later 
                # reference
                self.imageInsCLdiskNames.append(name)
                # Log the name of this temporary file being written to disk
                self.log.fullinfo('Temporary image file on disk for input to '+
                                  'CL: '+name)
                # Write this file to disk with its unique filename 
                ad.write(name, rename=False)
        # preparing the input filenames for temperary input ref image files to 
        # IRAF if needed along with saving the original astrodata filenames
        if self.refIns!=None:
            for ad in self.refIns:            
                # Adding the 'OBSMODE' phu key if needed
                ad = self.obsmodeAdd(ad)
                # Load up the _preCLrefnames list with the input's filename
                self._preCLrefnames.append(ad.filename)
                # Strip off all suffixs and prefix filename with a unique prefix
                name = gt.fileNameUpdater(adIn=ad, prefix=self.prefix, 
                                                                    strip=True)
                # store the unique name in refInsCLdiskNames for later reference
                self.refInsCLdiskNames.append(name)
                # Log the name of this temporary file being written to disk
                self.log.fullinfo('Temporary ref file on disk for input to CL: '
                                  +name)
                # Write this file to disk with its unique filename 
                ad.write(name, rename=False)
        # preparing the input filenames for temperary input array files to 
        # IRAF if needed and writing them to disk.   
        if self.arrayIns!=None:
            count=1
            for array in self.arrayIns:
                # creating temp name for array
                name = self.prefix+'_arrayIn_'+str(count)+'.txt'
                # store the unique name in arrayInsCLdiskNames for later 
                # reference
                self.arrayInsCLdiskNames.append(name)
                # Log the name of this temporary file being written to disk
                self.log.fullinfo('Temporary ref file on disk for input to CL: '
                                  +name)
                # Write this array to text file on disk with its unique filename 
                fout = open(name,'w')
                for line in array:
                    fout.write(line)
                fout.close()
                
                count=count+1
        # preparing the output filenames for temperary output array files from 
        # IRAF if needed, no writing here that is done by IRAF.
        if (self.numArrayOuts!=None) and (self.numArrayOuts!=0):
            # create empty list of array file names to be loaded in loop below
            self.arrayOutsNames = []
            for count in range(1,self.numArrayOuts+1):
                # Create name of output array file
                name = self.prefix+'_arrayOut_'+str(count)+'.txt'
                # store the unique name in arrayOutsNames for later reference
                self.arrayOutsNames.append(name)
                # Log the name of this temporary file being written to disk
                self.log.fullinfo('Temporary ref file on disk for input to CL: '
                                  +name)
    
    def refInsFiles(self, type=''):
        """
        The function to get the temporary files written to disk for the refIns
        as either a string (or comma-separated string if input was a list), a 
        list of the filenames, or a list file. These files are required to 
        be on disk by IRAF and the file names are automatically created when 
        the CLManager is instantiated based on the 'funcName' parameter and 
        the original file names of the 'refIns' astrodata objects.
        
        :param type: Desired form of the temp filenames on disk for refIns.
        :type type: 'string' for filenames as a string 
                    (comma-separated if input was a list),
                    'list' for filenames as strings in a python list, or
                    'listFile' for a IRAF type list file.
        """
        if type!='':
            if type=='string':
                return ','.join(self.refInsCLdiskNames)
            if type=='list':
                return self.refInsCLdiskNames
            if type=='listFile':
                refInsListName = gt.listFileMaker(list=self.refInsCLdiskNames,
                                    listName='refList'+str(os.getpid())+
                                                                self.funcName)
                self.refInsListName = refInsListName
                return '@'+refInsListName
        else:
            raise Errors.ManagersError('Parameter "type" must not be an empty string'+
                           '; choose either "string","list" or "listFile"')  
                
    def refOutsFiles(self, type=''):
        """
        This function is used to return the names of the reference images that
        will be written to disk by IRAF in the form desired to pass into the 
        IRAF routine call.
        The names of these files can either be defined using
        the refOutsNames parameter set during the CLManager initial call, or
        automatically created in one way:
        Triggered by, refOutsNames=None and suffix=<any string>.
        Then refOutsNames will be a list with each file name of the refIns  
        post pended by the value of suffix.
        
        This function is simply for 'convenience' and can be ignored as long
        as the refOutsNames is set properly and its filenames are passed into 
        IRAF properly.
        
        :param type: Desired form of the filenames on disk for refOutsNames.
        :type type: 'string' for filenames as a string 
                    (comma-separated if input was a list),
                    'list' for filenames as strings in a python list, or
                    'listFile' for a IRAF type list file.
        
        """
        # Loading up the refOutsNames list if not done yet and params are set 
        # correctly, else error log message
        if self.refOutsNames==None:
            self.refOutsNames = []
            if (self.suffix!=None):
                for ad in self.refIns:
                    name = gt.fileNameUpdater(adIn=ad, suffix=self.suffix)
                    self.refOutsNames.append(name) 
            else:
                self.log.error('The "automatic" setting of refOutsNames can '+
                        'only work if at least the suffix parameter is set')
        # The parameter was set, ie not None
        else:
            # Cast it to a list for use below
            if isinstance(self.refOutsNames,str):
                self.refOutsNames = [self.refOutsNames] 

        tmp_names = []
        for name in self.refOutsNames:
            tmp_names.append(self.prefix+name)


        # returning the refOutsNames contents in the form requested, else error
        # log messsage
        if type!='':
            if type=='string':
                return ','.join(tmp_names)
            if type=='list':
                return tmp_names
            if type=='listFile':
                refOutsListName = gt.listFileMaker(list=tmp_names,
                                    listName='refOutsList'+str(os.getpid())+
                                                                self.funcName)
                self.refOutsListName = refOutsListName
                return '@'+refOutsListName
        else:
            raise Errors.ManagersError('Parameter "type" must not be an empty string'+
                           '; choose either "string","list" or "listFile"')             

class IrafStdout():
    """ This is a class to act as the standard output for the IRAF 
        routines that instead of printing its messages to the screen,
        it will print them to the gemlog.py logger that the primitives use
        
    """
    log=None
    
    def __init__(self):
        """ 
        A function that is needed IRAF but not used in our wrapping its
        scripts.
            
        """
        self.log = gemLog.getGeminiLog()
    
    def flush(self):
        """ A function that is needed IRAF but not used in our wrapping its
            scripts
        """
        pass
    
    def write(self, out):
        """ This function converts the IRAF console prints to logger calls.
            If the print has 'PANIC' in it, then it becomes a error log message,
            else it becomes a fullinfo message.
            
        """
        if 'PANIC' in out or 'ERROR' in out:
            self.log.error(out, category='clError')
        elif len(out) > 1:
            self.log.fullinfo(out, category='clInfo')

class ScienceFunctionManager():
    """
    A manager class to hold functions for performing input checks, naming,
    log instantiation... code that is repeated throughout all the 'user level
    functions' in the gempy libraries (currently those functions in 
    science/geminiScience.py and gmosScience.py).
    """
    # Set up global variables 
    adinput = None
    output_names = None
    suffix = None
    combinedInputs = False
    log = None  
    
    def __init__(self, adinput=None, output_names=None, suffix=None,
                 combinedInputs=False, funcName=None):
        """
        This will load up the global variables to use throughout the manager
        functions and instantiate the logger object for use in here and 
        back in the 'user level function' that is utilizing this manager.
        
        Either a 'main' type logger object, if it exists, or a null logger will
        be returned from startUp() along with the checked input and
        output_names.
        
        :param adinput: Astrodata inputs to have DQ extensions added to
        :type adinput: Astrodata objects, either a single or a list of objects.
                       At least one object MUST be passed in for input.
        
        :param output_names: filenames of output(s)
        :type output_names: String, either a single or a list of strings of same 
                        length as input.
        
        :param suffix: String to add on the end of the input filenames 
                       (or output_names if not None) for the output filenames.
        :type suffix: string
        
        :param combinedInputs: A flag to indicated that the input images of 
                               input will be combined to form one single 
                               image output.
                               The use of this parameter is optional and is  
                               overridden by providing output_names. 
        :type combinedInputs: Python boolean (True/False)
        
        """ 
        self.adinput = adinput
        self.output_names = output_names
        self.suffix = suffix
        self.combinedInputs = combinedInputs
        # loading of the logger 
        self.log = gemLog.getGeminiLog()
    
    def autoVardq(self, fl_vardq):
        """
        This is a function to perform either the 'AUTO' fl_vardq determination
        or just to check convert the value from True->iraf.yes, False->iraf.no .
        
        NOTE: 'AUTO' uses the first input to determine if VAR and  
        DQ frames exist, so, if the first does, then the rest MUST 
        also have them as well.
        
        :param fl_vardq: The value of the fl_vardq parameter at the start of the
                         Python user level function.
        :type fl_vardq: either: Python bool (True/False) or the string 'AUTO'
        """
        from astrodata.adutils.gemutil import pyrafLoader
        # loading and/or bringing the pyraf related modules into the name-space
        pyraf, gemini, yes, no = pyrafLoader()
        
        if fl_vardq=='AUTO':
            # if there are matching numbers of VAR, DQ and SCI extensions
            # then set to yes to ensure the outputs have VAR and DQ's as well.
            if self.adinput[0].count_exts('VAR')==\
                        self.adinput[0].count_exts('DQ')\
                                            ==self.adinput[0].count_exts('SCI'):
                fl_vardq=yes
            else:
                fl_vardq=no
        else:
            # 'AUTO' wasn't selected, so just convert the python bools to iraf
            # yes or no.
            if fl_vardq:
                fl_vardq=yes
            elif fl_vardq==False:
                fl_vardq=no
       
        return fl_vardq
    
    def markHistory(self, adOutputs=None, historyMarkKey=None):
        """
        The function to use near the end of a python user level function to 
        add a history_mark timestamp to all the outputs indicating when and what
        function was just performed on them, then logging the new historyMarkKey
        PHU key and updated 'GEM-TLM' key values due to history_mark.
        
        Note: The GEM-TLM key will be updated, or added if not in the PHU yet, 
        automatically everytime wrapUp is called.
        
        :param adOutputs: List of astrodata instance(s) to perform history_mark 
                          on.
        :type adOutputs: Either a single or multiple astrodata instances in a 
                         list.
        
        :param historyMarkKey: The PHU header key to write the current UT time 
        :type historyMarkKey: Under 8 character, all caps, string.
                              If None, then only 'GEM-TLM' is added/updated.
        """
        # casting inputs to a list if not one all ready to make loop work right
        if not isinstance(adOutputs,list):
            adOutputs = [adOutputs]
        
        # looping though inputs to perform history_mark on each of them
        for ad in adOutputs:
            # Adding 'GEM-TLM' (automatic) and historyMarkKey (if not None)
            # time stamps to the PHU
            ad.history_mark(key=historyMarkKey, stomp=False)
            
            # Updating log with new GEM-TLM and GIFLAT time stamps
            self.log.fullinfo('*'*50, category='header')
            self.log.fullinfo('File = '+ad.filename, category='header')
            self.log.fullinfo('~'*50, category='header')
            self.log.fullinfo('PHU keywords updated/added:\n', 'header')
            self.log.fullinfo('GEM-TLM = '+ad.phu_get_key_value('GEM-TLM'), 
                              category='header')
            if historyMarkKey!=None:
                self.log.fullinfo(historyMarkKey+' = '+
                                  ad.phu_get_key_value(historyMarkKey), 
                                  category='header')
            self.log.fullinfo('-'*50, category='header')
        
    def startUp(self):
        """
        This function performs checks on the input AstroData objects specified
        by the 'adinput' parameter, determines the name of the output AstroData
        objects using the 'output_names' and 'suffix' parameters, and
        instantiates the log. The 'output_names' parameter supercedes the
        'suffix' parameter.
        """
        try:
            # Check if "adinput" contains at least one AstroData instance
            if self.adinput is not None:
                if type(self.adinput) is list:
                    if len(self.adinput) == 0:
                        raise Errors.InputError()
                else:
                    # Return the "adinput" back to the user level function as a
                    # list
                    self.adinput = [self.adinput]
            else:
                raise Errors.InputError()
            # Determine the name of the output AstroData instance(s) using the
            # "output_names" and "suffix" parameters. If "output_names" is
            # None, use the "suffix" parameter to determine the output names.
            if self.output_names is None:
                self.output_names = []
            if type(self.output_names) is not list:
                self.output_names = [self.output_names]
            if len(self.output_names) == 0:
                # Use the "suffix" parameter
                if self.suffix is not None:
                    for ad in self.adinput:
                        output_name = gt.fileNameUpdater(
                            infilename=ad.filename,
                            suffix=self.suffix,
                            strip=False)
                        self.output_names.append(output_name)
                else:
                    # Both "suffix" and "output_names" are undefined
                    raise Errors.OutputError()
            elif len(self.output_names) == 1:
                log.status("A single output name is defined")
                first_adinput = self.adinput[0]
                output_name = gt.fileNameUpdater(
                    infilename=first_adinput.filename,
                    suffix=None,
                    strip=False)
                self.output_names.append(output_name)
            else:
                # If there is more than one output name, make sure the number
                # of output names matches the number of input AstroData
                # instances
                if len(self.adinput) == len(self.output_names):
                    for ad in self.adinput:
                        output_name = gt.fileNameUpdater(
                            infilename=ad.filename,
                            suffix=None,
                            strip=False)
                        self.output_names.append(output_name)
                else:
                    raise Errors.Error("The number of output names does not " +
                                       "match with the number of inputs")
            # Return the adinput list, output names list and the log object
            return (self.adinput, self.output_names, self.log)
        except:
            # Log the message from the exception
            log.critical(repr(sys.exc_info()[1]))
            raise
