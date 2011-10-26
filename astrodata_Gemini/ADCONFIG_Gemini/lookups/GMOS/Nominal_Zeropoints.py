nominal_zeropoints = {
    # Table of GMOS Nominal Zeropoint magnitudes
    # By filter and detector ID.
    # For new CCDs, just add them with the new detector ID
    # If we don't have per-chip values, just add the same value
    #   for each detector in the focal plane.
    #
    # The "composite" detector name is the DETID header and should here give the mean value
    # - This is used for mosaiced images that have the three detectors stiched together.
    #
    # At the moment, we don't account for the colour terms of the zeropoints
    # they are mostly < 0.1 mag,  especially longer than u, though it would be good to add
    # support for these in the future
    #
    # Nominal extinction values for CP and MK are given in a separate table 
    # at the Gemini level, and provided for by a descriptor
    #
    # Columns below are given as:
    # ("detector ID", "filter") : zeropoint
    #
    # GMOS-N original EEV detectors
    # Values from http://www.gemini.edu/sciops/instruments/gmos/calibration?q=node/10445  20111021
    ('EEV 9273-20-04', "u") : 25.47,
    ('EEV 9273-16-03', "u") : 25.47,
    ('EEV 9273-20-03', "u") : 25.47,
    ('EEV9273-16-03EEV9273-20-04EEV9273-20-03', "u") : 25.47,
    ('EEV 9273-20-04', "g") : 27.95,
    ('EEV 9273-16-03', "g") : 27.95,
    ('EEV 9273-20-03', "g") : 27.95,
    ('EEV9273-16-03EEV9273-20-04EEV9273-20-03', "g") : 27.95,
    ('EEV 9273-20-04', "r") : 28.20,
    ('EEV 9273-16-03', "r") : 28.20,
    ('EEV 9273-20-03', "r") : 28.20,
    ('EEV9273-16-03EEV9273-20-04EEV9273-20-03', "r") : 28.20,
    ('EEV 9273-20-04', "i") : 27.94,
    ('EEV 9273-16-03', "i") : 27.94,
    ('EEV 9273-20-03', "i") : 27.94,
    ('EEV9273-16-03EEV9273-20-04EEV9273-20-03', "i") : 27.94,
    ('EEV 9273-20-04', "z") : 26.78,
    ('EEV 9273-16-03', "z") : 26.78,
    ('EEV 9273-20-03', "z") : 26.78,
    ('EEV9273-16-03EEV9273-20-04EEV9273-20-03', "z") : 26.78,
    #
    # GMOS-S 
    ('EEV 2037-06-03', 'u'): 24.936,
    ('EEV 8194-19-04', 'u'): 24.913,
    ('EEV 8261-07-0', 'u'): 24.941,
    ('EEV2037-06-03EEV8194-19-04EEV8261-07-04', 'u'): 24.91,
    ('EEV 2037-06-03', 'g'): 28.303,
    ('EEV 8194-19-04', 'g'): 28.312,
    ('EEV 8261-07-0', 'g'): 28.343,
    ('EEV2037-06-03EEV8194-19-04EEV8261-07-04', 'g'): 28.33,
    ('EEV 2037-06-03', 'r'): 28.330,
    ('EEV 8194-19-04', 'r'): 28.320,
    ('EEV 8261-07-0', 'r'): 28.355,
    ('EEV2037-06-03EEV8194-19-04EEV8261-07-04', 'r'): 28.33,
    ('EEV 2037-06-03', 'i'): 27.916,
    ('EEV 8194-19-04', 'i'): 27.921,
    ('EEV 8261-07-0', 'i'): 27.955,
    ('EEV2037-06-03EEV8194-19-04EEV8261-07-04', 'i'): 27.93,
    ('EEV 2037-06-03', 'z'): 26.828,
    ('EEV 8194-19-04', 'z'): 26.837,
    ('EEV 8261-07-0', 'z'): 26.867,
    ('EEV2037-06-03EEV8194-19-04EEV8261-07-04', 'z'): 26.84,
}
