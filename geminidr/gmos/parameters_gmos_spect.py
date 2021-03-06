# This parameter file contains the parameters related to the primitives located
# in the primitives_gmos_spect.py file, in alphabetical order.
from astrodata import AstroData
from gempy.library import config
from geminidr.core import parameters_spect

class QECorrectConfig(config.Config):
    suffix = config.Field("Filename suffix", str, "_QECorrected", optional=True)
    arc = config.ListField("Arc(s) with distortion map", (AstroData, str), None,
                           optional=True, single=True)
    use_iraf = config.Field("Use IRAF polynomial fits for Hamamatsu CCDs?",
                            bool, False)

class findAcquisitionSlitsConfig(config.Config):
    suffix = config.Field("Filename suffix", str, "_acqSlitsAdded", optional=True)

class determineWavelengthSolutionConfig(parameters_spect.determineWavelengthSolutionConfig):
    nbright = config.RangeField("Number of bright lines to eliminate", int, 0, min=0)

    def setDefaults(self):
        self.order = 3
