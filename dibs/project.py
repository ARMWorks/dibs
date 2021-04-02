import os
import shutil
import sys
from copy import deepcopy
from subprocess import run

from . import target
from .action import run_action
from .yaml import MultiDict, yaml

file_dir = os.path.dirname(os.path.realpath(__file__))
machine_dir = os.path.abspath(os.path.join(file_dir, '..', 'machine'))

def defconfig(machine):
    machine_config = os.path.join(machine_dir, machine, 'config.yaml')
    if not os.path.exists(machine_config):
        raise FileNotFoundError("Default configuration not found")
    if os.path.exists('config.yaml'):
        raise FileExistsError("Refusing to overwrite existing configuration")
    shutil.copyfile(machine_config, 'config.yaml')

def get_actions(config):
    actions = []
    config_actions = config.get('actions', MultiDict())
    if config_actions:
        for action, action_data in config_actions.items():
            if isinstance(action_data, str):
                actions.append((action, action_data))
            elif isinstance(action_data, list):
                for entry in action_data:
                    actions.append((action, entry))

    return actions

def first_diff(env):
    previous_actions = get_actions(env.previous_data)
    actions = get_actions(env.data)

    zipped_actions = tuple(zip(actions, previous_actions))
    for i, zipped_action in enumerate(zipped_actions):
        action, previous_action = zipped_action
        if action != previous_action:
            return i + 1

    return len(zipped_actions) + 1

def save(env, increment_step=False):
    config = MultiDict()
    config['config'] = env.config
    config['actions'] = env.actions

    if increment_step:
        env._step += 1
        env._state['step'] = env._step
    config['state'] = env._state

    with open('.state.yaml', 'w') as f:
        yaml.dump(config, f)

def get_env():
    class Env(object):
        pass
    env = Env()
    env._start_over = False
    env._state = MultiDict()

    if not os.path.exists('config.yaml'):
        raise FileNotFoundError('Configuration file not found')
    with open('config.yaml') as f:
        env.data = yaml.load(f)

    env.config = env.data['config']
    env.actions = env.data['actions']

    for key, value in env.config.items():
        key = key.replace('-', '_')
        setattr(env, key, value)

    env.btrfs_image = 'btrfs.img'
    env.btrfs = 'btrfs'
    env.root = os.path.join(env.btrfs, 'root')
    env.oldroot = os.path.join(env.btrfs, 'oldroot')
    env.snapshots = os.path.join(env.btrfs, 'snapshots')
    env.cache = os.path.join('.cache', env.distro, env.arch, env.suite)
    env.archives = os.path.join(env.root, 'var/cache/apt/archives')
    env.procfs = os.path.join(env.root, 'proc')
    env.sysfs = os.path.join(env.root, 'sys')
    env.usr_bin = os.path.join(env.root, 'usr/bin')

    if os.path.exists('.state.yaml'):
        with open('.state.yaml') as f:
            env.previous_data = yaml.load(f)

    if not os.path.exists(env.btrfs_image) or \
            not hasattr(env, 'previous_data') or \
            not env.previous_data or \
            env.config != env.previous_data['config']:
        env._start_over = True
        env._state = MultiDict()
    else:
        env._diff = first_diff(env)
        env._state = deepcopy(env.previous_data['state'])

    env._step = env._state.get('step', 0)
    if env._step == 0:
        env._start_over = True

    if env._start_over:
        env._diff = 0

    return env

def build(env):
    actions = get_actions(env.data)
    if not env._start_over and len(actions) == env._step - 1 and \
            env._step == env._diff:
        print('Nothing to do!', file=sys.stderr)
        return

    if env._state.get('extra_mounted'):
        target.unmount_extra(env, False)
        env._state['extra_mounted'] = False
    if env._state.get('btrfs_mounted'):
        target.unmount_btrfs(env, False)
        env._state['btrfs_mounted'] = False
    save(env)

    if env._start_over:
        env._state = MultiDict()
        env._step = 0
        if os.path.exists(env.btrfs_image):
            os.remove(env.btrfs_image)
        save(env)

        run(['dd', 'if=/dev/null', 'of=%s' % (env.btrfs_image,), 'bs=1',
                'seek=%s' % (env.btrfs_size,)], check=True)
        run(['mkfs.btrfs', '-f', env.btrfs_image], check=True)

    try:
        if not env._state.get('btrfs_mounted'):
            target.mount_btrfs(env)
            env._state['btrfs_mounted'] = True
            save(env)

        if env._diff < env._step:
            for index in range(env._step - 1, env._diff - 1, -1):
                snapshot = os.path.join(env.snapshots, str(index))
                run(['sudo', 'btrfs', 'subvolume', 'delete', snapshot],
                        check=True)

            env._step = env._diff - 1
            print('moving', env.root, 'to', env.oldroot, file=sys.stderr)
            run(['sudo', 'mv', env.root, env.oldroot], check=True)

            snapshot = os.path.join(env.snapshots, str(env._step))
            print('restoring', snapshot, 'to', env.root, file=sys.stderr)
            run(['sudo', 'mv', snapshot, env.root], check=True)

            run(['sudo', 'btrfs', 'subvolume', 'delete', env.oldroot],
                    check=True)

            run(['sudo', 'btrfs', 'subvolume', 'snapshot', env.root, snapshot],
                    check=True)

            save(env, True)

        if env._step == 0:
            args = []
            removed_keys = \
                    '/usr/share/keyrings/debian-archive-removed-keys.gpg'
            if os.path.exists(removed_keys):
                args.append('--keyring=%s' % (removed_keys,))

            run(['sudo', 'debootstrap', '--variant=minbase',
                    '--arch=%s' % (env.arch,)] + args + [env.suite,
                    env.root, '%s/%s' % (env.mirror, env.distro)],
                    check=True)

            snapshot = os.path.join(env.snapshots, str(env._step))
            run(['sudo', 'btrfs', 'subvolume', 'snapshot', env.root, snapshot],
                    check=True)
            save(env, True)

        if not env._state.get('extra_mounted'):
            target.mount_extra(env)
            env._state['extra_mounted'] = True
            save(env)

        for action in actions[max(env._step - 1, 0):]:
            if isinstance(action[0], tuple):
                action = (action[0][0], action[1])
            try:
                run_action(env, action)
            except:
                from pprint import pprint
                pprint(action)
                raise

            snapshot = os.path.join(env.snapshots, str(env._step))
            run(['sudo', 'btrfs', 'subvolume', 'snapshot', env.root, snapshot],
                    check=True)
            save(env, True)

    except:
        import traceback
        traceback.print_exc()

    finally:
        if env._state.get('extra_mounted'):
            target.unmount_extra(env, False)
            env._state['extra_mounted'] = False
        if env._state.get('btrfs_mounted'):
            target.unmount_btrfs(env, False)
            env._state['btrfs_mounted'] = False
        save(env)
