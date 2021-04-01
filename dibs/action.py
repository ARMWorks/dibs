import os
import subprocess

from .util import sudo

def _run(*args, **kwargs):
    print(*args)
    result = subprocess.run(*args, **kwargs)
    if result.returncode != 0:
        raise subprocess.SubprocessError(repr(args[0]) + ' failed')
    return result

def run(config, step, *args):
    if step == 'mount':
        _run(['mkdir', '-p', args[2]])
        _run(['sudo', 'mount', '-o', 'loop,rw', '-t', args[0], args[1], args[2]])
    elif step == 'make-btrfs':
        size = config.get('btrfs-size', '1G')
        _run(['dd', 'if=/dev/null', 'of=%s' % (args[0],), 'bs=1', 'seek=%s' % (size,)])
        _run(['mkfs.btrfs', '-f', args[0]])
    elif step == 'unmount':
        _run(['sudo', 'sync'])
        #_run(['sudo', 'btrfs', 'subvolume', 'sync', args[0]])
        _run(['sudo', 'umount', args[0]])
    elif step == 'subvolume-create':
        _run(['btrfs', 'subvolume', 'create', args[0]])
    elif step == 'subvolume-mount':
        _run(['mkdir', '-p', args[1]])
        _run(['sudo', 'mount', '-o', 'loop,rw,subvolid=%d' % (args[2],), '-t', 'btrfs', args[0], args[1]])
    elif step == 'debootstrap':
        pass
    elif step == 'snapshot-create':
        _run(['sudo', 'btrfs', 'subvolume', 'snapshot', args[0], '%s/%d' % (args[1], args[2])])
    elif step == 'snapshot-delete':
        _run(['sudo', 'btrfs', 'subvolume', 'delete', '%s/%d' % (args[0], args[1])])
    elif step == 'chown':
        _run(['sudo', 'chown', '%d:%d' % (args[1], args[2]), args[0]])
    elif step == 'move':
        _run(['sudo', 'mv', args[0], args[1]])
    elif step == 'remove':
        assert not args[0].startswith('/')
        _run(['sudo', 'rm', '-rf', args[0]])
    else:
        raise Exception('unknown action %s' % (step,))
