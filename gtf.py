import csv
import re
import argparse


class Gtf(object):
    """
    Separates out gtf parsing from iterating over records. Perhaps a flimsy
    use of a class.
    """
    def __init__(self, gtf_line):
        self.gtf_list = gtf_line
        self.seqname, self.source, self.feature, self.start, self.end, self.score, self.strand, self.frame, self.attribute = gtf_line  # These indexes are defined by the GTF spec
        self.attribute = dict(
            map(lambda x: re.split('\s+', x.replace('"', '')),
                re.split('\s*;\s*', self.attribute.strip().strip(';'))))  # convert attrs to dict

        self.start, self.end = int(self.start) - 1, int(self.end)

    def __str__(self):
        return '\t'.join(self.gtf_list) + '\n'


def gtf_reader(fileObject, delim):
    """
    Iterate over a file to extract 'exon' features of tx
    """
    for gtf_line in csv.reader(fileObject, delimiter=delim):
        gtf = Gtf(gtf_line)

        # only use exon features
        if gtf.feature.lower() == 'exon':
            yield Gtf(gtf_line)


def sort_gtf(file_name, output):
    gtf_list = []
    with open(file_name) as handle:
        for gtf_line in csv.reader(handle, delimiter='\t'):
            gtf = Gtf(gtf_line)
            gtf_list.append(gtf)
    gtf_list.sort(key=lambda x: (x.seqname, x.attribute['gene_id'], x.attribute['transcript_id'], x.start, x.end))

    # write the contents back to a file
    with open(output, 'wb') as write_handle:
        for gtf_obj in gtf_list:
            write_handle.write(str(gtf_obj))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='The command line interface for this python file is meant to properly sort a gtf file')
    parser.add_argument('-g', required=True, dest='gtf', action='store', help='path to gtf file')
    parser.add_argument('-o', required=True, dest='output', action='store', help='properly sorted gtf output')
    args = parser.parse_args()

    sort_gtf(args.gtf, args.output)  # do the work of sorting
