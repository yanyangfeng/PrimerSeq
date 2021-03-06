#!/usr/bin/env python
# Copyright (C) 2012-2013  Collin Tokheim
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

'''
Created on Feb 8, 2012-2013

@author: Collin
'''
# external dependencies
import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib.collections import PatchCollection
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredText   # import anchored text
from collections import Counter, namedtuple
import argparse
from operator import *
import json
import csv
import utils
# custom imports
from shapes import ExonRectangle, JunctionLine
from matplotlib.offsetbox import AnchoredOffsetbox, TextArea, DrawingArea, HPacker


def offset_text(ax, txt, loc, bbox_to_anchor=(-.03, .65)):
    box1 = TextArea(txt, textprops=dict(color="k", size='10'))

    box = HPacker(children=[box1],
                  align="center",
                  pad=2, sep=5)

    anchored_box = AnchoredOffsetbox(loc=loc,
                                     child=box, pad=0.,
                                     frameon=False,
                                     prop=dict(size=5),
                                     bbox_to_anchor=bbox_to_anchor,
                                     bbox_transform=ax.transAxes,
                                     borderpad=0.1,
                                     )
    ax.add_artist(anchored_box)


def draw_text(ax, txt):
    """
    Add text in right corner that identifies the data
    """

    at = AnchoredText(txt,
                      loc=1, prop=dict(size=13), frameon=True,)
    at.patch.set_boxstyle("round,pad=0.,rounding_size=0.2")
    ax.add_artist(at)


def addCommas(myNum):
    strNum = str(int(myNum))[::-1]
    numLength = len(strNum)

    # figure out the number of commas needed
    numCommas = numLength / 3

    # find the remainder
    remainder = numLength % 3

    # get 3 digit substrings
    subStrings = []
    i = 1
    for i in range(0, numCommas):
        tmp = strNum[i*3:i*3+3]
        revTemp = tmp[::-1]
        subStrings = [revTemp] + subStrings

    if not remainder == 0:
        # add first digits in number
        tmp = strNum[-remainder:]
        revTmp = tmp[::-1]
        subStrings = [revTmp] + subStrings

    # return comma seperated integer
    return ",".join(subStrings)


def estimate_isoform_psi(tx_paths, counts):
    num_edges = map(lambda x: len(x) - 1, tx_paths)
    normalized_counts = [count/float(num_edges[i]) if num_edges[i] else 0.0 for i, count in enumerate(counts)]
    return [ct/sum(normalized_counts) for ct in normalized_counts]


def scale_intron_length(exonShapes, scale):
    firstFlag = True
    tmpList = []
    previous = None
    previousActual = None
    for index, exonRect in enumerate(exonShapes):
        if not firstFlag == True:
            dist = exonRect.start - previousActual.stop  # distance from the previous (non-modified) exon
            tmpStart = int(dist/scale) + previous.stop  # scale distance between exons and plot relative to last exon
            dif = tmpStart - exonRect.start
            previousActual = ExonRectangle(start = exonRect.start, stop = exonRect.stop, mid = 0, height = 1)  # the actual coordinates of the exon
            exonRect.shift(dif)
            tmpList.append(exonRect)
            previous = exonRect
        else:
            previousActual = exonRect
            previous = exonRect
            tmpList.append(exonRect)
            firstFlag = False
    return tmpList  # return exon shape objects accounting for positions changing do to scaling introns


def editAxis(ax, include=[], notInclude=[]):
    for loc, spine in ax.spines.iteritems():
        if loc in include:
            spine.set_position(('outward', 10))  # outward by 10 points
        elif loc in notInclude:
            spine.set_color('none')  # don't draw spine
        else:
            raise ValueError('unknown spine location: %s' % loc)


