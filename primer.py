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
**Author:**  Collin Tokheim

**Description:** primer.py can design primers from the command line.
Note that PrimerApp.py (the GUI) just uses the primer module to design the
primers.
'''
import subprocess
import os
import glob
import gtf
import splice_graph
import csv
import argparse  # command line parsing
import itertools as it
from pygr.seqdb import SequenceFileDB
from pygr.sequence import Sequence
import sam
import utils
import shutil
import ConfigParser
import platform

# import for logging file
import logging
import datetime
import time
import sys
import traceback

# create a global variable that holds the config options
my_config = ConfigParser.ConfigParser()
my_config.read('PrimerSeq.cfg')
config_options = dict(my_config.items('directory'))


def gene_annotation_reader(file_path, FILTER_FACTOR=2):
    """
    *creates two data structures from gtf:*

        gene_dict is a dictionary with gene_id's as keys:
            * gene_dict['chr']['My_favorite_gene']['graph'] = list of list of exons
            * gene_dict['chr']['My_favorite_gene']['strand'] = gene strand (+, -)
            * gene_dict['chr']['My_favorite_gene']['chr'] = chromosome
            * gene_dict['chr']['My_favorite_gene']['start'] = start of gene
            * gene_dict['chr']['My_favorite_gene']['end'] = end of gene
            * gene_dict['chr']['My_favorite_gene']['exons'] = the set of exons (nodes)
    """
    # logging.debug('Started reading %s' % file_path)

    # check if GTF file is sorted before reading data
    logging.debug('Checking if GTF file is sorted  . . .')
    if not gtf.is_gtf_sorted(file_path):
        logging.debug('GTF file is not sorted.')
        return None
    logging.debug('GTF is sorted.')

    # iterate through each gtf feature
    file_input = open(file_path)
    gene_dict = {}
    for tx_id, tx in it.groupby(gtf.gtf_reader(file_input, delim='\t'), lambda x: x.attribute['transcript_id']):
        tx = list(tx)
        if len(tx) == 0: continue  # no 'exon' feature case

        gene_id = tx[0].attribute['gene_id']
        strand = tx[0].strand

        # sort exons
        tx_path = sorted([(exon.start, exon.end) for exon in tx],
                         key=lambda x: (x[0], x[1]))  # needs to be sorted because gtf files might not have them in proper order

        # add info to gene_dict
        gene_dict.setdefault(tx[0].seqname, {})
        gene_dict[tx[0].seqname].setdefault(gene_id, {})  # add the gene key if it doesn't exist
        gene_dict[tx[0].seqname][gene_id].setdefault('chr', tx[0].seqname)  # add chr if doesn't exist
        gene_dict[tx[0].seqname][gene_id].setdefault('strand', strand)  # add strand if doesn't exist
        gene_dict[tx[0].seqname][gene_id].setdefault('graph', []).append(tx_path)  # append the tx path
        gene_dict[tx[0].seqname][gene_id].setdefault('start', float('inf'))
        gene_dict[tx[0].seqname][gene_id]['start'] = min(gene_dict[tx[0].seqname][gene_id]['start'], tx_path[0][0])  # change start if this tx has lower start position
        gene_dict[tx[0].seqname][gene_id].setdefault('end', 0)
        gene_dict[tx[0].seqname][gene_id]['end'] = max(gene_dict[tx[0].seqname][gene_id]['end'], tx_path[-1][1])
        gene_dict[tx[0].seqname][gene_id].setdefault('exons', set())
        for ex in tx_path:
            gene_dict[tx[0].seqname][gene_id]['exons'].add(ex)  # hold a set of non-redundant exons
    file_input.close()  # close gtf file
    # logging.debug('Finished reading %s' % file_path)
    return gene_dict


def call_primer3(target_string, jobs_ID):
    """
    Does the actual call to primer3. Will raise a CalledProcessError if primer3
    exits with a non-zero exit status.

    :param str jobs_ID: basename of output file for Primer3
    :param str target_string: coordinate of target exon (only for logging purposes)
    """
    logging.debug('Calling primer3 for %s . . .' % target_string)
    os.chdir(config_options['tmp'])  # make sure primer3 files occur in tmp dir
    cmd = config_options['primer3'] + '/src/primer3_core < ' + jobs_ID + '.conf' + ' > ' + jobs_ID + '.Primer3'
    if platform.system() == 'Windows':
        cmd = cmd.replace('/', '\\')
    logging.debug(cmd)  # record command in log file
    subprocess.check_call(cmd, shell=True)
    logging.debug('Finished call of primer3 for %s' % target_string)
    os.chdir(config_options['primerseq'])  # go back to top level


def read_primer3(path):
    """
    Read the output from primer3_core into a dictionary containing
    the key:value relationship for the output tags.

    :param str path: path to primer3 configuration file (default: primer3.txt)
    """
    primer3_dict = {}
    # read primer3 file
    with open(path, 'r') as infile:
        for line in infile:
            try:
                primer3_dict[line.split('=')[0]] = line.split('=')[1].rstrip()
            except IndexError:
                print line
    return primer3_dict


def mkdir_tmp():
    '''
    Make all the necessary directories for temporary files
    '''
    if not os.path.isdir(config_options['tmp']): os.mkdir(config_options['tmp'])
    if not os.path.isdir(config_options['tmp'] + '/sam'): os.mkdir(config_options['tmp'] + '/sam')
    if not os.path.isdir(config_options['tmp'] + '/jct'): os.mkdir(config_options['tmp'] + '/jct')
    if not os.path.isdir(config_options['tmp'] + '/bed'): os.mkdir(config_options['tmp'] + '/bed')
    if not os.path.isdir(config_options['tmp'] + '/wig'): os.mkdir(config_options['tmp'] + '/wig')
    if not os.path.isdir(config_options['tmp'] + '/draw'): os.mkdir(config_options['tmp'] + '/draw')
    if not os.path.isdir(config_options['tmp'] + '/depth_plot'): os.mkdir(config_options['tmp'] + '/depth_plot')
    if not os.path.isdir(config_options['tmp'] + '/isoforms'): os.mkdir(config_options['tmp'] + '/isoforms')
    if not os.path.isdir(config_options['tmp'] + '/indiv_isoforms'): os.mkdir(config_options['tmp'] + '/indiv_isoforms')
    if not os.path.isdir(config_options['tmp'] + '/results'): os.mkdir(config_options['tmp'] + '/results')


def primer_coordinates(p3_output, strand, my_chr, tar, up, down, use_target=True):
    '''
    This function parses the .Primer3 file to find the primer coordinates on
    the genome.
    '''
    # get position information
    (left_primer_offset, left_primer_length), (right_primer_offset, right_primer_length) = map(int, p3_output['PRIMER_LEFT_0'].split(',')), map(int, p3_output['PRIMER_RIGHT_0'].split(','))
    if use_target:
        target_start, target_end = tar
    else:
        target_start, target_end = 0, 0  # dummy values
    upstream_start, upstream_end = up
    downstream_start, downstream_end = down
    # my_chr = utils.get_chr(tar)
    # get position of primers
    if strand == '+':
        tmp = upstream_start + left_primer_offset
        first = (tmp, tmp + left_primer_length)
        tmp = right_primer_offset - (upstream_end - upstream_start) - (target_end - target_start) + downstream_start
        # second = (tmp, tmp + right_primer_length)
        second = (tmp - right_primer_length + 1, tmp + 1)
    elif strand == '-':
        tmp = upstream_end - left_primer_offset - left_primer_length
        second = (tmp, tmp + left_primer_length)
        tmp = right_primer_offset - (upstream_end - upstream_start) - (target_end - target_start)
        tmp = downstream_end - tmp - 1  # - right_primer_length
        first = (tmp, tmp + right_primer_length)
    tmp_first, tmp_second = first, second
    first, second = sorted([first, second], key=lambda x: (x[0], x[1]))  # make sure primer coordinates are sorted by position
    return utils.construct_coordinate(my_chr, first[0], first[1]) + ';' + utils.construct_coordinate(my_chr, second[0], second[1])


def primer3(options, primer3_options):
    """
    The primer.py main function uses the gtf module to find information about constitutive flanking exons for the target exons of interest.
    It then designs primers by calling primer3. Next it parses the primer3 output and outputs the final results to a file. The output file
    is then emailed to the designated address in the command line parameters.
    """

    # tmp directory
    mkdir_tmp()  # make any necessary tmp directories

    # find flanking exons
    logging.debug('Calling splice_graph.main to find flanking exons')
    flanking_info = splice_graph.main(options)
    logging.debug('Finished splice_graph.main')

    # iterate over all target sequences
    STRAND, EXON_TARGET, PSI_TARGET, UPSTREAM_TARGET, PSI_UPSTREAM, DOWNSTREAM_TARGET, PSI_DOWNSTREAM, ALL_PATHS, UPSTREAM_Seq, TARGET_SEQ, DOWNSTREAM_SEQ, GENE_NAME = range(12)
    output_list = []
    for z in range(len(flanking_info)):
        jobs_ID = str(z+1)  # base file name for primer3 output
        # no flanking exon information case
        if len(flanking_info[z]) == 1:
            logging.debug(flanking_info[z][0])
            output_list.append(flanking_info[z])  # write problem msg
        # has flanking exon information case
        else:
            genome_chr = options['fasta'][flanking_info[z][ALL_PATHS].chr]
            tar = options['target'][z][1][0]  # flanking_info[z][1]  # target interval (used for print statements)
            tar_id = options['target'][z][0]
            ####################### Primer3 Parameter Configuration###########
            P3_FILE_FLAG = '1'
            PRIMER_EXPLAIN_FLAG = '1'
            PRIMER_THERMODYNAMIC_PARAMETERS_PATH = os.path.join(config_options['primer3'],
                                                                'src/primer3_config/')
            SEQUENCE_ID = tar  # use the 'chr:start-stop' format for the sequence ID in primer3
            #SEQUENCE_TEMPLATE = flanking_info[z][UPSTREAM_Seq] + flanking_info[z][TARGET_SEQ].lower() + flanking_info[z][DOWNSTREAM_SEQ]
            #SEQUENCE_TARGET = str(len(flanking_info[z][UPSTREAM_Seq]) + 1) + ',' + str(len(flanking_info[z][TARGET_SEQ]))
            # SEQUENCE_PRIMER_PAIR_OK_REGION_LIST = '0,' + str(len(flanking_info[z][UPSTREAM_Seq])) + ',' + str(len(flanking_info[z][UPSTREAM_Seq]) + len(flanking_info[z][TARGET_SEQ])) + ',' + str(len(flanking_info[z][DOWNSTREAM_SEQ]))
            if options['short_isoform']:
                # this option uses the shortest available isoform for designing primers
                shortest_isoform = flanking_info[z][ALL_PATHS].get_shortest_path()
                middle_sequence = utils.get_seq_from_list(genome_chr,
                                                          flanking_info[z][STRAND],
                                                          shortest_isoform[1:-1])
                SEQUENCE_TEMPLATE = '%s%s%s' % (str(flanking_info[z][UPSTREAM_Seq]).upper(),
                                                middle_sequence,
                                                str(flanking_info[z][DOWNSTREAM_SEQ]).upper())
                SEQUENCE_PRIMER_PAIR_OK_REGION_LIST = '0,%d,%d,%d' % (len(flanking_info[z][UPSTREAM_Seq]),
                                                                      len(flanking_info[z][UPSTREAM_Seq]) + len(middle_sequence),
                                                                      len(flanking_info[z][DOWNSTREAM_SEQ]))
                middle_pos = (0, len(middle_sequence))
            else:
                # this uses upstream flanking exon, target exon, and downstream flanking exon to design primers
                SEQUENCE_TEMPLATE = '%s%s%s' % (str(flanking_info[z][UPSTREAM_Seq]).upper(),
                                                str(flanking_info[z][TARGET_SEQ]).lower(),
                                                str(flanking_info[z][DOWNSTREAM_SEQ]).upper())
                SEQUENCE_PRIMER_PAIR_OK_REGION_LIST = '0,%d,%d,%d' % (len(flanking_info[z][UPSTREAM_Seq]),
                                                                      len(flanking_info[z][UPSTREAM_Seq]) + len(flanking_info[z][TARGET_SEQ]),
                                                                      len(flanking_info[z][DOWNSTREAM_SEQ]))
                middle_pos = utils.get_pos(flanking_info[z][EXON_TARGET])
            #############################################################

            ####################### Write jobs_ID.conf##################
            with open(os.path.join(config_options['tmp'], jobs_ID + '.conf'), 'w') as outfile:
                # hard coded options
                outfile.write('SEQUENCE_ID=' + SEQUENCE_ID + '\n')
                outfile.write('SEQUENCE_TEMPLATE=' + SEQUENCE_TEMPLATE + '\n')
                #outfile.write('SEQUENCE_TARGET=' + SEQUENCE_TARGET + '\n')
                outfile.write('SEQUENCE_PRIMER_PAIR_OK_REGION_LIST=' + SEQUENCE_PRIMER_PAIR_OK_REGION_LIST + '\n')
                outfile.write('P3_FILE_FLAG=' + P3_FILE_FLAG + '\n')
                outfile.write('PRIMER_EXPLAIN_FLAG=' + PRIMER_EXPLAIN_FLAG + '\n')
                outfile.write('PRIMER_THERMODYNAMIC_PARAMETERS_PATH=' + PRIMER_THERMODYNAMIC_PARAMETERS_PATH + '\n')  # make sure primer3 finds the config files

                # options from primer3.cfg
                for o in primer3_options:
                    outfile.write(o)
                outfile.write('=' + '\n')  # primer3 likes a '=' at the end of sequence params
                logging.debug('Wrote the input file (%s) for primer3' % (config_options['tmp'] + '/' + jobs_ID + '.conf'))

            ###################### Primer3 #####################################
            if os.path.exists(config_options['tmp'] + jobs_ID + '.Primer3'):
                os.remove(config_options['tmp'] + jobs_ID + '.Primer3')  # delete old files

            call_primer3(tar, jobs_ID)  # command line call to Primer3!
            shutil.copy(os.path.join(config_options['tmp'], jobs_ID + '.Primer3'),
                        config_options['primer3_log'])  # copy primer3 results
            shutil.copy(os.path.join(config_options['tmp'], jobs_ID + '.conf'),
                        config_options['primer3_log'])  # copy config file

            #################### Parse '.Primer3' ################################
            primer3_dict = read_primer3(config_options['tmp'] + '/' + jobs_ID + '.Primer3')

            # checks if no output
            if(primer3_dict.keys().count('PRIMER_LEFT_0_SEQUENCE') == 0):
                str_params = (tar, os.path.abspath(os.path.join(config_options['primer3_log'], str(jobs_ID) + '.Primer3')))
                primer3_problem = 'No Primer3 results for %s. Check %s for more details.' % str_params
                logging.debug(primer3_problem)
                output_list.append([primer3_problem])
                continue
            # there is output case
            else:
                logging.debug('There are primer3 results for %s' % SEQUENCE_ID)
                # get info about product sizes
                target_exon_len = len(flanking_info[z][TARGET_SEQ])
                Primer3_PRIMER_PRODUCT_SIZE = int(primer3_dict['PRIMER_PAIR_0_PRODUCT_SIZE']) - target_exon_len
                primer3_coords = primer_coordinates(primer3_dict, flanking_info[z][STRAND], flanking_info[z][ALL_PATHS].chr,
                                                    # utils.get_pos(flanking_info[z][EXON_TARGET]),
                                                    # (0, len(middle_sequence)),
                                                    middle_pos,  # either the target exon or a dummy pos for using shortest isoform
                                                    utils.get_pos(flanking_info[z][UPSTREAM_TARGET]),
                                                    utils.get_pos(flanking_info[z][DOWNSTREAM_TARGET]),
                                                    use_target=True)
                flanking_info[z][ALL_PATHS].set_all_path_lengths(map(utils.get_pos, primer3_coords.split(';')))
                skipping_size_list = flanking_info[z][ALL_PATHS].skip_lengths
                inclusion_size_list = flanking_info[z][ALL_PATHS].inc_lengths
                skipping_size = ';'.join(map(str, filter(lambda x: x>0, skipping_size_list)))
                inclusion_size = ';'.join(map(str, filter(lambda x: x>0, inclusion_size_list)))
                # left_seq = Sequence(primer3_dict['PRIMER_LEFT_0_SEQUENCE'], 'left')
                # right_seq = Sequence(primer3_dict['PRIMER_RIGHT_0_SEQUENCE'], 'right')
                # forward_seq, reverse_seq = (-right_seq, -left_seq) if str(flanking_info[z][STRAND]) == '-' else (left_seq, right_seq)   # reverse complement sequence
                my_strand = flanking_info[z][STRAND]
                forward_pos, reverse_pos = map(utils.get_pos, primer3_coords.split(';')) if flanking_info[z][STRAND] == '+' else map(utils.get_pos, reversed(primer3_coords.split(';')))
                forward_seq = genome_chr[forward_pos[0]:forward_pos[1]] if my_strand == '+' else -genome_chr[forward_pos[0]:forward_pos[1]]
                reverse_seq = -genome_chr[reverse_pos[0]:reverse_pos[1]] if my_strand == '+' else genome_chr[reverse_pos[0]:reverse_pos[1]]
                asm_region = '%s:%d-%d' % (flanking_info[z][ALL_PATHS].chr,
                                           flanking_info[z][ALL_PATHS].asm_component[0][0],
                                           flanking_info[z][ALL_PATHS].asm_component[-1][1])

                # append results to output_list
                tmp = [tar_id, tar, primer3_coords, flanking_info[z][PSI_TARGET], str(forward_seq).upper(), str(reverse_seq).upper(),
                       str((float(primer3_dict['PRIMER_LEFT_0_TM']) + float(primer3_dict['PRIMER_RIGHT_0_TM'])) / 2), skipping_size, inclusion_size,
                       flanking_info[z][UPSTREAM_TARGET], flanking_info[z][PSI_UPSTREAM], flanking_info[z][DOWNSTREAM_TARGET],
                       flanking_info[z][PSI_DOWNSTREAM], asm_region, flanking_info[z][GENE_NAME]]
                output_list.append(tmp)

    # write output information
    with open(options['user_output'], 'wb') as outputfile_tab, open(options['output'], 'wb') as tmp_output:
        # define csv header
        header = ['ID', 'target coordinate', 'primer coordinates', 'PSI target', 'forward primer', 'reverse primer', 'average TM',
                  'skipping product size', 'inclusion product size', 'upstream exon coordinate', 'PSI upstream',
                  'downstream exon coordinate', 'PSI downstream', 'ASM Region', 'Gene']
        output_list = [header] + output_list  # pre-pend header to output file
        csv.writer(outputfile_tab, dialect='excel', delimiter='\t').writerows(output_list)  # output primer design to a tab delimited file
        csv.writer(tmp_output, dialect='excel', delimiter='\t').writerows(output_list)  # output primer design to a tmp file location


def main(options):
    """
    Reads in primer3 options, starts logging, and then calls the :func:`primer3`
    function to run primer3.

    :param dict options: parameters for running PrimerSeq
    """

    ##### Getting Start Time ######
    logging.debug('Start the program with [%s]', ' '.join(sys.argv))
    startTime = time.time()

    # read in primer3 options
    logging.debug('Reading in primer3 config file . . .')
    primer3_options = []
    with open(config_options['primer3_cfg']) as handle:
        for line in handle:
            # skip comment lines and lines with no set values
            if not line.startswith('#') and len(line.strip().split("=")[1]) > 0:
                primer3_options.append(line)
    logging.debug('Finished reading primer3 config file.')

    # the primer3 function runs the primer3_core executable
    try:
        primer3(options, primer3_options)
    except:
        t, v, trace = sys.exc_info()
        logging.debug('ERROR! For more information read the following lines')
        logging.debug('Type: ' + str(t))
        logging.debug('Value: ' + str(v))
        logging.debug('Traceback:\n' + traceback.format_exc())
        raise

    # delete temporary sam files (may eventually delete more tmp files)
    logging.debug('Deleting tmp files')
    delete_tmp_files(options)

    ### record end of running primer3 ###
    logging.debug("Program ended")
    currentTime = time.time()
    runningTime = currentTime - startTime  # in seconds
    logging.debug("Program ran for %.2d:%.2d:%.2d" % (runningTime / 3600, (runningTime % 3600) / 60, runningTime % 60))


def delete_tmp_files(opts):
    """
    Delete Primer3 files that clutter the tmp directory. Users must select the
    keep temporary option in the GUI to prevent deletion of the LARGE SAM files.

    :param dict opts: parameters for running PrimerSeq
    """
    # delete SAM files
    if not opts['keep_temp']:
        for f in glob.glob(os.path.join(config_options['tmp'], 'sam/*.sam')):
            os.remove(f)

    # delete all .for files from primer3
    for f in glob.glob(os.path.join(config_options['tmp'], '*.for')):
        os.remove(f)

    # delete all .rev files from primer3
    for f in glob.glob(os.path.join(config_options['tmp'], '*.rev')):
        os.remove(f)

    # remove primer3 files
    for f in glob.glob(os.path.join(config_options['tmp'], '*.Primer3')):
        os.remove(f)

    # delete '.conf' input files for primer3
    for f in glob.glob(os.path.join(config_options['tmp'], '*.conf')):
        os.remove(f)


class ValidateRnaseq(argparse.Action):
    """
    Makes sure the -r parameter input is a SAM/BAM file
    """
    def __call__(self, parser, namespace, values, option_string=None):
        # if error print help and exit
        if not values.endswith('.sam') and not values.endswith('.bam'):
            parser.print_help()
            parser.exit(status=1,
                message='\n' + '#' * 40 + '\nThe -r parameter expects a SAM or BAM file' + '#' * 40 + '\n')
        # set value if no error,
        # simply assign the string as is
        setattr(namespace, self.dest, values)  # set the value


class ValidateCutoff(argparse.Action):
    """
    Make sure PSI cutoff is between 0 and 1 since it is a percentage
    """
    def __call__(self, parser, namespace, values, option_string=None):
        # if error print help and exit
        if 0 <= values <= 1:
            setattr(namespace, self.dest, values)  # set the value
        else:
            parser.print_help()
            parser.exit(status=1,
                        message='\n' + '#' * 40 +
                        '\nInclusion levels can only be between 0 and 1\n' +
                        '#' * 40 + '\n')


if __name__ == '__main__':
    # command line arguments
    parser = argparse.ArgumentParser(description='Command line interface for designing primers')
    group_one = parser.add_mutually_exclusive_group(required=True)
    group_one.add_argument('-b', dest='big_bed', action='store', help='big bed file that defines the possible exons in a gene')
    group_one.add_argument('-g', dest='gtf', action='store', help='gtf file that defines the possible exons in a gene')
    parser.add_argument('--no-gene-id', dest='no_gene_id', action='store_true', help='Use this flag if your gtf does not have a valid gene_id')
    parser.add_argument('-f', required=True, dest='fasta', action='store', help='path to fasta file')
    parser.add_argument('-r', required=True, dest='rnaseq', action=ValidateRnaseq, help='path to SAM/BAM file(s) ("," delimited)')
    parser.add_argument('-t', required=True, dest='target', action='store', help='path to txt file with <strand><chr>:<start>-<end> for each target on separate lines.')
    group_two = parser.add_mutually_exclusive_group(required=True)
    group_two.add_argument('--annotaton', dest='annotation_flag', action='store_true', help='only use junctions supported from annotation')
    group_two.add_argument('--rnaseq', dest='rnaseq_flag', action='store_true', help='only use junctions supported from RNA-Seq')
    group_two.add_argument('--both', dest='both_flag', action='store_true', help='use junctions from both RNA-Seq and annotation')
    parser.add_argument('--psi', dest='psi', action=ValidateCutoff, default=1.0, type=float, help='Define inclusion level sufficient to define constitutive exon. Valid: 0<psi<1.')
    parser.add_argument('--read-threshold', dest='read_threshold', default=5, action='store', type=int, help='Define the minimum number of read support necessary to call a junction from RNA-Seq')
    parser.add_argument('--keep-temp', dest='keep_temp', action='store_true', help='Keep temporary files in your tmp directory')
    parser.add_argument('-m', '--min-jct-count', dest='min_jct_count', action='store', type=int, default=1, help='Assign junctions that are known from annotation at least MIN_JCT_COUNT number of reads')
    parser.add_argument('-a', '--anchor-length', dest='anchor_length', action='store', type=int, default=8, help='Set the minimum number of bases a junction read must span on both sides of the junction')
    parser.add_argument('-o', required=True, dest='output', action='store', help='Output directory')
    options = vars(parser.parse_args())  # make it a dictionary

    # define job_id by the name of the target file
    tmp = options['target'].split('/\\')[-1].split('.')
    options['job_id'] = ('.'.join(tmp[:-1]) if len(tmp) > 1 else tmp[0]) + '.output'
    with open(options['target']) as handle:
        options['target'] = map(lambda x: x.strip().split('\t'), handle.readlines())

    # define logging file before using logging.debug
    if not os.path.exists(config_options['log']): os.mkdir(config_options['log'])  # make directory to put log files
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(message)s',
                        filename=config_options['log'] + '/log.primer.' + str(datetime.datetime.now()),
                        filemode='w')

    ### Start loading the user's files ###
    # gtf file must be pre-loaded since there is no random access
    if options['gtf']:
        print 'Loading GTF . . .'
        print 'May take ~1 min.'
        options['gtf'] = gene_annotation_reader(options['gtf'])

    print 'Loading fasta . . .'
    options['fasta'] = SequenceFileDB(options['fasta'])  # get fasta object using pygr right away

    # the sam object interfaces with the user specified BAM/SAM file!!!
    print 'Loading Bam Files . . .'
    options['rnaseq'] = [sam.Sam(data, options['anchor_length']) for data in options['rnaseq'].split(',')]
    print 'Done loading all files.'
    ### END loading files ###

    # call main function
    main(options)
