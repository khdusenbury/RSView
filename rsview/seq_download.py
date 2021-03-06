"""Download sequences and metadata from GenBank"""

import time
import re
import os
import math
import pandas as pd
from Bio import Entrez
import rsview.parsearguments


# Initialize lists for genotype assignment
GTA_LIST = [r'\bGA\s?[0-9]*\b', r'\bNA\s?[0-9]*\b', r'\bSAA\s?[0-9]*\b',
		    r'\bON\s?[0-9]*\b']

GTB_LIST = [r'\bGB\s?[0-9]*\b', r'\bSAB\s?[0-9]*\b', r'\bURU\s?[0-9]*\b',
		    r'\bBA\s?[0-9]*\b', r'\bBA\s?IV\b', r'\bTHB\b']


def getids(database, retmax, term):
    """Retrieve genbank sequence IDs matching query term.

    Args:
        `database` (str)
            string specifying genbank database to search
        `retmax` (int)
            maximum number of sequence IDs to return
        `term` (str)
            query term

    Returns:
        `search_IDs` (list)
            list of sequence IDs returned from the search
    """
    search_handle = Entrez.esearch(db=database, retmax=retmax, term=term)
    search_record = Entrez.read(search_handle)
    search_handle.close()
    search_ids = search_record['IdList']
    return search_ids

def gethandle(database, ids, firstseq, dload_size, rettype, retmode):
    """Download Entrez 'handle' for downloading seqs of interest
       
    See `Entrez.efetch` help for additional help.

    Args:
        `database` (str)
            Genbank database containing sequences of interest
        `ids` (list)
            sequence IDs returned from `getIDs` or other Entrez search
        `firstseq` (int)
            index of first sequence to download
        `dload_size` (int)
        	number of seqs to download at a time
        `rettype` (str)
        	type of file downloaded from GenBank. default: 'gb'
        `retmode` (str)
        	format of output from GenBank download. default: `xml`

    Returns:
        `handle`
            Entrez object containing sequence information
    """

    handle = Entrez.efetch(db=database, id=ids, retstart=firstseq,
    		retmax=dload_size, rettype=rettype, retmode=retmode)
    return handle

def find_subtype(meta_dict):
    """Find subtype from dictionary of sequence metadata.

    Args:
        `meta_dict` (dict)
        	dictionary of metadata downloaded from genbank

    Returns:
        `subtype` (str)
        	RSV subtype as one letter string, 'A' or 'B'.
    """

    subtype = ''
    if ' A' in meta_dict['organism']:
        subtype = 'A'
    elif ' B' in meta_dict['organism']:
        subtype = 'B'

    elif subtype == '':
        for val in meta_dict.values():
            if re.search(r'RSV\s?A\b', val) or \
                    re.search(r'type: A\b', val) or    \
                    re.search(r'group: A\b', val) or re.search(r'\bA\b', val):
                subtype = 'A'
            elif re.search(r'RSV\s?B\b', val) or \
                    re.search(r'type: B\b', val) or \
                    re.search(r'group: B\b', val) or re.search(r'\bB\b', val):
                subtype = 'B'

    return subtype


def find_genotype(meta_dict, genotypes_a, genotypes_b):
    """Script for extracting genotype data from genbank metadata.

    If the genotype is found, but the subtype is still empty, populate
    subtype data based on genotype.


    Args:
        `meta_dict` (dict)
            dictionary of metadata
        `genotypes_a` (list)
            list of possible genotypes for subtype A
        `genotypes_b` (list)
            list of possible genotypes for subtype B

    Returns:
        `typed_dict` (dict)
            dictionary of metadata with genotype (and missing subtype) data
            filled in.
    """
    typed_dict = meta_dict
    genotype = ''
    for value in meta_dict.values():
        if 'genotype:' in value:
            for gtype in genotypes_a:
                if re.search(gtype, value):
                    genotype = re.findall(gtype, value)[0]
                    if meta_dict['subtype'] == '':
                        typed_dict['subtype'] = 'A'

            for gtype in genotypes_b:
                if re.search(gtype, value):
                    genotype = re.findall(gtype, value)[0]
                    if meta_dict['subtype'] == '':
                        typed_dict['subtype'] = 'B'

    typed_dict['genotype'] = genotype

    return typed_dict