def exonDrawSubplot(ax, exons, tgt_exon, strand, pct, options, prod_length=False):  # exons was coords
    # move/remove axis
    includedAxes = ["bottom"]
    notIncludedAxes = ["left", "right", "top"]
    editAxis(ax, include=includedAxes, notInclude=notIncludedAxes)  # funtion to remove/modify axis

    # turn off ticks where there is no line
    ax.xaxis.set_ticks_position('bottom')
    ax.yaxis.set_ticks_position('left')

    # get ExonRectangle objects
    exonRectangles = []
    for myIndex, (tmpStart, tmpStop) in enumerate(exons):
        tmpRect = ExonRectangle(start=tmpStart, stop=tmpStop, mid=0, height=1)
        exonRectangles.append(tmpRect)  # holds the exons to be drawn
    exonRectangles.sort(key=lambda x: (x.start, x.stop))

    # scale intron length
    exonRectangles = scale_intron_length(exonRectangles, options['scale'])
    new_start, new_stop = exonRectangles[0].start, exonRectangles[-1].stop

    # add lines when applicable
    my_junction_line = JunctionLine(exonRectangles)
    my_junction_line.createExonLines()
    exon_lines = my_junction_line.get_exon_lines()

    # exonLines could be empty
    span_length = exonRectangles[-1].stop - exonRectangles[0].start
    triangle_rate = 5
    marker_symbol = '$>$' if strand == '+' else '$<$'
    for tmp_line in exon_lines:
        tmp_x, tmp_y = zip(*tmp_line)
        dist = tmp_x[1] - tmp_x[0]
        num_triangles = (dist * triangle_rate) / float(span_length)
        if num_triangles:
            ax.plot(tmp_x, tmp_y, linewidth=1, color='black')
            triangle_x_pos = np.linspace(tmp_x[0], tmp_x[1], num_triangles + 2)[1:-1]
            triangle_y_pos = (tmp_y[0] - .02) * np.ones((len(triangle_x_pos), 1))
            ax.scatter(triangle_x_pos, triangle_y_pos, marker=marker_symbol, color='black')
        else:
            ax.plot(tmp_x, tmp_y, linewidth=1, color='black')


    ### start plotting exons ###
    # plot exons
    patches = []
    exonCount = 0
    for tmpExon in exonRectangles:
        art = mpatches.Rectangle(np.array([tmpExon.exon_start, tmpExon.bottom_left.y]), tmpExon.exon_stop - tmpExon.exon_start, tmpExon.height)
        art.set_clip_on(True)
        patches.append(art)
        exonCount += 1
    collection = PatchCollection(patches, cmap=matplotlib.cm.jet, alpha=1)

    # make color scheme size match the number of exons
    color_scheme = [[.6, 0, 0] if tuple(e) == tgt_exon else [0, 0, 0] for e in exons]
    edge_color_scheme = [[.45, 0, 0] if tuple(e) == tgt_exon else [0, 0, 0] for e in exons]
    # color_scheme = [[0, 0, 0]] * len(exons)

    # plot exons
    collection.set_facecolor(color_scheme)
    collection.set_edgecolor(edge_color_scheme)
    ax.add_collection(collection)
    ### end plotting exons ###

    ax.set_ylim(-1.0, 1.0)
    plt.gca().axes.get_yaxis().set_visible(False)
    if isinstance(pct, (float, int)):
        if prod_length:
            # primers amplify this isoform case
            offset_text(ax, '%.1f' % (100 * pct) + '%\n' + '%d bp' % prod_length, 1, (-.03, .75))
        else:
            # primers don't amplify that isoform case
            offset_text(ax, '%.1f' % (100 * pct) + '%\n' + 'N/A', 1, (-.03, .75))
    else:
        offset_text(ax, pct, 1)
    # if prod_length:
    #    offset_text(ax, '%d bp' % prod_length, 1, (1.13, .65))

    return ax, new_start, new_stop


def retrieve_top(tx_paths, counts, n=5):
    # sort the potential paths by normalized counts
    tmp = zip(counts, tx_paths)
    tmp.sort(key=lambda x: -float(x[0])/(len(x[1]) - 1) if len(x[1]) > 1 else 0)
    top_counts, top_tx_paths = zip(*tmp)
    percent_estimate = estimate_isoform_psi(top_tx_paths, top_counts)
    if len(top_tx_paths) >= n:
        counts = top_counts[:n]
        tx_paths = top_tx_paths[:n]
        percent_estimate = percent_estimate[:n]
        num_of_txs = n
    else:
        counts = top_counts
        tx_paths = top_tx_paths
        num_of_txs = len(top_tx_paths)
    return tx_paths, counts, num_of_txs, percent_estimate


def read_primer_file(primer_file, ID):
    with open(primer_file) as handle:
        for line in csv.reader(handle, delimiter='\t'):
            if line[0] == ID:
                return sorted(map(utils.get_pos, line[2].split(';')),
                              key=lambda x: (x[0], x[1]))  # make sure primer is in numerical order


def get_strand_from_primer_file(primer_file, ID):
    with open(primer_file) as handle:
        for line in csv.reader(handle, delimiter='\t'):
            if line[0] == ID:
                return line[1][0]


