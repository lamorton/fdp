# -*- coding: utf-8 -*-
"""
Created on Thu Oct 29 10:20:43 2015

@author: ktritz
"""
from __future__ import print_function
from __future__ import division

from builtins import map
from builtins import range
#from past.utils import old_div
from warnings import warn
#import time

import numpy as np
import numba as nb
#import matplotlib as mpl
# mpl.use('TkAgg')
import matplotlib.pyplot as plt
#import pyqtgraph as pg

from ..lib.globals import FdpWarning

# pg.mkQApp()




def plot1d(signal, time=None, tmin=0.0, tmax=None, axes=None, **kwargs):
    xaxis = getattr(signal, signal.axes[0])
    kwargs.pop('stack', None)
    kwargs.pop('signals', None)
    kwargs.pop('maxrange', None)
    kwargs.pop('minrange', None)
    ax = axes
    ax.plot(xaxis, signal, label=signal._name, **kwargs)
    ax.set_ylabel('{} ({})'.format(signal._name, signal.units))
    ax.set_xlabel('{} ({})'.format(xaxis._name, xaxis.units))
    ax.set_title('{} -- {} -- {}'.format(signal._parent._name.upper(),
                                         signal._name,
                                         signal.shot))
    if tmax is not None:
        ax.set_xlim(tmin, tmax)
    if time is not None and signal.axes[0]=='time':
        if hasattr(time, '__iter__'):
            if len(time)>1:
                ax.set_xlim(time[0], time[1])
            else:
                ax.set_xlim(-100,time[0])
        else:
            ax.set_xlim(-100,time)



def plot2d(signal, tmin=0.0, tmax=None, axes=None, **kwargs):
    plot_type = kwargs.pop('type', 'contourf')
    nlevels = int(kwargs.pop('nlevels', 100))
    default_min = float(kwargs.pop('minrange', 0.))
    default_max = float(kwargs.pop('maxrange', 1.))

    plot_func = getattr(plt, plot_type)
    xaxis = getattr(signal, signal.axes[1])
    yaxis = getattr(signal, signal.axes[0])
    xaxis[:]
    yaxis[:]
    if tmax is None:
        tmax = yaxis[-1]  # this should be yaxis.max() when fixed
    plot_range = set_range(signal, default_min, default_max)
    levels = np.linspace(plot_range[0], plot_range[1], nlevels)
    plt.sca(axes)
    artist = plot_func(np.array(xaxis), np.array(yaxis), np.array(signal),
                       levels=levels, **kwargs)
    plt.ylabel('{} ({})'.format(yaxis._name, yaxis.units))
    plt.xlabel('{} ({})'.format(xaxis._name, xaxis.units))
    plt.title('{} -- {} -- {}'.format(signal._parent._name.upper(),
                                      signal._name,
                                      signal.shot))
    plt.ylim(tmin, tmax)
    if plot_type == 'contourf':
        cbar = plt.colorbar(artist, format='%.1e')
        cbar.set_label(signal.units, rotation=270)


def set_range(data, default_min, default_max):
    max_range = np.array(data).max()
    min_range = np.array(data).min()
    if default_max is 1. and default_min is 0.:
        return min_range, max_range
    hist_data = np.histogram(data, bins=20000)
    cumulative = hist_data[0].cumsum()
    if default_max < 1.0:
        max_index = np.where(cumulative > default_max * cumulative[-1])[0][0]
        max_range = hist_data[1][max_index] * 1.15
    if default_min > 0.0:
        min_index = np.where(cumulative > default_min * cumulative[-1])[0][0]
        min_range = hist_data[1][min_index]
        min_range -= 0.15 * abs(min_range)
    return min_range, max_range


def plot3d(data, xaxis, yaxis, zaxis, **kwargs):
    print('3D')


def update3d(value):
    pass


def plot4d(data, xaxis, yaxis, zaxis, taxis, **kwargs):
    print('4D')


plot_methods = [None, plot1d, plot2d, plot3d, plot4d]


