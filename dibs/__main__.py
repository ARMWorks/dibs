import argparse
import os
import subprocess
import sys
import time

import dibs.project as project
import dibs.target as target
from dibs.action import ScriptException


def mount(args):
    env = project.get_env()

    if not args.force:
        if env._state.get('btrfs_mounted'):
                print ('aldready mounted, try -f')
                return
    check = not args.force

    if not env._state.get('btrfs_mounted') and not args.force:
        check = False

    try:
        target.mount_btrfs(env, check)
        env._state['btrfs_mounted'] = True
        target.mount_extra(env, check)
        env._state['extra_mounted'] = True
        project.save(env)
    except:
        print('Could not mount btrfs image', file=sys.stderr)

def unmount(args):
    env = project.get_env()

    if not args.force:
        if not env._state.get('btrfs_mounted'):
            print('not mounted, try -f')
            return
    check = not args.force

    try:
        target.unmount_extra(env, check)
        env._state['extra_mounted'] = False
        target.unmount_btrfs(env, check)
        env._state['btrfs_mounted'] = False
        project.save(env)
    except:
        print('Could not unmount btrfs image', file=sys.stderr)

def build(args):
    try:
        env = project.get_env()
        project.build(env)
    except ScriptException as e:
        print(e)
    except Exception:
        raise

def config(args):
    try:
        project.config(args.CONFIG, args.force)
    except (FileExistsError, FileNotFoundError) as e:
        print(e)

def shell(args):
    env = project.get_env()

    skip_mount = env._state.get('btrfs_mounted')
    if not skip_mount:
        target.mount_btrfs(env)
        target.mount_extra(env)

    try:
        subprocess.run(['sudo', 'chroot', env.root, '/bin/bash'])
    except:
        raise
    finally:
        if not skip_mount:
            target.unmount_extra(env)
            target.unmount_btrfs(env)

def copy(args):
    env = project.get_env()

    initial_dir = os.getcwd()
    skip_mount = env._state.get('btrfs_mounted')
    if not skip_mount:
        target.mount_btrfs(env)
        target.mount_extra(env)

    args.DEST = os.path.abspath(args.DEST)
    try:
        os.chdir(env.root)
        subprocess.run(['sudo', 'cp', '-rpx', '.', args.DEST])
        subprocess.run(['sudo', 'sync'])
        subprocess.run(['sudo', 'sync'])
    except:
        raise
    finally:
        os.chdir(initial_dir)
        if not skip_mount:
            target.unmount_extra(env)
            target.unmount_btrfs(env)

def main():
    parser = argparse.ArgumentParser(description='Debian Image Build System')
    subparsers = parser.add_subparsers(title='subcommands',
                                       description='valid subcommands')

    parser_mount = subparsers.add_parser('mount')
    parser_mount.add_argument('-f', '--force', action='store_true')
    parser_mount.set_defaults(func=mount)

    parser_unmount = subparsers.add_parser('unmount', aliases=['umount'])
    parser_unmount.add_argument('-f', '--force', action='store_true')
    parser_unmount.set_defaults(func=unmount)

    parser_build = subparsers.add_parser('build')
    parser_build.set_defaults(func=build)

    parser_config = subparsers.add_parser('config')
    parser_config.add_argument('-f', '--force', action='store_true')
    parser_config.add_argument('CONFIG')
    parser_config.set_defaults(func=config)

    parser_shell = subparsers.add_parser('shell')
    parser_shell.set_defaults(func=shell)

    parser_copy = subparsers.add_parser('copy')
    parser_copy.add_argument('DEST')
    parser_copy.set_defaults(func=copy)

    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)

if __name__ == '__main__':
    main()
