from time import sleep
from ReductionObjects import ReductionObject

stepduration = 1.
class GEMINIPrimitives(ReductionObject):
    
    # primitives
    def init(self, co):
        ReductionObject.init(self, co)
        return co
    
    def logFilename (self, co):
        print "logFilename"
        for i in range(0,5):
            print "\tlogFilename",i
            sleep(stepduration)
            yield co
    
    def displayStructure(self, co):
        print "displayStructure"
        for i in range(0,5):
            print "\tds ",i
            sleep(stepduration)
            yield co
        
    def summarize(self, co):
        print "done with task"
        for i in range(0,5):
            sleep(stepduration)
            yield co        
    
    def gem_produce_im_flat(self, co):
        print "gem_produce_imflat step called"
        co.update({"flat" :co.calibrations[(co.inputs[0], "flat")]})
        yield co
    
    def gem_produce_bias(self, co):
        print "gem_produce_bias step called"
        co.update({"bias" :co.calibrations[(co.inputs[0], "bias")]})
        yield co    

    def getProcessedBias(self, co):
        try:
            print "getting bias"
            co.rqCal( "bias" )
        except:
            print "problem getting bias"
            raise
        yield co
        
    def setStackable(self, co):
        try:
            print "updating stackable with input"
            co.rqStackUpdate()
        except:
            print "problem stacking input"
            raise
        yield co
        
    def getStackable(self, co):
        try:
            print "getting stack"
            co.rqStackGet()
        except:
            print "problem getting stack"
            raise
        yield co