def plot(signal, fig=None, axes=None, **kwargs):
    defaults = getattr(signal, '_plot_defaults', {})
    kwargs.update(defaults)
    if signal._is_container():
        plot_container(signal, **kwargs)
        return

    signal[:]
    if signal.size==0:
        warn("Empty signal {}".format(signal.mdsnode), FdpWarning)
    signal.time[:]
    if signal.time.size==0:
        warn("Empty signal.time {}".format(signal.time.mdsnode), FdpWarning)

    dims = signal.ndim
    multi_axis = kwargs.get('multi', None)
    if multi_axis is 'shot':
        #plot_multishot(signal, **kwargs)
        #plt.title(signal._name, fontsize=20)
        return
    if multi_axis in signal.axes and dims > 1:
        plot_multi(signal, ax=axes, **kwargs)
        plt.title(signal._name, fontsize=20)
        return

    if axes is None:
        if fig is None:
            fig = plt.figure()
        axes = fig.add_subplot(111)

    if 1:  # dims > 1:
        plot_methods[dims](signal, axes=axes, **kwargs)
        # fig.show()
    else:
        if not len(fig.axes):
            axes = PlotAxes(plot_methods[dims], fig, [0.1, 0.1, 0.8, 0.8])
        else:
            axes = fig.axes[0]
        axes.callbacks.connect('xlim_changed', axes._update_all_plots)
        fig.add_axes(axes)
        axes.plot(signal, **kwargs)
        fig.canvas.draw()
        fig.canvas.mpl_connect('resize_event', axes._update_all_plots)
    # return fig


def plot_multi(signal, ax=None, **kwargs):
    default_min = float(kwargs.pop('minrange', 0.))
    default_max = float(kwargs.pop('maxrange', 1.))
    plot_range = set_range(signal, default_min, default_max)

    axis_name = kwargs.pop('multi', None)
    kwargs.pop('type', None)
    kwargs.pop('stack', '1,1')
    kwargs.poop('signals', None)
    axes = [getattr(signal, axis) for axis in signal.axes]
    axis_index = signal.axes.index(axis_name)
    multi_axis = axes.pop(axis_index)
    if ax is None:
        ax = plt.subplot(111)
    ax.grid()
    legend = kwargs.pop('legend', False)
    for index, label in enumerate(multi_axis):
        label = '{} = {:.3f} {}'.format(axis_name, label, multi_axis.units)
        data = np.take(signal, index, axis=axis_index)
        plot_axes = [np.take(axis, index, axis=axis.axes.index(axis_name))
                     if axis_name in axis.axes else axis for axis in axes]
        plot_methods[data.ndim](data, *plot_axes, label=label, **kwargs)
    if legend:
        plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
        plt.subplots_adjust(right=0.65)
    plt.show()
    ax.set_ylim(plot_range[0], plot_range[1])
    kwargs['multi'] = axis_name


def plot_container(container, **kwargs):
    stack = kwargs.pop('stack', '1,1')
    plot_sigs = kwargs.pop('signals', None)
    if plot_sigs is not None:
        plot_sigs = plot_sigs.split(',')
    vstack, hstack = tuple(map(int, stack.split(',')))
    num = hstack * vstack
    index = 0
    fig = plt.figure(figsize=(2 + 3 * hstack, 4 + 2 * vstack))
    # title = container._get_branch().upper()
    # plt.suptitle('Shot #{} {}'.format(container.shot, title),
    #              x=0.5, y=1.00, fontsize=20, horizontalalignment='center')
    for signal in list(container._signals.values()):
        if plot_sigs:
            if signal._name not in plot_sigs:
                continue
        index += 1
        if index > num:
            fig = plt.figure()
            index = 1
        if index == 1:
            ax = plt.subplot(vstack, hstack, index)
        else:
            ax = plt.subplot(vstack, hstack, index)  # , sharex=ax, sharey=ax)
        signal.plot(fig=fig, ax=ax, **kwargs)
    plt.tight_layout()


