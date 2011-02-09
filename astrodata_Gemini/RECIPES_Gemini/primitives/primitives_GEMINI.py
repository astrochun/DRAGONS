import os, sys, re
from sets import Set

import time
from astrodata.ReductionObjects import PrimitiveSet
from astrodata.adutils import gemLog
from astrodata import IDFactory
from gempy.instruments import geminiTools as gemt
from gempy.science import geminiScience
from datetime import datetime
import shutil
from primitives_GENERAL import GENERALPrimitives
from astrodata.adutils.gemutil import pyrafLoader

log = gemLog.getGeminiLog()

class GEMINIException:
    """ This is the general exception the classes and functions in the
    Structures.py module raise.
    
    """
    def __init__(self, message='Exception Raised in Recipe System'):
        """This constructor takes a message to print to the user."""
        self.message = message
    def __str__(self):
        """This str conversion member returns the message given by the 
        user (or the default message)
        when the exception is not caught."""
        return self.message

class GEMINIPrimitives(GENERALPrimitives):
    """ 
    This is the class of all primitives for the GEMINI astrotype of 
    the hierarchy tree.  It inherits all the primitives to the level above
    , 'PrimitiveSet'.
    
    """
    astrotype = 'GEMINI'
    
    def init(self, rc):
        return 
    init.pt_hide = True
    
    def addDQ(self,rc):
        """
        This primitive will create a numpy array for the data quality 
        of each SCI frame of the input data. This will then have a 
        header created and append to the input using AstroData as a DQ 
        frame. The value of a pixel will be the sum of the following: 
        (0=good, 1=bad pixel (found in bad pixel mask), 
        2=value is non linear, 4=pixel is saturated)
        
        """
        try:
            log.status('*STARTING* to add the DQ frame(s) to the input data')
            
            # Calling addBPM primitive to add the appropriate Bad Pixel Mask
            # to the inputs which will then be updated below to create data 
            # quality frames from these new BPM extensions in the inputs.
            log.debug('Calling addBPM primitive for '+rc.inputsAsStr())
            rc.run('addBPM')
            log.status('Returned from the addBPM primitive successfully')
                
            # Calling geminiScience toolbox function ADUtoElectons to do the work
            # of converting the pixels, updating headers and logging.
            log.debug('Calling geminiScience.addDQ')

            adOuts = geminiScience.addDQ(adIns=rc.getInputs(style='AD'), 
                                         fl_nonlinear=rc['fl_nonlinear'], 
                                         fl_saturated=rc['fl_saturated'], 
                                         postpend=rc['postpend'], verbose=rc['logVerbose'])    
           
            log.status('geminiScience.addDQ completed successfully')
            
            # Reporting the outputs to the reduction context
            rc.reportOutput(adOuts)          
                
            log.status('*FINISHED* adding the DQ frame(s) to the input data')
        except:
            log.critical('Problem adding the DQ to one of '+rc.inputsAsStr())
            raise 
        yield rc
    
    def addVAR(self,rc):
        """
        This primitive uses numpy to calculate the variance of each SCI frame
        in the input files and appends it as a VAR frame using AstroData.
        
        The calculation will follow the formula:
        variance = (read noise/gain)2 + max(data,0.0)/gain
        
        """
        try:
            log.fullinfo('*STARTING* to add the VAR frame(s) to the input data')
            
            
            # Calling geminiScience toolbox function ADUtoElectons to do the work
            # of converting the pixels, updating headers and logging.
            log.debug('Calling geminiScience.addVAR')
            
            adOuts = geminiScience.addVAR(adIns=rc.getInputs(style='AD'), 
                                         postpend=rc['postpend'], verbose=rc['logVerbose'])    
           
            log.status('geminiScience.addVAR completed successfully')
            
            # Reporting the outputs to the reduction context
            rc.reportOutput(adOuts)            
                
            log.status('*FINISHED* adding the VAR frame(s) to the input data')
        except:
            log.critical('Problem adding the VAR to one of '+rc.inputsAsStr())
            raise 
        yield rc 
    
    def ADUtoElectrons(self,rc):
        """
        This primitive will convert the inputs from having pixel 
        units of ADU to electrons.
        
        """
        try:
            log.status('*STARTING* to convert the pixel values from '+
                       'ADU to electrons')
            # Calling geminiScience toolbox function ADUtoElectons to do the work
            # of converting the pixels, updating headers and logging.
            log.debug('Calling geminiScience.ADUtoElectrons')
            
            adOuts = geminiScience.ADUtoElectrons(adIns=rc.getInputs(style='AD'), postpend=rc['postpend'], verbose=rc['logVerbose'])    
           
            log.status('geminiScience.ADUtoElectrons completed successfully')
            
            # Reporting the outputs to the reduction context
            rc.reportOutput(adOuts)   
            
            log.status('*FINISHED* converting the pixel units to electrons')
        except:
            log.critical('Problem converting the pixel units of one of '+
                         rc.inputsAsStr())
            raise
        yield rc
            
    def combine(self,rc):
        """
        This primitive will average and combine the SCI extensions of the 
        inputs. It takes all the inputs and creates a list of them and 
        then combines each of their SCI extensions together to create 
        average combination file. New VAR frames are made from these 
        combined SCI frames and the DQ frames are propagated through 
        to the final file.
        
        """
