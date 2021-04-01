import os
import subprocess

from .util import sudo

__all__ = ['make_btrfs', 'mount', 'unmount', 'chown', 'move', 'remove',
           'subvolume_create', 'subvolume_mount', 'snapshot_create'
           'snapshot_delete']

def _run(*args, **kwargs):
    result = subprocess.run(*args, **kwargs)
    if result.returncode != 0:
        raise subprocess.SubprocessError(repr(args[0]) + ' failed')
    return result

def make_btrfs(file, size):
    _run(['dd', 'if=/dev/null', 'of=%s' % (file,), 'bs=1', 'seek=%s' % (size,)])
    _run(['mkfs.btrfs', '-f', file])

def mount(type, file, mountpoint):
    _run(['mkdir', '-p', mountpoint])
    _run(['sudo', 'mount', '-o', 'loop,rw', '-t', type, file, mountpoint])

def unmount(mountpoint):
    _run(['sudo', 'sync'])
    #_run(['sudo', 'btrfs', 'subvolume', 'sync', mountpoint])
    _run(['sudo', 'umount', mountpoint])

def chown(path, uid, gid):
    _run(['sudo', 'chown', '%d:%d' % (uid, gid), path])

def move(src, dest):
    _run(['sudo', 'mv', src, dest])

def remove(path):
    assert not path.startswith('/')
    _run(['sudo', 'rm', '-rf', path])

def subvolume_create(path):
    _run(['btrfs', 'subvolume', 'create', path])

def subvolume_mount(file, mountpoint, subvolid=0):
    _run(['mkdir', '-p', mountpoint])
    _run(['sudo', 'mount', '-o', 'loop,rw,subvolid=%d' % (subvolid,), '-t', 'btrfs', file, mountpoint])

def snapshot_create(src, dest):
    _run(['sudo', 'btrfs', 'subvolume', 'snapshot', src, dest])

def snapshot_delete(path):
    _run(['sudo', 'btrfs', 'subvolume', 'delete', path])
