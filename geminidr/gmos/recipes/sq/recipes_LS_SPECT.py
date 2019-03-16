"""
Recipes available to data with tags ['GMOS', 'SPECT', 'LS'].
These are GMOS longslit observations.
Default is "reduce".
"""
recipe_tags = set(['GMOS', 'SPECT', 'LS'])

def reduce(p):
    p.prepare()
    p.addDQ(static_bpm=None)
    p.addVAR(read_noise=True)
    p.overscanCorrect()
    #p.biasCorrect()
    p.ADUToElectrons()
    p.addVAR(poisson_noise=True)
    p.distortionCorrect()
    p.writeOutputs()
    p.findSourceApertures()
    p.traceApertures()
    p.extract1DSpectra()
    p.removeFromInputs(tags='EXTRACTED', outstream='2d')
    p.writeOutputs(stream='2d')
    p.selectFromInputs(tags='EXTRACTED')
    p.linearizeSpectra()
    p.writeOutputs()

default = reduce
