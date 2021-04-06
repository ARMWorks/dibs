import os
import shutil
import sys
from subprocess import run

from . import target
from .action import ScriptException, run_action
from .yaml import MultiDict, yaml

file_dir = os.path.dirname(os.path.realpath(__file__))
configs_dir = os.path.abspath(os.path.join(file_dir, '..', 'configs'))

def config(config, force=False):
    config_file = os.path.join(configs_dir, config) + '.yaml'
    if not os.path.exists(config_file):
        raise FileNotFoundError("Configuration not found")
    if not force and os.path.exists('config.yaml'):
        raise FileExistsError("Refusing to overwrite existing configuration")
    with open('config.yaml', 'w') as f:
        f.write('include:\n  ' + config + '\n')

def get_actions(config):
    actions = []
    actions_md = config.setdefault('actions', MultiDict())
    if actions_md:
        for action, action_data in actions_md.items():
            actions.append((action, action_data))

    cleanup_md = config.setdefault('cleanup', MultiDict())
    if cleanup_md:
        for action, action_data in cleanup_md.items():
            actions.append((action, action_data))

    return actions

def first_diff(env):
    if not hasattr(env, '_last_data') or not env._last_data:
        return 0

    config = env._data.get('config', MultiDict())
    last_config = env._last_data.get('config', MultiDict())

    for key in ('btrfs-size', 'mirror', 'distro', 'arch', 'suite'):
        if config.get(key) != last_config.get(key):
            return 0

    if config != last_config:
        return 1

    actions = get_actions(env._data)
    last_actions = get_actions(env._last_data)

    zipped_actions = tuple(zip(actions, last_actions))
    for i, zipped_action in enumerate(zipped_actions):
        action, last_action = zipped_action
        if action != last_action:
            return i + 1

    return len(zipped_actions) + 1

def load(file):
    if not os.path.exists(file):
        raise FileNotFoundError('File not found: ' + file)

    data = MultiDict()

    with open(file) as f:
        override_data = yaml.load(f)
    if 'include' in override_data:
        includes = override_data['include']
        if isinstance(includes, str):
            includes = includes.split()
        for include in includes:
            include_data = load(os.path.join(configs_dir, include + '.yaml'))
            if 'config' in include_data:
                for key, value in include_data['config'].items():
                    data.setdefault('config', MultiDict())[key] = value
            if 'actions' in include_data:
                for key, value in include_data['actions'].items():
                    data.setdefault('actions', MultiDict()).append(key, value)
            if 'cleanup' in include_data:
                for key, value in include_data['cleanup'].items():
                    data.setdefault('cleanup', MultiDict()).append(key, value)

    if 'config' in override_data:
        for key, value in override_data['config'].items():
            data.setdefault('config', MultiDict())[key] = value
    if 'actions' in override_data:
        for key, value in override_data['actions'].items():
            data.setdefault('actions', MultiDict()).append(key, value)
    if 'cleanup' in override_data:
        for key, value in override_data['cleanup'].items():
            data.setdefault('cleanup', MultiDict()).append(key, value)

    return data

def save(env, increment_step=False):
    if increment_step:
        env._step += 1
        env._state['step'] = env._step
    env._data['state'] = env._state

    with open('.state.yaml', 'w') as f:
        yaml.dump(env._data, f)

def get_env():
    class Env(object):
        pass
    env = Env()
    env._data = load('config.yaml')

    for key, value in env._data['config'].items():
        key = key.replace('-', '_')
        setattr(env, key, value)

    env.configs = configs_dir
    env.project = os.path.abspath('.')
    env.btrfs_image = os.path.join(env.project, 'btrfs.img')
    env.btrfs = os.path.join(env.project, 'btrfs')
    env.root = os.path.join(env.btrfs, 'root')
    env.oldroot = os.path.join(env.btrfs, 'oldroot')
    env.snapshots = os.path.join(env.btrfs, 'snapshots')
    env.cache = os.path.join(env.project, '.cache')
    env.packages = os.path.join(env.cache, env.distro, env.arch, env.suite)
    env.downloads = os.path.join(env.project, '.cache/downloads')
    env.archives = os.path.join(env.root, 'var/cache/apt/archives')
    env.procfs = os.path.join(env.root, 'proc')
    env.sysfs = os.path.join(env.root, 'sys')
    env.usr_bin = os.path.join(env.root, 'usr/bin')

    if os.path.exists('.state.yaml'):
        with open('.state.yaml') as f:
            env._last_data = yaml.load(f)

    env._diff = first_diff(env)
    if not os.path.exists(env.btrfs_image):
        env._diff = 0
    env._state = MultiDict() if env._diff == 0 else env._last_data['state']
    env._step = env._state.get('step', 0)
    if env._step == 0:
        env._diff = 0

    return env

def build(env):
    actions = get_actions(env._data)
    if not env._diff == 0 and len(actions) == env._step - 1 and \
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

    try:
        if env._diff == 0:
            env._state = MultiDict()
            env._step = 0
            if os.path.exists(env.btrfs_image):
                os.remove(env.btrfs_image)
            save(env)

            run(['dd', 'if=/dev/null', 'of=' + env.btrfs_image, 'bs=1',
                    'seek=' + env.btrfs_size], check=True)
            run(['mkfs.btrfs', '-f', env.btrfs_image], check=True)

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
                args.append('--keyring=' + removed_keys)

            run(['sudo', 'debootstrap', '--variant=minbase',
                    '--arch=' + env.arch] + args + [env.suite,
                    env.root, env.mirror + '/' + env.distro],
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
            run_action(env, action)

            snapshot = os.path.join(env.snapshots, str(env._step))
            run(['sudo', 'btrfs', 'subvolume', 'snapshot', env.root, snapshot],
                    check=True)
            save(env, True)

    except ScriptException:
        raise

    finally:
        if env._state.get('extra_mounted'):
            target.unmount_extra(env, False)
            env._state['extra_mounted'] = False
        if env._state.get('btrfs_mounted'):
            target.unmount_btrfs(env, False)
            env._state['btrfs_mounted'] = False
        save(env)