class PlotAxes(plt.Axes):

    def __init__(self, plot_method, *args, **kwargs):
        plt.Axes.__init__(self, *args, **kwargs)
        self.callbacks.connect('xlim_changed', self._update_all_plots)
        self._plot_objects = []
        self.method = plot_method
        self.limits = None

    def plot(self, signal, *args, **kwargs):
        index_list = []
        stride = kwargs.get('stride', 0)
        if stride:
            stride_levels = np.floor(np.log(signal.size // 3000) // 
                                     np.log(stride))
            index_list = [numba_decimate_stride(signal, int(level))
                          for level in np.arange(stride_levels) + 1]
        myplot = signal, index_list, args, kwargs
        self._plot_objects.append(myplot)
        self._update_plot(myplot)
        self._set_limits(signal)

    def _update_all_plots(self, event):
        self.clear()
        for myplot in self._plot_objects:
            self._update_plot(myplot)
        self.callbacks.connect('xlim_changed', self._update_all_plots)

    def _update_plot(self, myplot):

        signal, index_list, args, kwargs = myplot
        axes = [getattr(signal, axis) for axis in signal.axes]

        y = signal
        x = axes[0]
        # dpi = self.figure.get_dpi()

        autoscale = self.get_autoscale_on()

        if autoscale:
            self.set_autoscale_on(False)

        # width = self.get_position().width * self.figure.get_figwidth()

        # nx = int(round(width * dpi))
        nx = 3e3
        xmin, xmax = self.get_xlim()
        ymin, ymax = self.get_ylim()

        ixmin = np.searchsorted(x, xmin, side='left')
        ixmax = np.searchsorted(x, xmax * 1.1, side='right')
        stride = kwargs.pop('stride', 0)
        kwargs.pop('type', None)
        kwargs.pop('stack', None)
        stride_level = 0
        if stride:
            stride_level = int(np.floor(np.log((ixmax - ixmin) // nx) 
                // np.log(stride)))
            if stride_level:
                dec_index = index_list[stride_level - 1]
                dec_min = np.searchsorted(dec_index, ixmin, side='left')
                dec_max = np.searchsorted(dec_index, ixmax, side='right')
                index = dec_index[dec_min:dec_max]
                super(PlotAxes, self).plot(x[index], y[index], *args, **kwargs)
                return
        xdata = x[ixmin:ixmax]
        ydata = y[ixmin:ixmax]
        use_numba = kwargs.pop('numba', False)
        if use_numba:
            dec_index = numba_decimate(ydata)
        else:
            dec_index = decimate_plot(ydata)
        super(PlotAxes, self).plot(
            xdata[dec_index], ydata[dec_index], *args, **kwargs)

    def _set_limits(self, signal):
        if len(signal.axes) > 1:
            y = np.array(getattr(signal, signal.axes[0]))
            x = np.array(getattr(signal, signal.axes[1]))
        else:
            y = np.array(signal)
            x = np.array(getattr(signal, signal.axes[0]))
        if self.limits is None:
            xmin = np.min(x)
            xmax = np.max(x)
            ymin = np.min(y)
            ymax = np.max(y)
        else:
            pxmin, pxmax = self.limits[0]
            pymin, pymax = self.limits[1]
            pzmin, pzmax = self.limit[2]
            xmin = min(np.min(x), pxmin)
            xmax = max(np.max(x), pxmax)
            ymin = min(np.min(y), pymin)
            ymax = max(np.max(y), pymax)
        self.set_xlim(xmin, xmax)
        self.set_ylim(ymin, ymax)
        self.limits = ((xmin, xmax), (ymin, ymax))


# class PyQTPlot(pg.PlotCurveItem):
#    def __init__(self, *args, **kwds):
#        self.hdf5 = None
#        self.limit = 10000  # maximum number of samples to be plotted
#        pg.PlotCurveItem.__init__(self, *args, **kwds)
#
#    def setHDF5(self, data):
#        self.hdf5 = data
#        self.updateHDF5Plot()
#
#    def viewRangeChanged(self):
#        self.updateHDF5Plot()
#
#    def updateHDF5Plot(self):
#        if self.hdf5 is None:
#            self.setData([])
#            return
#
#        vb = self.getViewBox()
#        if vb is None:
#            return  # no ViewBox yet
#
#        # Determine what data range must be read from HDF5
#        xrange = vb.viewRange()[0]
#        start = max(0, int(xrange[0])-1)
#        stop = min(len(self.hdf5), int(xrange[1]+2))
#
#        # Decide by how much we should downsample
#        ds = int((stop-start) / self.limit) + 1
#
#        if ds == 1:
#            # Small enough to display with no intervention.
#            visible = self.hdf5[start:stop]
#            scale = 1
#        else:
#            # Here convert data into a down-sampled array suitable for visualizing.
#            # Must do this piecewise to limit memory usage.
#            samples = 1 + ((stop-start) // ds)
#            visible = np.zeros(samples*2, dtype=self.hdf5.dtype)
#            sourcePtr = start
#            targetPtr = 0
#
#            # read data in chunks of ~1M samples
#            chunkSize = (1000000//ds) * ds
#            while sourcePtr < stop-1:
#                chunk = self.hdf5[sourcePtr:min(stop, sourcePtr+chunkSize)]
#                sourcePtr += len(chunk)
#
#                # reshape chunk to be integral multiple of ds
#                chunk = chunk[:(len(chunk)//ds) * ds].reshape(len(chunk)//ds, ds)
#
#                # compute max and min
#                chunkMax = chunk.max(axis=1)
#                chunkMin = chunk.min(axis=1)
#
#                # interleave min and max into plot data to preserve envelope shape
#                visible[targetPtr:targetPtr+chunk.shape[0]*2:2] = chunkMin
#                visible[1+targetPtr:1+targetPtr+chunk.shape[0]*2:2] = chunkMax
#                targetPtr += chunk.shape[0]*2
#
#            visible = visible[:targetPtr]
#            scale = ds * 0.5
#
#        self.setData(visible)  # update the plot
#        self.setPos(start, 0)  # shift to match starting index
#        self.resetTransform()
#        self.scale(scale, 1)   # scale to match downsampling


def decimate_plot(data, pixels=2000):
    # returns a decimated indices array to visually approximate a plot with
    # points >> pixels
    if data.size <= pixels * 2:
        return np.arange(data.size)
    stride = (data.size - 2) // (pixels - 1)
    endpoint = (pixels - 1) * stride + 1
    data2D = data[1:endpoint].reshape((pixels - 1, stride))
    column_offset = np.arange(pixels - 1) * stride + 1
    data_min = data2D.argmin(axis=1) + column_offset
    data_max = data2D.argmax(axis=1) + column_offset
    data_endmin = data[endpoint:-2].argmin() + endpoint
    data_endmax = data[endpoint:-2].argmax() + endpoint
    decimate_index = np.dstack((data_min, data_max)).flatten()
    decimate_index = np.concatenate(([0], decimate_index,
                                     [data_endmin], [data_endmax],
                                     [data.size - 1]))
    return np.sort(decimate_index)


@nb.autojit(nopython=True)
def numba_decimate(data, pixels=2000):
    # returns a decimated indices array to visually approximate a plot with
    # points >> pixels
    output = np.zeros(2 * pixels + 2, dtype=np.int64)
    if data.size <= pixels * 2:
        return np.arange(data.size)
    stride = (data.size - 2) // (pixels - 1)
    output[0] = 0
    output[-1] = data.size - 1
    for pixel in range(1, pixels + 1):
        offset = 1 + stride * (pixel - 1)
        arrmin = data[offset]
        arrmax = data[offset]
        minind = offset
        maxind = offset
        if offset + stride > data.size - 1:
            stride = data.size - offset - 1
        for index in range(offset + 1, offset + stride):
            check = data[index]
            if check < arrmin:
                minind = index
                arrmin = check
            else:
                if check > arrmax:
                    maxind = index
                    arrmax = check
        if maxind > minind:
            output[2 * pixel - 1] = minind
            output[2 * pixel] = maxind
        else:
            output[2 * pixel - 1] = maxind
            output[2 * pixel] = minind
    return output


@nb.autojit(nopython=True)
def numba_decimate_stride(data, stride):
    # returns a decimated indices array to visually approximate a plot with
    # points >> pixels
    elements = 2 * (data.size - 2) // stride + 2
    output = np.zeros(elements, dtype=np.int64)
    output[0] = 0
    output[-1] = data.size - 1
    for element in range(1, elements - 1, 2):
        offset = 1 + stride * (element - 1) / 2
        arrmin = data[offset]
        arrmax = data[offset]
        minind = offset
        maxind = offset
        if offset + stride > data.size - 1:
            stride = data.size - offset - 1
        for index in range(offset + 1, offset + stride):
            check = data[index]
            if check < arrmin:
                minind = index
                arrmin = check
            else:
                if check > arrmax:
                    maxind = index
                    arrmax = check
        if maxind > minind:
            output[element] = minind
            output[element + 1] = maxind
        else:
            output[element] = maxind
            output[element + 1] = minind
    return output