def makedf(handle):
    """
    Convert Genbank sequence data into dataframe containing necessary
    metadata.

    Args:
        `handle`
            Entrez object containing information downloaded from GenBank

    Returns:
        `seqinfo_df` (DataFrame)
            pandas DataFrame containing downloaded sequence and metadata
    """
    records = Entrez.parse(handle)
    seqinfo = []
    for record in records:
        sub_dict = {}
        features = record['GBSeq_feature-table']

        #Retrieve metadata
        strain_quals = features[0]['GBFeature_quals']
        for qual in strain_quals:
            qual_dict = dict(qual)
            if 'GBQualifier_value' in qual_dict.keys():
                sub_dict[qual_dict['GBQualifier_name']] = \
                        qual_dict['GBQualifier_value']

        #Retrieve G protein sequence
        for feat_dict in features[1:]:
            if 'GBFeature_quals' in feat_dict.keys():
                for feat_qual in feat_dict['GBFeature_quals']:
                    if 'GBQualifier_value' in feat_qual.keys():
                        if re.search(r'\bG\b', feat_qual['GBQualifier_value'])\
                                or re.search(r'\battachment.*protein\b',
                                             feat_qual['GBQualifier_value']):
                            g_quals = feat_dict['GBFeature_quals']
                            for g_qual in g_quals:
                                if g_qual['GBQualifier_name'] == 'translation':
                                    sub_dict['G_seq'] = g_qual['GBQualifier_value']

        sub_dict['subtype'] = find_subtype(sub_dict)

        sub_dict = find_genotype(sub_dict, GTA_LIST, GTB_LIST)

        seqinfo.append(sub_dict)

    handle.close()

    seqinfo_df = pd.DataFrame(seqinfo)

    return seqinfo_df


def main():
    """Download sequence data and return dataframe"""

    parser = rsview.parsearguments.seq_parser()
    args = vars(parser.parse_args())
    prog = parser.prog

    print("\nExecuting {0} ({1}) in {2} at {3}.\n".format(
        prog, rsview.__version__, os.getcwd(), time.asctime()))

    Entrez.email = args['email']
    query = args['query']
    begin = args['firstseq']
    filesize = args['filesize']
    maxseqs = args['maxseqs']
    database = args['db']
    filetype = args['filetype']
    outmode = args['outmode']

    if 0 < (filesize - begin) < 100:
        batchsize = filesize - begin
    else:
        batchsize = args['batchsize']

    assert maxseqs >= begin, "Search ends before index of `--firstseq`. "\
            "`--maxseqs` ({0}) must be greater than `--firstseq` ({1})."\
            .format(maxseqs, begin)

    if not os.path.isdir(args['outdir']):
        os.makedirs(args['outdir'])

    maxids = getids(database, maxseqs, query)
    num_all = len(maxids)
    if num_all < maxseqs:
        print('There are {0} IDs that match the query:\n\t{1}'.format(
        		num_all, query))
    elif num_all == maxseqs:
        print('There are at least {0} IDs that match the query:\n\t{1}\n'\
                '`--maxseqs` may be limiting number of IDs returned.'.format(
                num_all, query))

    firstseq = begin # keept track of first seq for print statements

    while begin < maxseqs:
        if (begin + filesize) <= maxseqs:
            end = begin + filesize
        else:
            end = maxseqs
        outfile = '{0}/{1}_{2}-{3}.csv'.format(args['outdir'],
        		args['outprefix'], begin, end)
        print('\nDownloading seq file number {0} of {1}.'.format(
                int(math.ceil((end-firstseq)/filesize)), 
                int(math.ceil((num_all-firstseq)/filesize))))
        print('Saving sequences and metadata to: {0}'.format(outfile))

        ids = getids(database, end, query)
        numseqs = len(ids)

        start = begin
        print('Downloading metadata for seqs: {0} to {1}'.format(start, numseqs))

        metadata_frames = []
        while start <= (numseqs - batchsize):
            handle = gethandle(database, ids, start, batchsize, filetype, outmode)
            metadata_df = makedf(handle)
            metadata_frames.append(metadata_df)
            start = start + batchsize
            if (start-begin) % 500 == 0:
                print('Processed {0} seqs'.format(start-begin))

        if start != numseqs: #Process final seqs
            handle = gethandle(database, ids, start, numseqs, filetype, outmode)
            metadata_df = makedf(handle)
            metadata_frames.append(metadata_df)

        full_df = pd.concat(metadata_frames, ignore_index=True, sort=False)
        assert len(full_df.index) == (numseqs-begin), 'Exported unexpected ' \
                'number of seqs. Expected: {0} Retrieved: {1}'.format(
                (numseqs-begin), len(full_df.index))
        full_df.to_csv(outfile)

        begin = end

if __name__ == '__main__':
    START_TIME = time.time()
    main()
    END_TIME = time.time()
    print('Program took {0:.3f} minutes to run.'.format((END_TIME - START_TIME)/60))
