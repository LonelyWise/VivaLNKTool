#
#	=================
#	=  CHANGE LOG   =
#	= Troy P. Kling =
#	=================
#
#	08/22/2019:
#		- Version 1.0.1.0001
#		- Initial release.
#	08/27/2019:
#		- Version 1.0.1.0002
#		- Added new documentation for helper functions.
#		- Improved existing documentation.
#	08/29/2019:
#		- Version 1.0.2.0001
#		- Corrected a floating point arithmetic error in the derivative operator.
#		- Edited to agree with the Python version.
#		- Corrected version numbers.
#	09/28/2020:
#		- Version 1.0.3.0001
#		- Added functions for finding the minimum and maximum values in an array.
#

import numpy as np
import sklearn.decomposition


def get_pca(x_filt, y_filt, z_filt):
    """
    PCA on 3D SCG signal

    ----------
    Parameters
    ----------
    x_filt           : An array containing x-axis filtered signal data
    y_filt           : An array containing y-axis filtered signal data
    z_filt           : An array containing z-axis filtered signal data

    -------
    Returns
    -------
    An array of transformed PCA signal uninverted by axis of greatest eigenvalue
    """
    X = np.vstack((x_filt, y_filt, z_filt)).T
    model = sklearn.decomposition.PCA(n_components=1)
    pca = model.fit((X - np.mean(X, axis=0)) / np.std(X, axis=0))
    ev = pca.components_[0]
    i = np.argmax(abs(ev))
    if ev[i] < 0:
        ev = -ev
    new_pca = ev[0] * x_filt + ev[1] * y_filt + ev[2] * z_filt
    return new_pca


def abs_array(sig, length):
    """
    Absolute value function.

    ----------
    Parameters
    ----------
    sig             : An array containing signal data.
    length          : The length of the signal.

    -------
    Returns
    -------
    A section of the absolute valued signal.
    """

    a = np.zeros(length)

    for i in range(0, length):
        a[i] = np.abs(sig[i])

    return a


def square_array(sig, length):
    """
    Squaring function.

    ----------
    Parameters
    ----------
    sig             : An array containing signal data.
    length          : The length of the signal.

    -------
    Returns
    -------
    A section of the squared signal.
    """

    a = np.zeros(length)

    for i in range(0, length):
        a[i] = sig[i] * sig[i]

    return a


def sort_array(sig, length):
    """

    """

    result = np.zeros(len(sig))
    for i in range(0, length):
        result[i] = sig[i]

    for i in range(1, length):
        key = result[i]
        j = i - 1

        while j >= 0 and result[j] > key:
            result[j + 1] = result[j]
            j = j - 1
        result[j + 1] = key

    return result


def min_array(sig, length):
    """

    """

    if length == 0:
        return 0

    min_val = np.inf
    for i in range(0, length):
        if sig[i] < min_val:
            min_val = sig[i]

    return min_val


def max_array(sig, length):
    """

    """

    if length == 0:
        return 0

    max_val = -np.inf
    for i in range(0, length):
        if sig[i] > max_val:
            max_val = sig[i]

    return max_val


def median_array(sig, length):
    """

    """

    if length == 0:
        return 0

    result = sort_array(sig, length)

    if length % 2 == 0:
        return (result[int(length / 2) - 1] + result[int(length / 2)]) / 2.0
    else:
        return result[int(length / 2)]


def mean_array(sig, length):
    """
    Calculates the mean of the elements in an array.

    ----------
    Parameters
    ----------
    sig             : An array containing signal data.
    length          : The length of the signal.

    -------
    Returns
    -------
    The mean of the elements in the array.
    """

    if length == 0:
        return 0

    mean = 0

    for i in range(0, length):
        mean += sig[i]
    mean = mean / length

    return mean


def std_array(sig, length):
    """
    Calculates the standard deviation of the elements in an array.

    ----------
    Parameters
    ----------
    sig             : An array containing signal data.
    length          : The length of the signal.

    -------
    Returns
    -------
    The standard deviation of the elements in the array.
    """

    if length == 0:
        return 0

    mean = 0
    std = 0
    dev = 0

    mean = mean_array(sig, length)

    for i in range(0, length):
        dev = sig[i] - mean
        std += dev * dev
    std = np.sqrt(std / length)

    return std


def convolve(sig, length, kernel, width):
    """
    Convolution operator.

    ----------
    Parameters
    ----------
    sig             : An array containing signal data.
    length          : The length of the signal.
    kernel          : The kernel to use for convolution.
    width           : The width of the kernel.

    -------
    Returns
    -------
    A section of the convolved signal.
    """

    # Initialize an empty array.
    result = np.zeros(length)
    temp = 0

    # Use convolution to apply the convolution operator to the signal.
    for i in range(0, length):
        temp = 0
        for j in range(-width, width + 1):
            if i + j >= 0 and i + j < length:
                temp += kernel[j + width] * sig[i + j]
        result[i] = int(temp)

    return result