def calc_product_length(path, primer_coord):
    """
    Calculate product length based on the primer coordinates
    """
    primer_coord.sort(key=lambda x: (x[0], x[1]))  # make sure primers are sorted by position
    # calculate length between primers
    tmp_len = 0
    first_exon_primer, second_exon_primer = False, False  # flag for telling if a primer was contained within an exon
    flag = False
    for start, end in path:
        if start <= primer_coord[0][0] and end >= primer_coord[0][1] and start <= primer_coord[1][0] and end >= primer_coord[1][1]:
            tmp_len = primer_coord[1][0] - primer_coord[0][1]
            first_exon_primer = True
            second_exon_primer = True
        elif start <= primer_coord[0][0] and end >= primer_coord[0][1]:
            tmp_len += end - primer_coord[0][1]
            flag = True
            first_exon_primer = True
        elif start <= primer_coord[1][0] and end >= primer_coord[1][1]:
            tmp_len += primer_coord[1][0] - start
            flag = False
            second_exon_primer = True
        elif flag:
            tmp_len += end - start

    if not (first_exon_primer and second_exon_primer):
        # case where either one or both primers were not located within an exon
        final_len = 0
    else:
        # add length between primers to actual length of sequnces for each primer
        first_primer_len = primer_coord[0][1] - primer_coord[0][0]
        second_primer_len = primer_coord[1][1] - primer_coord[1][0]
        final_len = tmp_len + first_primer_len + second_primer_len
    return final_len


def main(tx_paths, target_exon, counts, primer_coord, strand, output, options):
    # configurations
    matplotlib.rcParams['font.size'] = 16  # edit font size of title
    matplotlib.rcParams['xtick.labelsize'] = 13
    matplotlib.rcParams['ytick.labelsize'] = 13
    #matplotlib.rc("lines", linewidth=optionDict["thick"])
    plt.close()  # try to make sure previous is closed
    plt.close('all')  # try to make sure previous is closed

    tx_paths, counts, num_of_txs, percent_estimate = retrieve_top(tx_paths, counts, n=10)

    # add primer to drawing
    num_of_drawings = num_of_txs + 1

    fig, axes = plt.subplots(num_of_drawings, 1, sharex=True, sharey=True, figsize=(6, .75 * num_of_drawings))

    # loop through and make all subplots in a figure
    lowest_start, highest_stop = float('inf'), float('-inf')
    for i, ax in enumerate(axes.flat):
        # draw exon structure + junctions
        # exonDrawAxis, new_start, new_stop = exonDrawSubplot(ax, tx_paths[i], percent_estimate[i])

        if i == 0:
            exonDrawAxis, new_start, new_stop = exonDrawSubplot(ax, primer_coord, None, strand, 'primers', options)
        else:
            i -= 1
            prod_length = calc_product_length(tx_paths[i], primer_coord)
            exonDrawAxis, new_start, new_stop = exonDrawSubplot(ax, tx_paths[i], target_exon, strand, percent_estimate[i], options, prod_length)
            lowest_start = lowest_start if lowest_start < new_start else new_start
            highest_stop = highest_stop if highest_stop > new_stop else new_stop

        if i == (num_of_txs - 1):
            first_label, last_label = tx_paths[i][0][0], tx_paths[i][-1][1]
            # exonDrawAxis.set_xlim(new_start, new_stop)
            # exonDrawAxis.set_xticks([new_start, new_stop])  # edited
            exonDrawAxis.set_xlim(lowest_start, highest_stop)
            exonDrawAxis.set_xticks([lowest_start, highest_stop])  # edited
            exonDrawAxis.xaxis.set_ticklabels(["%s" % (addCommas(first_label)), "%s" % (addCommas(last_label))])  # prevents scientific notation and provide scale effect for axis
            exonDrawAxis.get_xticklabels()[0].set_horizontalalignment('left')
            exonDrawAxis.get_xticklabels()[1].set_horizontalalignment('right')
            exonDrawAxis.get_xaxis().set_visible(False)  # set axis invisible
        else:
            exonDrawAxis.get_xaxis().set_visible(False)  # set axis invisible
        editAxis(ax, include=["left"], notInclude=["bottom", "top", "right"])  # removes x-axis spline
        exonDrawAxis.get_yaxis().set_visible(False)  # set axis invisible
        #exonDrawAxis.set_title(exonCoordinates[exonIndex][0] + " " + gene) # add title

    fig.subplots_adjust(hspace=.00, wspace=.00)  # change subplot spacing
    # plt.show()
    plt.savefig(output)
    plt.clf()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='This script displays multiple isoforms and their relative abundance')
    parser.add_argument('-j', action='store', dest='json', help='input json file')
    parser.add_argument('-p', '--primer-file', action='store', dest='primer_file', required=True, help='Path to output file from primer.py')
    parser.add_argument('-i', action='store', dest='id', required=True, help='ID to use from PRIMER_FILE')
    parser.add_argument('-s', action='store', dest='scale', type=int, default=1)
    parser.add_argument('-o', action='store', dest='output', required=True, help='output file')
    options = vars(parser.parse_args())

    with open(options['json']) as handle:
        my_json = json.load(handle)

    main(my_json['path'], my_json['counts'], read_primer_file(options['primer_file'], options['id']), options)
