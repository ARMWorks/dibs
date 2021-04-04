import os
from subprocess import run

def mount_btrfs(env, check=True):
    run(['mkdir', '-p', env.cache, env.btrfs], check=check)
    run(['sudo', 'mount', '-o', 'loop,rw,subvolid=0', '-t', 'btrfs', env.btrfs_image, env.btrfs], check=check)
    if not os.path.exists(env.root):
        run(['sudo', 'btrfs', 'subvolume', 'create', env.root], check=check)
    run(['sudo', 'mkdir', '-p', env.snapshots], check=check)

def unmount_btrfs(env, check=True):
    run(['sudo', 'umount', env.btrfs], check=check)

def mount_extra(env, check=True):
    run(['sudo', 'mkdir', '-p', env.procfs, env.sysfs, env.archives, env.usr_bin], check=check)
    qemu = 'qemu-%s-static' % ('arm' if env.arch in ('armhf', 'armel') else env.arch,)
    run(['sudo', 'cp', os.path.join('/usr/bin', qemu), env.usr_bin], check=check)
    run(['sudo', 'mount', '-t', 'proc', 'proc', env.procfs], check=check)
    run(['sudo', 'mount', '-t', 'sysfs', 'sysfs', env.sysfs], check=check)
    run(['sudo', 'mount', '--bind', env.cache, env.archives], check=check)

def unmount_extra(env, check=True):
    qemu = 'qemu-%s-static' % ('arm' if env.arch in ('armhf', 'armel') else env.arch,)
    qemu = os.path.join(env.usr_bin, qemu)
    if os.path.exists(qemu):
        run(['sudo', 'rm', qemu])
    run(['sudo', 'umount', env.procfs], check=check)
    run(['sudo', 'umount', env.sysfs], check=check)
    run(['sudo', 'umount', env.archives], check=check)
