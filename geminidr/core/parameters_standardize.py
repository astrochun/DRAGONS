# This parameter file contains the parameters related to the primitives located
# in the primitives_standardize.py file, in alphabetical order.

from geminidr import ParametersBASE

class ParametersStandardize(ParametersBASE):
    addDQ = {
        "suffix"            : "_dqAdded",
        "bpm"               : None,
        "illum_mask"        : False,
    }
    addMDF = {
        "suffix"            : "_mdfAdded",
        "mdf"               : None,
    }
    addVAR = {
        "suffix"            : "_varAdded",
        "read_noise"        : False,
        "poisson_noise"     : False,
    }
    prepare = {
        "suffix"            : "_prepared",
    }
