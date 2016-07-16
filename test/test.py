#!/usr/bin/python

import os, sys, signal
from subprocess import Popen, PIPE, check_call, check_output
import unittest

# print test usage
def test_usage():
    print 'Test Usage:'
    print './test.py <congestion-control-name>'
    sys.exit(1)

class TestCongestionControl(unittest.TestCase):
    # run parameterized test cases
    def __init__(self, test_name, cc_option):
        super(TestCongestionControl, self).__init__(test_name)
        self.cc_option = cc_option

    def timeout_handler(signum, frame):
        raise

    def run_congestion_control(self, first_to_run):
        second_to_run = 'sender'
        if first_to_run == 'sender':
            second_to_run = 'receiver'

        # run the side specified by first_to_run
        cmd = 'python %s %s' % (self.src_file, first_to_run)
        sys.stderr.write(cmd + '\n')
        sys.stderr.write('Running %s %s...\n' % (self.cc_option, first_to_run))
        proc1 = Popen(cmd, stdout=DEVNULL, stderr=PIPE, shell=True)

        # find port printed
        port_info = proc1.stderr.readline()
        port = port_info.rstrip().rsplit(' ', 1)[-1]

        # run the other side specified by second_to_run
        cmd = "'python %s %s %s %s'" % (self.src_file, second_to_run,
                                        self.ip, port)
        mm_cmd = 'mm-link %s %s --once --uplink-log=%s --downlink-log=%s' \
                 ' -- sh -c %s' % (self.uplink_trace, self.downlink_trace,
                 self.uplink_log, self.downlink_log, cmd)
        sys.stderr.write(mm_cmd + '\n')
        sys.stderr.write('Running %s %s...\n' % (self.cc_option, second_to_run))
        proc2 = Popen(mm_cmd, stdout=DEVNULL, stderr=PIPE, shell=True)

        # running for 60 seconds
        signal.signal(signal.SIGALRM, self.timeout_handler)
        signal.alarm(60)

        try:
            proc2_err = proc2.communicate()[1]
        except:
            sys.stderr.write('Done\n')
        else:
            if proc2.returncode != 0:
                sys.stderr.write(proc2_err)
            else:
                sys.stderr.write('Running is shorter than 60s\n')
            sys.exit(1)

        proc2.kill()
        proc1.kill()

    # congestion control test
    def test_congestion_control(self):
        cc_option = self.cc_option
        test_dir = os.path.abspath(os.path.dirname(__file__))
        src_dir = os.path.abspath(os.path.join(test_dir, '../src'))
        self.src_file = os.path.join(src_dir, cc_option + '.py')

        # get build dependencies
        deps_needed = check_output(['python', self.src_file, 'deps'])
        sys.stderr.write('Installing dependencies: ' + deps_needed + '\n')
        check_call('sudo apt-get -yq --force-yes install ' + deps_needed, shell=True)

        # run build
        build_cmd = 'python %s build' % self.src_file
        sys.stderr.write(build_cmd + '\n')
        sys.stderr.write('Building...\n')
        check_call(build_cmd, shell=True)
        sys.stderr.write('Done\n')

        # run setup
        setup_cmd = 'python %s setup' % self.src_file
        sys.stderr.write(setup_cmd + '\n')
        sys.stderr.write('Setting up...\n')
        setup_proc = Popen(setup_cmd, stdout=DEVNULL, stderr=PIPE, shell=True)
        setup_info = setup_proc.communicate()[1]
        if setup_proc.returncode != 0:
            sys.stderr.write(setup_info)
            sys.exit(1)

        setup_info = setup_info.rstrip().rsplit('\n', 1)[-1]
        first_to_run = setup_info.split(' ')[0].lower()
        if first_to_run != 'receiver' and first_to_run != 'sender':
            sys.stderr.write('Need to specify receiver or sender first\n')
            sys.exit(1)
        sys.stderr.write('Done\n')

        # prepare mahimahi
        traces_dir = '/usr/share/mahimahi/traces/'
        self.datalink_log = '%s/%s_datalink.log' % (test_dir, cc_option)
        self.acklink_log = '%s/%s_acklink.log' % (test_dir, cc_option)

        if first_to_run == 'receiver':
            self.uplink_trace = traces_dir + 'Verizon-LTE-driving.up'
            self.downlink_trace = traces_dir + 'Verizon-LTE-driving.down'
            self.uplink_log = self.datalink_log
            self.downlink_log = self.acklink_log
        else:
            self.uplink_trace = traces_dir + 'Verizon-LTE-driving.down'
            self.downlink_trace = traces_dir + 'Verizon-LTE-driving.up'
            self.uplink_log = self.acklink_log
            self.downlink_log = self.datalink_log

        self.ip = '$MAHIMAHI_BASE'

        # run receiver and sender depending on the run order
        self.run_congestion_control(first_to_run)

        # generate throughput graphs
        sys.stderr.write('* Data link statistics:\n')
        datalink_throughput = open('%s/%s_datalink_throughput.html' \
                                   % (test_dir, cc_option), 'wb')
        proc = Popen(['mm-throughput-graph', '500', self.datalink_log],
                     stdout=datalink_throughput, stderr=PIPE)
        datalink_results = proc.communicate()[1]
        sys.stderr.write(datalink_results)
        datalink_throughput.close()

        sys.stderr.write('* ACK link statistics:\n')
        acklink_throughput = open('%s/%s_acklink_throughput.html' \
                                  % (test_dir, cc_option), 'wb')
        proc = Popen(['mm-throughput-graph', '500', self.acklink_log],
                     stdout=acklink_throughput, stderr=PIPE)
        acklink_results = proc.communicate()[1]
        sys.stderr.write(acklink_results)
        acklink_throughput.close()

def main():
    if len(sys.argv) != 2:
        test_usage()
    cc_option = sys.argv[1]

    # Enable IP forwarding
    cmd = ['sudo', 'sysctl', '-w', 'net.ipv4.ip_forward=1']
    check_call(cmd, stdout=DEVNULL, stderr=DEVNULL)

    # create test suite to run
    suite = unittest.TestSuite()
    suite.addTest(TestCongestionControl('test_congestion_control', cc_option))
    if not unittest.TextTestRunner().run(suite).wasSuccessful():
        sys.exit(1)

if __name__ == '__main__':
    DEVNULL = open(os.devnull, 'wb')
    main()
    DEVNULL.close()
