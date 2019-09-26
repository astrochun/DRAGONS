#!/usr/bin/env python
"""
Tests related to GMOS Long-slit Spectroscopy arc processing.
"""
import os

import numpy as np
# noinspection PyPackageRequirements
import pytest

import astrodata
# noinspection PyUnresolvedReferences
import gemini_instruments
import geminidr
from geminidr.gmos import primitives_gmos_spect
from gempy.utils import logutils

dataset_file_list = [
    # 'process_arcs/GMOS/S20130218S0126.fits',  # todo: Breaks p.determineWavelengthSolution()
    'process_arcs/GMOS/S20170103S0152.fits',
    'process_arcs/GMOS/N20170530S0006.fits',
    'process_arcs/GMOS/N20180119S0232.fits',
    # 'process_arcs/GMOS/N20181114S0512.fits',  # todo: RMS > 0.5 (RMS = 0.646)
    'process_arcs/GMOS/N20180120S0417.fits',
    'process_arcs/GMOS/N20180516S0214.fits',
]


@pytest.fixture(scope='class', params=dataset_file_list)
def inputs_for_tests(request, path_to_inputs, path_to_outputs, path_to_refs):
    """
    Super fixture that returns an object with the data required for the tests
    inside this file. This super fixture avoid confusions with Pytest, Fixtures
    and Parameters that could generate a very large matrix of configurations.

    The `path_to_*` fixtures are defined inside the `conftest.py` file.

    Parameters
    ----------
    request : pytest.fixture
        Special fixture providing information of the requesting test function.
    path_to_inputs : pytest.fixture
        Fixture inherited from astrodata.testing with path to the input files.
    path_to_outputs : pytest.fixture
        Fixture inherited from astrodata.testing with path to the output files.
    path_to_refs : pytest.fixture
        Fixture inherited from astrodata.testing with path to the reference files.

    Returns
    -------
    namespace
        An object that contains `.ad`, `.output_dir`, `.ref_dir`, and
        `.filename` attributes.
    """
    logutils.config(mode='quiet', file_name='foo.log')

    reference_folder = os.path.join(path_to_refs, os.path.dirname(request.param))

    dirname = os.path.dirname(request.param)
    output_folder = os.path.join(path_to_outputs, dirname)

    oldmask = os.umask(000)
    os.makedirs(output_folder, exist_ok=True, mode=0o775)
    os.umask(oldmask)

    output_file = os.path.join(path_to_outputs, request.param)
    output_file, _ = os.path.splitext(output_file)
    output_file = output_file + "_arc.fits"
    output_file = os.path.join(output_folder, output_file)
    print(output_file)

    input_file = os.path.join(path_to_inputs, request.param)

    p = primitives_gmos_spect.GMOSSpect([astrodata.open(input_file)])
    p.viewer = geminidr.dormantViewer(p, None)

    p.prepare()
    p.addDQ(static_bpm=None)
    p.addVAR(read_noise=True)
    p.overscanCorrect()
    p.ADUToElectrons()
    p.addVAR(poisson_noise=True)
    p.mosaicDetectors()
    p.makeIRAFCompatible()
    p.determineWavelengthSolution()
    p.determineDistortion(suffix="_arc")
    ad = p.writeOutputs(outfilename=output_file, overwrite=True)[0]
    os.chmod(output_file, mode=0o775)

    class InputsForTests:
        pass

    InputsForTests.ad = ad
    InputsForTests.output_file = output_file
    InputsForTests.output_dir = output_folder
    InputsForTests.ref_dir = reference_folder

    return InputsForTests


