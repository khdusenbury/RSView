"""Argument parser for `rsview`"""

import sys
import argparse

from argparse import RawTextHelpFormatter

import rsview

class ArgumentParserNoArgHelp(argparse.ArgumentParser):
    """Like *argparse.ArgumentParser*, but prints help when no arguments."""
    def error(self, message):
        """Prints error message, then help."""
        sys.stderr.write('error: {0}\n\n'.format(message))
        self.print_help()
        sys.exit(2)


def map_parser():
    """Returns argument parser for `map_rsv.py`"""
    parser = argparse.ArgumentParser(description="Plot global distribution "\
                                     "of RSV")
    parser.add_argument('level', type=str, choices=['subtype', 'genotype'],
                        help="Specify whether the subtype or genotype of RSV sequences "\
                        "should be plotted")
    parser.add_argument('datadir', type=str,
                        help="Specify the directory that contains seq_download.py output")
    parser.add_argument('--genotype-level', type=str, choices=['collapse', 'all'],
                        default='collapse', help="Specify whether to plot all genotypes of "\
                        "RSV or collapse them into major clades")
    parser.add_argument('--years', default=[1990, 2018],
                        help="Specify a range of years to plot. Example: [1990, 2018]. If 'all'"\
                        "is specified, all years for which there are data points will be plotted")
    return parser

def seq_parser():
    """Returns argument parser for `seq_download.py`."""
    parser = ArgumentParserNoArgHelp(
        description='Downloads RSV G protein sequences & metadata from '\
            'Genbank. This program is part of {0} (version {1}) written by '\
            '{2}.'.format(rsview.__name__, rsview.__version__,
                          rsview.__author__) + 'For documentation, see {0}'.format(
                rsview.__url__),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--email', required=True, type=str, help='User email'\
            ' for GenBank download.')
    parser.add_argument('--query', required=True, type=str, help='Search '\
            'term(s) for downloading sequences from GenBank.')
    parser.add_argument('--outdir', required=True, type=str, help='Directory'\
            'for downloaded data.')
    parser.add_argument('--outprefix', default='RSVG_gb_metadata', type=str,
            help='Beginning of file name for output `.csv`. Suffix will '\
            'specify number of sequences downloaded.')
    parser.add_argument('--db', default='nuccore', type=str, help='Entrez'\
            ' database to search.')
    parser.add_argument('--firstseq', default=0, type=int, help='Index of '\
            'first sequence to download.')
    parser.add_argument('--filesize', default=5000, type=int, help='Number of '\
            'seqs to download into one file. Default of 5000 balances '\
            'download time and minimizing the number of separate files.')
    parser.add_argument('--maxseqs', default=20000, type=int, help='Maximum '\
            'number of sequence hits to search for and download across all '\
            'output files.')
    parser.add_argument('--batchsize', default=100, type=int, help='Number '\
            'seqs to download in one retrieval. If much larger than 100, '\
            'download will be quite slow.')
    parser.add_argument('--filetype', default='gb', type=str, help='File '\
            'type of sequences downloaded from GenBank.')
    parser.add_argument('--outmode', default='xml', type=str, help='File '\
            'type for results of GenBank query.')

    return parser

def genotype_parser():
    """Returns argparser for genotype.py"""
    parser = ArgumentParserNoArgHelp(
        description='Given RSV G protein sequences & metadata downloaded '\
            'from Genbank, fill in missing genotype data. This program is part '\
            ' of {0} (version {1}) written by {2}.'.format(rsview.__name__,
            rsview.__version__, rsview.__author__) + 'For documentation, see '
            '{0}'.format(rsview.__url__),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--inprefix', required=True, type=str, help="Prefix "\
            "pointing to downloaded sequences and metadata files. --inprefix"\
            " name should be truncated where differences begin between files"\
            " that will be combined into one dataframe. Example: "\
            "'./data/RSVG_gb_metadata'. ")
    parser.add_argument('--seqsdir', required=True, type=str, help="Directory"\
            " for outputting generated fasta and alignment files.")
    parser.add_argument('--outdir', required=True, type=str, help="Directory "\
            "for outputting cleaned, genotyped `.csv`.")
    parser.add_argument('--threshold', type=int, default=150,
            help="Threshold for how many sites must match in order to call a"\
            " genotype.")
    parser.add_argument('--full_length', type=int, default=290, help="Min "\
            "length for a sequence to be considered full length.")
    return parser

def plot_parser(allowed_data=""):
    """Returns argparser for plot_rsv.py"""
    parser = argparse.ArgumentParser(description="Plot data on child death "\
            "rates from acute respiratory infection",
                                     formatter_class=RawTextHelpFormatter)
    parser.add_argument(
        'level', type=str, choices=['all', 'country'], default='all',
        help="Specify whether to plot data for all countries or for a "\
            "specific country")
    parser.add_argument(
        'data_type', type=str, choices=['nnd', 'pnd', 'neo9',
                                        'post9', 'ufive9', 'rneo9', 'rpost9', 'rufive9',
                                        'fneo9', 'fpost9', 'fufive9'],
        help="Specify which category of "\
            "data to plot:\n" + allowed_data)
    parser.add_argument('datadir', type=str,
                        help="Specify the directory that contains"
                        + " health data and seq_download.py output")
    parser.add_argument(
        '--country', type=str, default='Global',
        help="Specify the country for which to plot data",
        #required='level' in sys.argv and sys.args.level == "country"
        )
    parser.add_argument(
        '--highlight_country', type=str, default=None,
        help="Specify the country for to highlight")
    return parser



def correlation_parser(allowed_data=""):
    """Returns argparser for plot_correlation.py"""
    parser = argparse.ArgumentParser(description="Plot data on child death "\
        "rates from acute respiratory infection",
                                     formatter_class=RawTextHelpFormatter)
    parser.add_argument(
        'level', type=str, choices=['all', 'year'], default='all',
        help="Specify whether to plot data for all countries or for a "\
        "specific country")
    parser.add_argument(
        'data_type', type=str, choices=['nnd', 'pnd', 'neo9',
                                        'post9', 'ufive9', 'rneo9', 'rpost9', 'rufive9',
                                        'fneo9', 'fpost9', 'fufive9'],
        help="Specify which category of "\
        "data to plot:\n" + allowed_data)
    parser.add_argument('datadir',
                        type=str,
                        help="Specify the directory that contains"
                        + " health data and seq_download.py output")
    return parser



def health_parser():
    """Returns argparser for health_download.py"""
    parser = argparse.ArgumentParser(description="Plot data on child death "\
        "rates from acute respiratory infection",
                                     formatter_class=RawTextHelpFormatter)
    parser.add_argument('datadir', type=str,
                        help="Specify the directory that contains health data")
    return parser
