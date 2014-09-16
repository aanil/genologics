#!/usr/bin/env python
DESC = """EPP script for updating #Reads and %Q30 for quality filtered reads.
The script reads the new values from a csv file "Quality Filter" that first 
need to be generated by the quality filter script XXX and uploaded to the process.

Reads from:
    --files--
    "Quality Filter"            "shared result file" uploaded by user.   

Writes to:
    --Lims fields--
    "% Bases >=Q30"             udf of process artifacts (result file)
    "#Reads"                    udf of process artifacts (result file)

Logging:
    The script outputs a regular log file with regular execution information.

Written by Maya Brandi 
"""

import os
import sys
import logging

from argparse import ArgumentParser
from genologics.lims import Lims
from genologics.config import BASEURI, USERNAME, PASSWORD
from genologics.entities import Process
from genologics.epp import EppLogger
from genologics.epp import set_field
from genologics.epp import ReadResultFiles

class QualityFilter():
    def __init__(self, process):
        self.process = process
        self.result_files = process.result_files()
        self.QF_from_file = {}
        self.missing_samps = []
        self.abstract = []
        self.nr_samps_updat = 0
        self.nr_samps_tot = '-'

    def get_and_set_yield_and_Q30(self):
        file_handler = ReadResultFiles(self.process)
        source_file = file_handler.shared_files['Quality Filter']
        target_files = dict((r.samples[0].name, r) for r in self.result_files)
        self.nr_samps_tot = str(len(target_files))
        self.QF_from_file = file_handler.format_file(source_file, 
                               name = 'Quality Filter', first_header = 'Sample')
        for samp_name, target_file in target_files.items():
            self._set_udfs(samp_name, target_file)
        self._logging()

    def _set_udfs(self, samp_name, target_file):
        if samp_name in self.QF_from_file.keys():
            s_inf = self.QF_from_file[samp_name]
            target_file.udf['# Reads'] = int(s_inf['# Reads'])
            target_file.udf['% Bases >=Q30'] = float(s_inf['% Bases >=Q30'])
            self.nr_samps_updat += 1
        else:
            self.missing_samps.append(samp_name)
        set_field(target_file)

    def _logging(self):
        self.abstract.append("Yield and Q30 uploaded for {0} out of {1} samples."
                              "".format(self.nr_samps_updat, self.nr_samps_tot))
        if self.missing_samps:
            self.abstract.append("The following samples are missing in Quality "
            "Filter file: {0}.".format(', '.join(self.missing_samps)))
        print >> sys.stderr, ' '.join(self.abstract)

def main(lims, pid, epp_logger):
    process = Process(lims,id = pid)
    QF = QualityFilter(process)
    QF.get_and_set_yield_and_Q30()
    

if __name__ == "__main__":
    parser = ArgumentParser(description=DESC)
    parser.add_argument('--pid', default = None , dest = 'pid',
                        help='Lims id for current Process')
    parser.add_argument('--log', dest = 'log',
                        help=('File name for standard log file, '
                              'for runtime information and problems.'))

    args = parser.parse_args()
    lims = Lims(BASEURI, USERNAME, PASSWORD)
    lims.check_version()

    with EppLogger(log_file=args.log, lims=lims, prepend=True) as epp_logger:
        main(lims, args.pid, epp_logger)