@pytest.mark.gmosls
class TestGmosArcProcessing:
    """
    Collection of tests that will run on every `dataset_file`.
    """

    @staticmethod
    def remove_spect_continuum(data, mask):
        """
        Split the arr into different `arr` sections based on the `msk`, fit
        a polynomium to each of them, and then, stack them together into a
        single array.

        Parameters
        ----------
        data : `ndarray`
            Input 2D array with spectrum
        mask : `ndarray`
            Input 2D array with mask

        Returns
        -------
        arr : `ndarray`
            Masked output 1D array with no background.
        msk : `ndarray`
            Output 1D array containing mask.
        """
        from scipy.signal import argrelmax
        from scipy.ndimage import binary_dilation

        msk = np.array(np.average(mask, axis=0), dtype=int)
        msk = np.bitwise_and(16, msk)  # 16 is the data quality bit for no-data
        diff_msk = np.diff(msk)

        idxs = argrelmax(diff_msk, order=15)
        idxs = np.insert(idxs, 0, 0)
        idxs = np.append(idxs, msk.size)

        data = np.average(data, axis=0)
        data = np.ma.masked_where(msk > 0, data)
        data = (data - data.min()) / data.ptp()

        sub_arrs = []
        for i0, i1 in zip(idxs[:-1], idxs[1:]):

            sub_arr = data[i0:i1]

            x = np.arange(i0, i1)
            y = sub_arr

            for n in range(1):  # interacts 5 times

                p = np.polyfit(x, y, 9)
                y_fit = np.polyval(p, x)

                err = np.abs(y_fit - y)

                x = np.ma.masked_where(err > 3 * err.std(), x)
                y = np.ma.masked_where(err > 3 * err.std(), y)

            # noinspection PyUnboundLocalVariable
            sub_arr = y - y_fit
            sub_arrs.extend(sub_arr.data)

        msk = binary_dilation(msk // msk.max(), iterations=3)
        arr = np.array(sub_arrs)
        arr = np.ma.masked_where(msk > 0, arr)

        return arr, msk

    @staticmethod
    def plot_spectrum(name, ext_num, output_folder, data, mask, peaks,
                      wavelengths, grating, central_wavelength):
        """
        Plot the spectrum for visual inspection. The 20 brightest lines are marked
        with lines and tagged with the correspondent wavelengths.

        Parameters
        ----------
        name : str
            Base name of the plot and of the file.
        ext_num : int
            Extension number.
        output_folder : str
            Path to the output data.
        data : ndarray
            Masked 1D spectrum.
        mask : ndarray
            1D mask.
        peaks : ndarray
            Position of the identified peaks extracted from the WAVECAL table.
        wavelengths : ndarray
            Wavelengths related to the peaks extracted from the WAVECAL table.
        """
        # noinspection PyPackageRequirements
        from matplotlib import pyplot as plt
        from scipy.signal import argrelmax

        x = np.arange(data.size)

        fig, ax = plt.subplots(num="{:s}_{:d} Lines".format(name, ext_num))

        print(x.size, data.size)

        ax.plot(x, data, 'C0-')
        ax.set_xlabel('pixels')
        ax.set_ylabel('weights [counts]')
        ax.set_title("{} - Lines Identified".format(name))
        ax.grid(alpha=0.25)

        n = 20

        argmaxs = argrelmax(data, order=3)[0]
        peak_idxs = [np.argmin(np.abs(p - argmaxs)) for p in peaks]
        peaks = argmaxs[np.array(peak_idxs)]

        peak_values = data[peaks]
        idxs = np.argsort(peak_values)[-n:]

        peaks = peaks[idxs]
        wavelengths = wavelengths[idxs]

        for p, w in zip(peaks, wavelengths):
            v = np.max(data.data[p - 3:p + 3])
            ymin = v + 0.01
            ymax = v + 0.2 + 0.1 * v

            ax.vlines(p, ymin=ymin, ymax=ymax, alpha=0.5, color='C1')
            ax.text(p, ymax + 0.01, '{:.02f}'.format(10 * w),
                    rotation='vertical', va='bottom', ha='center', size='small')

        fig_name = os.path.join(
            output_folder,
            name + '_{:02d}_{:s}_{:.0f}.svg'.format(
                ext_num, grating, central_wavelength))

        oldmask = os.umask(000)
        fig.savefig(fig_name)
        os.chmod(fig_name, mode=0o775)
        os.umask(oldmask)

        del fig, ax

    def test_arc_lines_are_properly_matched(self, inputs_for_tests):
        """
        Test that Arc lines are properly matched to the reference lines.
        """
        ad = inputs_for_tests.ad
        output_folder = inputs_for_tests.output_dir

        name, _ = os.path.splitext(ad.filename)
        grating = ad.disperser(pretty=True)
        central_wavelength = ad.central_wavelength() * 1e10

        for ext_num, ext in enumerate(ad):

            table = ext.WAVECAL
            peaks = np.array(table['peaks'])
            wavelengths = np.array(table['wavelengths'])

            data, mask = self.remove_spect_continuum(ext.data, ext.mask)

            self.plot_spectrum(
                name, ext_num, output_folder, data, mask, peaks, wavelengths,
                grating, central_wavelength)

    # noinspection PyUnusedLocal
    @staticmethod
    def test_reduced_arcs_contain_model_with_expected_rms(inputs_for_tests):
        """
        Make sure that the WAVECAL model was fitted with an RMS smaller than
        0.5.
        """
        ad = inputs_for_tests.ad

        for ext in ad:

            if not hasattr(ext, 'WAVECAL'):
                continue

            table = ext.WAVECAL
            coefficients = table['coefficients']
            rms = coefficients[table['name'] == 'rms']

            np.testing.assert_array_less(rms, 0.5)

    @staticmethod
    def test_reduced_arcs_contains_model_with_stable_wavelength_solution(inputs_for_tests):
        """
        Make sure that the wavelength solution gives same results on different
        runs.
        """
        from gempy.library.astromodels import dict_to_chebyshev

        ad = inputs_for_tests.ad
        output_folder = inputs_for_tests.output_dir
        reference_folder = inputs_for_tests.ref_dir

        filename = ad.filename
        output = os.path.join(output_folder, filename)
        reference = os.path.join(reference_folder, filename)

        if not os.path.exists(output):
            pytest.skip('Output file not found: {}'.format(output))

        if not os.path.exists(reference):
            pytest.fail('Reference file not found: {}'.format(reference))

        ad_ref = astrodata.open(reference)

        for ext, ext_ref in zip(ad, ad_ref):
            model = dict_to_chebyshev(
                dict(zip(ext.WAVECAL["name"], ext.WAVECAL["coefficients"]))
            )

            ref_model = dict_to_chebyshev(
                dict(zip(ext_ref.WAVECAL["name"], ext_ref.WAVECAL["coefficients"]))
            )

            x = np.arange(ext.shape[1])
            y = model(x)
            ref_y = ref_model(x)

            np.testing.assert_allclose(y, ref_y, rtol=1)