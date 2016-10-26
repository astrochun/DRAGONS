#!/usr/bin/env python
#
#                                                                     QAP Gemini
#
#                                                               mosaicFactory.py
#                                                               Kenneth Anderson
#                                                                        07-2013
#                                                          <kanderso@gemini.edu>
# ------------------------------------------------------------------------------
"""
This module provides the MosaicFactory class and command line interface to
receive a list of files to process with gemini_python mosaic package,currently
under gemini_python/trunk/devel/mosaic. The mosaic package currently supports
GMOS and GSAOI images.

The MosaicFactory class provides one (1) public method, auto_mosaic() is all
the caller needs to call on a list of input images. Command line users  may
pass one (1) or more FITS files to the command line. mosaicFactory will process
all input files. Efficient use of this module will see a list of input images
passed, avoiding re-importing astrodata and the MosaicAD class.

Eg.,
$ infile=`ls *.fits`
$ mosaicFactory.py $infiles

usage: mosaicFactory [-h] [-v] [infiles [infiles ...]]

Auto mosaic builder.

positional arguments:
  infiles        infile1 [infile2 ...]

optional arguments:
  -h, --help     show this help message and exit
  -v, --version  show program's version number and exit

Mosaic-ed FITS  images are written to cwd(), like

inputImage.fits --> inputImage_mosaic.fits
"""
------------------------------------------------------------------------------
__version__ = "0.1"

import os
import sys
from datetime import datetime
from argparse import ArgumentParser

import astrodata
import gemini_instruments

from gempy.gmosaic.mosaicAD import MosaicAD
from gempy.gmosaic.gemMosaicFunction import gemini_mosaic_function

# ------------------------------------------------------------------------------
def ptime():
    """
    parameters: <void>
    return:     <string>, ISO 8601 'now' timestamp
    """
    return datetime.isoformat(datetime.now())


def buildNewParser(version=__version__):
    """
    parameters: <string>, defaulted optional version.
    return:     <instance>, ArgumentParser instance
    """
    parser = ArgumentParser(description="Auto mosaic builder.",
                            prog="mosaicFactory")
    parser.add_argument("-v", "--version", action="version",
                        version="%(prog)s @r" + version)
    parser.add_argument('infiles', nargs='*', default= '',
                        help="infile1 [infile2 ...]")
    return parser


def handleCLargs():
    """
    parameters: None
    return:     <instance>, Namespace instance.
    """
    parser = buildNewParser()
    args = parser.parse_args()
    return args


class MosaicFactory(object):

    def auto_mosaic(self, infiles):
        """
        parameters: <list>, list of input filenames
        return:     <void>
        """
        for in_fits in infiles:
            out_fits = self._set_out_fits(in_fits)
                
            print ptime(),"\tWorking on ...", os.path.split(in_fits)[1]
            ad = astrodata.open(in_fits)
            
            print ptime(),"\tAstroData object built"
            print ptime(),"\tWorking on type:", self._check_tags(ad.tags)
            print ptime(),"\tConstructing MosaicAD instance ..."
            mos = MosaicAD(ad, mosaic_ad_function=gemini_mosaic_function)

            print ptime(),"\tMaking mosaic ..."
            mos.mosaic_image_data()

            print ptime(), "\tConverting data ..."
            adout = mos.as_astrodata()

            print ptime(),"\tWriting file ..."
            adout.write(out_fits)

            print ptime(),"\tMosaic fits image written:", out_fits
        return

    def _check_tags(self, tlist):
        """
        parameters: <set>, set of astrodata tags
        return:     <str>, compatible tags, 'GMOS IMAGE' or 'GSAOI IMAGE'

        raises:     TypeError on incompatible tag sets.

        """
        item = None
        err  = "File does not appear to be a supported type."

        if "GMOS" in tlist and "IMAGE" in tlist:
            item = 'GMOS IMAGE'
        elif "GSAOI" in tlist and "IMAGE" in tlist:
            item = 'GSAOI IMAGE'

        if not item:
            raise TypeError(err)

        return item

    def _set_out_fits(self, in_fits):
        """
        parameters: <string>, filename
        return:     <string>, output filename
        """
        head, tail = os.path.split(in_fits)
        fnam, fext = os.path.splitext(tail)
        out_fits   = fnam + "_mosaic" + fext
        return out_fits



if __name__ == '__main__':
    args = handleCLargs()
    mos_factory = MosaicFactory()
    mos_factory.auto_mosaic(args.infiles)
