#!/usr/bin/python

import os, sys
from subprocess import check_output, check_call
import usage

def main():
    usage.check_args(sys.argv, os.path.basename(__file__), usage.SEND_FIRST)
    option = sys.argv[1]
    src_dir = os.path.abspath(os.path.dirname(__file__))
    submodule_dir = os.path.abspath(os.path.join(src_dir,
                                    '../third_party/verus'))
    find_unused_port_file = os.path.join(src_dir, 'find_unused_port')
    send_file = os.path.join(submodule_dir, 'src/verus_server')
    recv_file = os.path.join(submodule_dir, 'src/verus_client')
    DEVNULL = open(os.devnull, 'wb')

    # build dependencies
    if option == 'deps':
        print 'libtbb-dev libasio-dev libalglib-dev libboost-system-dev'

    # build
    if option == 'build':
        cmd = 'cd %s && autoreconf -i && ./configure && make -j' % submodule_dir
        check_call(cmd, shell=True)

    # setup
    if option == 'setup':
        sys.stderr.write('Sender first\n')

    # sender
    if option == 'sender':
        port = check_output([find_unused_port_file])
        sys.stderr.write('Listening on port: %s\n' % port)
        cmd = [send_file, '-name', 'verus_tmp', '-p', port, '-t', '75']
        check_call(cmd, stdout=DEVNULL, stderr=DEVNULL)

    # receiver
    if option == 'receiver':
        ip = sys.argv[2]
        port = sys.argv[3]
        cmd = [recv_file, ip, '-p', port]
        check_call(cmd, stdout=DEVNULL, stderr=DEVNULL)

    DEVNULL.close()

if __name__ == '__main__':
    main()