#        # Loading and bringing the pyraf related modules into the name-space
#        pyraf, gemini, yes, no = pyrafLoader()
        
        try:
            if len(rc.getInputs())>1:
                log.status('*STARTING* combine the images of the input data')
                
                # Calling geminiScience toolbox function combine to do the work
                # of converting the pixels, updating headers and logging.
                log.debug('Calling geminiScience.combine')
                
                adOut = geminiScience.combine(adIns=rc.getInputs(style='AD'), 
                                              fl_vardq=rc['fl_vardq'], fl_dqprop=rc['fl_dqprop'], 
                                              method=rc['method'], postpend=rc['postpend'], 
                                              verbose=rc['logVerbose']) 
                
                log.status('geminiScience.combine completed successfully')
            
                # Reporting the outputs to the reduction context
                rc.reportOutput(adOut)    
                
                log.status('*FINISHED* combining the images of the input data')
        except:
            log.critical('There was a problem combining '+rc.inputsAsStr())
            raise 
        yield rc

    def crashReduce(self, rc):
        raise 'Crashing'
        yield rc
        
    def clearCalCache(self, rc):
        # print 'pG61:', rc.calindfile
        rc.persistCalIndex(rc.calindfile, newindex={})
        scals = rc['storedcals']
        if scals:
            if os.path.exists(scals):
                shutil.rmtree(scals)
            cachedict = rc['cachedict']
            for cachename in cachedict:
                cachedir = cachedict[cachename]
                if not os.path.exists(cachedir):                        
                    os.mkdir(cachedir)                
        yield rc
        
    def display(self, rc):
        try:
            rc.rqDisplay(displayID=rc['displayID'])           
        except:
            log.critical('Problem displaying output')
            raise 
        yield rc
   
    def getProcessedBias(self,rc):
        """
        A primitive to search and return the appropriate calibration bias from
        a server for the given inputs.
        
        """
        rc.rqCal('bias', rc.getInputs(style='AD'))
        yield rc
        
    def getProcessedFlat(self,rc):
        """
        A primitive to search and return the appropriate calibration flat from
        a server for the given inputs.
        
        """
        rc.rqCal('flat', rc.getInputs(style='AD'))
        yield rc
    
    def getStackable(self, rc):
        """
        This primitive will check the files in the stack lists are on disk,
        and then update the inputs list to include all members of the stack 
        for stacking.
        
        """
        sidset = set()
        purpose=rc["purpose"]
        if purpose==None:
            purpose = ""
        try:
            for inp in rc.inputs:
                sidset.add(purpose+IDFactory.generateStackableID(inp.ad))
            for sid in sidset:
                stacklist = rc.getStack(sid) #.filelist
                log.fullinfo('Stack for stack id=%s' % sid)
                for f in stacklist:
                    rc.reportOutput(f)
                    log.fullinfo('   '+os.path.basename(f))
            yield rc
        except:
            log.critical('Problem getting stack '+sid, category='stack')

            raise 
        yield rc
    
    def measureIQ(self,rc):
        """
        This primitive will detect the sources in the input images and fit
        both Gaussian and Moffat models to their profiles and calculate the 
        Image Quality and seeing from this.
        
        """
        #@@FIXME: Detecting sources is done here as well. This 
        # should eventually be split up into
        # separate primitives, i.e. detectSources and measureIQ.
        try:
            log.status('*STARTING* to detect the sources'+
                       ' and measure the IQ of the inputs')
            # Importing getiq module to perform the source detection and IQ
            # measurements of the inputs
            from iqtool.iq import getiq
            
            # Initializing a total time sum variable for logging purposes 
            total_IQ_time = 0
            
            for ad in rc.getInputs(style='AD'):
                # Check that the files being processed are in the current 
                # working directory, as that is a requirement for getiq to work
                if os.path.dirname(ad.filename) != '':
                    log.critical('The inputs to measureIQ must be in the'+
                                 ' pwd for it to work correctly')
                    raise GEMINIException('inputs to measureIQ were not in pwd')
                    
                # Start time for measuring IQ of current file
                st = time.time()
                
                log.debug('Calling getiq.gemiq for input '+ad.filename)
                
                # Calling the gemiq function to detect the sources and then
                # measure the IQ of the current image 
                iqdata = getiq.gemiq( ad.filename, function='moffat', verbose=True,
                                      display=True, mosaic=False, qa=True)
                
                # End time for measuring IQ of current file
                et = time.time()
                total_IQ_time = total_IQ_time + (et - st)
                # Logging the amount of time spent measuring the IQ 
                log.stdinfo('MeasureIQ time: '+repr(et - st), category='IQ')
                log.fullinfo('~'*45, category='format')
                
                # iqdata is list of tuples with image quality metrics
                # (ellMean, ellSig, fwhmMean, fwhmSig)
                # First check if it is empty (ie. gemiq failed in someway)
                if len(iqdata) == 0:
                    log.warning('Problem Measuring IQ Statistics, '+
                                'none reported')
                # If it all worked, then format the output and log it
                else:
                    # Formatting this output for printing or logging                
                    fnStr = 'Filename:'.ljust(19)+ad.filename
                    emStr = 'Ellipticity Mean:'.ljust(19)+str(iqdata[0][0])
                    esStr = 'Ellipticity Sigma:'.ljust(19)+str(iqdata[0][1])
                    fmStr = 'FWHM Mean:'.ljust(19)+str(iqdata[0][2])
                    fsStr = 'FWHM Sigma:'.ljust(19)+str(iqdata[0][3])
                    sStr = 'Seeing:'.ljust(19)+str(iqdata[0][2])
                    psStr = 'PixelScale:'.ljust(19)+str(ad.pixel_scale())
                    vStr = 'VERSION:'.ljust(19)+'None' #$$$$$ made on ln12 of ReductionsObjectRequest.py, always 'None' it seems.
                    tStr = 'TIMESTAMP:'.ljust(19)+str(datetime.now())
                    # Create final formated string
                    finalStr = '-'*45+'\n'+fnStr+'\n'+emStr+'\n'+esStr+'\n'\
                                    +fmStr+'\n'+fsStr+'\n'+sStr+'\n'+psStr+\
                                    '\n'+vStr+'\n'+tStr+'\n'+'-'*45
                    # Log final string
                    log.stdinfo(finalStr, category='IQ')
                    
            # Logging the total amount of time spent measuring the IQ of all
            # the inputs
            log.stdinfo('Total measureIQ time: '+repr(total_IQ_time), 
                        category='IQ')
            
            log.status('*FINISHED* measuring the IQ of the inputs')
        except:
            log.critical('There was a problem combining '+rc.inputsAsStr())
            raise 
        yield rc
 
    def pause(self, rc):
        rc.requestPause()
        yield rc
 
    def setContext(self, rc):
        rc.update(rc.localparms)
        yield rc   
       
    def setStackable(self, rc):
        """
        This primitive will update the lists of files to be stacked
        that have the same observationID with the current inputs.
        This file is cached between calls to reduce, thus allowing
        for one-file-at-a-time processing.
        
        """
        try:
            log.status('*STARTING* to update/create the stack')
            # Requesting for the reduction context to perform an update
            # to the stack cache file (or create it) with the current inputs.
            purpose = rc["purpose"]
            if purpose == None:
                purpose = ""
                
            rc.rqStackUpdate(purpose= purpose)
            # Writing the files in the stack to disk if not all ready there
            for ad in rc.getInputs(style='AD'):
                if not os.path.exists(ad.filename):
                    log.fullinfo('writing '+ad.filename+\
                                 ' to disk', category='stack')
                    ad.write(ad.filename)
                    
            log.status('*FINISHED* updating/creating the stack')
        except:
            log.critical('Problem writing stack for files '+rc.inputsAsStr(),
                         category='stack')
            raise
        yield rc
    
    def showCals(self, rc):
        if str(rc['showcals']).lower() == 'all':
            num = 0
            # print 'pG256: showcals=all', repr (rc.calibrations)
            for calkey in rc.calibrations:
                num += 1
                log.fullinfo(rc.calibrations[calkey], category='calibrations')
            if (num == 0):
                log.warning('There are no calibrations in the cache.')
        else:
            for adr in rc.inputs:
                sid = IDFactory.generateAstroDataID(adr.ad)
                num = 0
                for calkey in rc.calibrations:
                    if sid in calkey :
                        num += 1
                        log.fullinfo(rc.calibrations[calkey], 
                                     category='calibrations')
            if (num == 0):
                log.warning('There are no calibrations in the cache.')
        yield rc
    ptusage_showCals='Used to show calibrations currently in cache for inputs.'

    def showInputs(self, rc):
        log.fullinfo('Inputs:',category='inputs')
        for inf in rc.inputs:
            log.fullinfo('  '+inf.filename, category='inputs')  
        yield rc  
    showFiles = showInputs

    def showParameters(self, rc):
        rcparams = rc.paramNames()
        if (rc['show']):
            toshows = rc['show'].split(':')
            for toshow in toshows:
                if toshow in rcparams:
                    log.fullinfo(toshow+' = '+repr(rc[toshow]), 
                                 category='parameters')
                else:
                    log.fullinfo(toshow+' is not set', category='parameters')
        else:
            for param in rcparams:
                log.fullinfo(param+' = '+repr(rc[param]), category='parameters')
        
        # print 'all',repr(rc.parmDictByTag('showParams', 'all'))
        # print 'iraf',repr(rc.parmDictByTag('showParams', 'iraf'))
        # print 'test',repr(rc.parmDictByTag('showParams', 'test'))
        # print 'sdf',repr(rc.parmDictByTag('showParams', 'sdf'))

        # print repr(dir(rc.ro.primDict[rc.ro.curPrimType][0]))
        yield rc  
         
    def showStackable(self, rc):
        sidset = set()
        purpose = rc["purpose"]
        if purpose == None:
            purpose = ""
        # print "pG710"
        if purpose == "all":
            allsids = rc.getStackIDs()
            # print "pG713:", repr(allsids)
            for sid in allsids:
                sidset.add(sid)
        else:   
            for inp in rc.inputs:
                sidset.add(purpose+IDFactory.generateStackableID(inp.ad))
        for sid in sidset:
            stacklist = rc.getStack(sid) #.filelist
            log.status('Stack for stack id=%s' % sid)
            if len(stacklist)>0:
                for f in stacklist:
                    log.status('    '+os.path.basename(f))
            else:
                log.status("    no datasets in list")
        yield rc
            
    def sleep(self, rc):
        if rc['duration']:
            dur = float(rc['duration'])
        else:
            dur = 5.
        log.status('Sleeping for %f seconds' % dur)
        time.sleep(dur)
        yield rc
             
    def standardizeHeaders(self, rc):
        """
        This primitive updates and adds the important header keywords
        for the input MEFs. First the general headers for Gemini will 
        be update/created, followed by those that are instrument specific.
        
        """
        
        try:   
            log.status('*STARTING* to standardize the headers')
            log.status('Standardizing observatory general headers')            
            for ad in rc.getInputs(style='AD'):
                log.debug('calling gemt.stdObsHdrs for '+ad.filename)
                gemt.stdObsHdrs(ad)
                log.status('Completed standardizing the headers for '+
                           ad.filename)
   
            log.status('Observatory headers fixed')
            log.debug('Calling standardizeInstrumentHeaders primitive')
            log.status('Standardizing instrument specific headers')
            
            # Calling standarizeInstrumentHeaders primitive
            rc.run('standardizeInstrumentHeaders') 
            log.status('Instrument specific headers fixed')
            
            # Updating the file name with the postpend/outsuffix  and timestamps 
            # for this primitive and then reporting the new file to the 
            # reduction context 
            for ad in rc.getInputs(style='AD'):
                # Adding a GEM-TLM (automatic) and STDHDRS time stamps 
                # to the PHU
                ad.historyMark(key='STDHDRS',stomp=False)
                log.debug('Calling gemt.fileNameUpdater on '+ad.filename)
                ad.filename = gemt.fileNameUpdater(adIn=ad, 
                                                   postpend=rc['postpend'], 
                                                   strip=False)
                log.status('File name updated to '+ad.filename)
                # Updating logger with updated/added time stamps
                log.fullinfo('************************************************'
                             ,category='header')
                log.fullinfo('file = '+ad.filename, category='header')
                log.fullinfo('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
                             , 'header')
                log.fullinfo('PHU keywords updated/added:\n', category='header')
                log.fullinfo('GEM-TLM = '+ad.phuGetKeyValue('GEM-TLM'), 
                             category='header')
                log.fullinfo('STDHDRS = '+ad.phuGetKeyValue('STDHDRS'), 
                             category='header')
                log.fullinfo('------------------------------------------------'
                             , category='header')    
                rc.reportOutput(ad)
                
            log.status('*FINISHED* standardizing the headers')
        except:
            log.critical('Problem preparing one of '+rc.inputsAsStr())
            raise 
        yield rc
                                 
    def standardizeStructure(self,rc):
        """
        This primitive ensures the MEF structure is ready for further 
        processing, through adding the MDF if necessary and the needed 
        keywords to the headers.  First the MEF's will be checked for the 
        general Gemini structure requirements and then the instrument specific
        ones if needed. If the data requires a MDF to be attached, use the 
        'addMDF' flag to make this happen 
        (eg. standardizeStructure(addMDF=True)).
        
        """
        
        try:
            log.status('*STARTING* to standardize the structure of input data')
            
            #$$$$ MAYBE SET THIS TO FALSE IF GMOS_IMAGE AND TRUE IF GMOS_SPEC?$$$$$$$
            # Add the MDF if not set to false
            if rc['addMDF'] is True:
                log.debug('Calling attachMDF primitive')
                # Calling the attachMDF primitive
                rc.run('attachMDF')
                log.status('Successfully returned to '+
                           'standardizeStructure from the attachMDF primitive')

            for ad in rc.getInputs(style='AD'):
                log.debug('Calling gemt.stdObsStruct on '+ad.filename)
                gemt.stdObsStruct(ad)
                log.status('Completed standardizing the structure for '+
                           ad.filename)
                
                # Adding a GEM-TLM (automatic) and STDSTRUC time stamps 
                # to the PHU
                ad.historyMark(key='STDSTRUC',stomp=False)
                # Updating the file name with the postpend/outsuffix for this   
                # primitive and then reporting the new file to the reduction 
                # context
                log.debug('Calling gemt.fileNameUpdater on '+ad.filename)
                ad.filename = gemt.fileNameUpdater(adIn=ad, 
                                                   postpend=rc['postpend'], 
                                                   strip=False)
                log.status('File name updated to '+ad.filename)
                # Updating logger with updated/added time stamps
                log.fullinfo('************************************************'
                             ,category='header')
                log.fullinfo('file = '+ad.filename, category='header')
                log.fullinfo('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
                             , category='header')
                log.fullinfo('PHU keywords updated/added:\n', category='header')
                log.fullinfo('GEM-TLM = '+ad.phuGetKeyValue('GEM-TLM'), 
                             category='header')
                log.fullinfo('STDSTRUC = '+ad.phuGetKeyValue('STDSTRUC'), 
                             category='header')
                log.fullinfo('------------------------------------------------'
                             , category='header')  
                rc.reportOutput(ad)
   
            log.status('*FINISHED* standardizing the structure of input data')
        except:
            log.critical('Problem preparing one of '+rc.inputsAsStr())
            raise 
        yield rc
        
    def time(self, rc):
        cur = datetime.now()
        
        elap = ''
        if rc['lastTime'] and not rc['start']:
            td = cur - rc['lastTime']
            elap = ' (%s)' %str(td)
        log.fullinfo('Time:'+' '+str(datetime.now())+' '+elap)
        
        rc.update({'lastTime':cur})
        yield rc

    def validateData(self,rc):
        """
        This primitive will ensure the data is not corrupted or in an odd 
        format that will affect later steps in the reduction process.  
        It will call a function to take care of the general Gemini issues 
        and then one for the instrument specific ones. If there are issues 
        with the data, the flag 'repair' can be used to turn on the feature to 
        repair it or not (eg. validateData(repair=True))
        (this feature is not coded yet).
        
        """
        
        try:
            if rc['repair'] is True:
               # This should repair the file if it is broken, but this function
               # isn't coded yet and would require some sort of flag set while 
               # checking the data to tell this to perform the corrections
               log.critical('Sorry, but the repair feature of validateData' +
                            ' is not available yet')
            
            log.status('*STARTING* to validate the input data')
            
            log.debug('Calling validateInstrumentData primitive')
            # Calling the validateInstrumentData primitive 
            rc.run('validateInstrumentData')
            log.status('Successfully returned to validateData'+
                       ' from the validateInstrumentData primitive') 
            
            # Updating the file name with the postpend/outsuffix  and timestamps 
            # for this primitive and then reporting the new file to the 
            # reduction context 
            for ad in rc.getInputs(style='AD'):
                # Adding a GEM-TLM (automatic) and VALDATA time stamps 
                # to the PHU
                ad.historyMark(key='VALDATA',stomp=False)
                log.debug('calling gemt.gemt.fileNameUpdater on '+ad.filename)        
                ad.filename = gemt.fileNameUpdater(adIn=ad, 
                                                   postpend='_validated', 
                                                   strip=False)
                log.status('File name updated to '+ad.filename)
                # Updating logger with updated/added time stamps
                log.fullinfo('************************************************'
                             ,'header')
                log.fullinfo('File = '+ad.filename, category='header')
                log.fullinfo('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
                             , category='header')
                log.fullinfo('PHU keywords updated/added:\n', category='header')
                log.fullinfo('GEM-TLM = '+ad.phuGetKeyValue('GEM-TLM'), 
                              category='header')
                log.fullinfo('VALDATA = '+ad.phuGetKeyValue('VALDATA'), 
                             category='header')
                log.fullinfo('------------------------------------------------'
                             , category='header')  
                rc.reportOutput(ad) 
                        
            log.status('*FINISHED* validating input data')                
        except:
            log.critical('Problem preparing one of  '+rc.inputsAsStr())
            raise 
        yield rc

    def writeOutputs(self,rc):
        """
        A primitive that may be called by a recipe at any stage to
        write the outputs to disk.
        If postpend is set during the call to writeOutputs, any previous 
        postpends will be striped and replaced by the one provided.
        examples: 
        writeOutputs(postpend= '_string'), writeOutputs(prepend= '_string') 
        or if you have a full file name in mind for a SINGLE file being 
        ran through Reduce you may use writeOutputs(outfilename='name.fits').
        
        """
        try:
            log.status('*STARTING* to write the outputs')
            
            # Logging current values of postpend and prepend
            log.status('postpend = '+str(rc['postpend']))
            log.status('prepend = '+str(rc['prepend']))
            log.status('strip = '+str(rc['strip']))
            
            if rc['postpend'] and rc['prepend']:
                log.critical('The input will have '+rc['prepend']+' prepended'+
                             ' and '+rc['postpend']+' postpended onto it')
                
            for ad in rc.getInputs(style='AD'):
                # If the value of 'postpend' was set, then set the file name 
                # to be written to disk to be postpended by it
                if rc['postpend']:
                    log.debug('calling gemt.fileNameUpdater on '+ad.filename)
                    ad.filename = gemt.fileNameUpdater(adIn=ad, 
                                        postpend=rc['postpend'], 
                                        strip=rc['strip'])
                    log.status('File name updated to '+ad.filename)
                    outfilename = os.path.basename(ad.filename)
                    
                # If the value of 'prepend' was set, then set the file name 
                # to be written to disk to be prepended by it
                if rc['prepend']:
                    infilename = os.path.basename(ad.filename)
                    outfilename = rc['prepend']+infilename
                    
                # If the 'outfilename' was set, set the file name of the file 
                # file to be written to this
                elif rc['outfilename']:
                    # Check that there is not more than one file to be written
                    # to this file name, if so throw exception
                    if len(rc.getInputs(style='AD'))>1:
                        log.critical('More than one file was requested to be'+
                                     'written to the same name '+
                                     rc['outfilename'])
                        raise GEMINIException('More than one file was '+
                                     'requested to be written to the same'+
                                     'name'+rc['outfilename'])
                    else:
                        outfilename = rc['outfilename']   
                # If no changes to file names are requested then write inputs
                # to their current file names
                else:
                    outfilename = os.path.basename(ad.filename) 
                    log.status('not changing the file name to be written'+
                    ' from its current name') 
                    
                # Finally, write the file to the name that was decided 
                # upon above
                log.status('writing to file = '+outfilename)      
                ad.write(filename=outfilename, clobber=rc['clobber'])     
                #^ AstroData checks if the output exists and raises an exception
                #rc.reportOutput(ad)
            
            log.status('*FINISHED* writing the outputs')   
        except:
            log.critical('There was a problem writing one of '+rc.inputsAsStr())
            raise 
        yield rc   
         