def differentiate(sig, length, h):
    """
    Derivative operator.

    ----------
    Parameters
    ----------
    sig             : An array containing signal data.
    length          : The length of the signal.
    h               : The width of the derivative operator.

    -------
    Returns
    -------
    The differentiated signal.
    """

    result = np.zeros(length)

    for i in range(0, h):
        result[i] = 0
    for i in range(h, length):
        result[i] = int((sig[i] - sig[i - h]) / h)

    return result


def integrate(sig, length, width):
    """
    Integral operator.

    ----------
    Parameters
    ----------
    sig             : An array containing signal data.
    length          : The length of the signal.
    width           : The width of the integral operator.

    -------
    Returns
    -------
    The integrated signal.
    """

    result = np.zeros(length)

    kernel = np.ones(2 * width + 1)
    result = convolve(sig, length, kernel, width)

    return result


def filtfilt(sig, length, b, a, zi, n):
    """
    Forward-backward filter.

    ----------
    Parameters
    ----------
    sig             : An array containing signal data.
    length          : The length of the signal.
    b               : An array containing transfer function coefficients (numerator).
    a               : An array containing transfer function coefficients (denominator).
    zi              : An array containing initial conditions for the filter.
    n               : The length of the b and a arrays.

    -------
    Returns
    -------
    The filtered signal.
    """

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    #
    #	How to calculate b, a, and zi in Python:
    #		low = 5
    #		high = 25
    #		fs = 128
    #		b, a = signal.butter(2, Wn=[low/(fs/2), high/(fs/2)], btype="bandpass")
    #		zi = signal.lfilter_zi(b, a)
    #
    #	Example of hard-coded b, a, and zi:
    #		b =  np.array([ 0.13993929,  0.        , -0.27987857,  0.        ,  0.13993929])
    #		a =  np.array([ 1.        , -2.26820013,  2.08268532, -1.02392152,  0.25949518])
    #		zi = np.array([-0.13993929, -0.13993929,  0.13993929,  0.13993929])
    #
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    # Initialize some empty arrays.
    y1 = np.zeros(length)
    y2 = np.zeros(length)
    result = np.zeros(length)
    temp = 0

    # Forward filter.
    # y[n] = b[0]*x[n] + b[1]*x[n-1] + ... + b[N]*x[n-N]
    #                  - a[1]*y[n-1] - ... - a[N]*y[n-N]
    for i in range(0, n - 1):
        temp = zi[i] * sig[0]
        for j in range(0, i + 1):
            temp += b[j] * sig[i - j]
        for j in range(1, i + 1):
            temp -= a[j] * y1[i - j]
        y1[i] = temp
    for i in range(n - 1, length):
        temp = 0
        for j in range(0, n):
            temp += b[j] * sig[i - j]
        for j in range(1, n):
            temp -= a[j] * y1[i - j]
        y1[i] = temp

    # Backward filter.
    for i in range(0, n - 1, 1):
        temp = zi[i] * y1[length - 1]
        for j in range(0, i + 1):
            temp += b[j] * y1[length - 1 - i + j]
        for j in range(1, i + 1):
            temp -= a[j] * y2[length - 1 - i + j]
        y2[length - 1 - i] = temp
    for i in range(n - 1, length):
        temp = 0
        for j in range(0, n):
            temp += b[j] * y1[length - 1 - i + j]
        for j in range(1, n):
            temp -= a[j] * y2[length - 1 - i + j]
        y2[length - 1 - i] = temp

    return y2


def savgol_filter(sig, length, kernel, width):
    """
    Savitzy-Golay filter.

    ----------
    Parameters
    ----------
    sig             : An array containing signal data.
    length          : The length of the signal.
    kernel          : The kernel to use for convolution.
    width           : The width of the kernel.

    -------
    Returns
    -------
    The filtered signal.
    """

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    #
    #	How to calculate v in Python:
    #		width = 7
    #		degree = 3
    #		kernel = np.linalg.pinv([[k**i for i in range(degree+1)] for k in range(-width, width+1)])[0]
    #
    #	Example of hard-coded kernel:
    #		kernel = np.array([-0.07058824, -0.01176471,  0.03800905,  0.07873303,  0.11040724,
    #							0.13303167,  0.14660633,  0.15113122,  0.14660633,  0.13303167,
    #							0.11040724,  0.07873303,  0.03800905, -0.01176471, -0.07058824])
    #
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    return convolve(sig, length, kernel, width)