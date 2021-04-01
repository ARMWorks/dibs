import os
import shutil
from collections import OrderedDict
from copy import deepcopy

from . import action, util, yaml

file_dir = os.path.dirname(os.path.realpath(__file__))
machine_dir = os.path.abspath(os.path.join(file_dir, '..', 'machine'))

def defconfig(machine):
    machine_config = os.path.join(machine_dir, machine, 'config.yaml')
    if not os.path.exists(machine_config):
        raise FileNotFoundError("Default configuration not found")
    if os.path.exists('config.yaml'):
        raise FileExistsError("Refusing to overwrite existing configuration")
    shutil.copyfile(machine_config, 'config.yaml')

def get_steps(config):
    steps = []
    for action, action_data in config.get('actions', OrderedDict()).items():
        if isinstance(action_data, str):
            steps.append((action, action_data))
        elif isinstance(action_data, list):
            for entry in action_data:
                steps.append((action, entry))

    return steps

def first_diff(previous_config, config):

    if previous_config['config'] != config['config']:
        return 0

    previous_steps = get_steps(previous_config)
    steps = get_steps(config)

    zipped_steps = zip(previous_steps, steps)
    for i, zipped_step in enumerate(zipped_steps):
        previous_step, step = zipped_step

        if previous_step != step:
            return i + 1

    return len(steps) + 1

def save(config):
    with open('.state.yaml', 'w') as f:
        yaml.ordered_dump(config, f)

def revert(config, start, end):
    for i in range(end, start + 1, -1):
        print('snapshot-delete %d' % (i,))
        action.run(config, 'snapshot-delete', 'btrfs/snapshots', i)

    action.run(config, 'remove', 'btrfs/rootfs')
    action.run(config, 'move', 'btrfs/snapshots/%d' % (start + 1,), 'btrfs/rootfs')

    config['state']['step'] = start
    save(config)

def snapshot(config, step_num):
    action.run(config, 'snapshot-create', 'btrfs/rootfs' , 'btrfs/snapshots', step_num)
    config['state']['step'] = step_num
    save(config)

def build():
    start_over = False

    if not os.path.exists('config.yaml'):
        raise FileNotFoundError("Configuration file not found")
    with open('config.yaml') as f:
        config = yaml.ordered_load(f)
        config['state'] = OrderedDict()

    if os.path.exists('.state.yaml'):
        with open('.state.yaml') as f:
            previous_config = yaml.ordered_load(f)
        diff_num = first_diff(previous_config, config)
        config['state'] = deepcopy(previous_config['state'])
    else:
        start_over = True

    if not os.path.exists('btrfs.img'):
        start_over = True

    step_num = config['state'].get('step', 0)
    if start_over:
        config['state'] = OrderedDict()
        diff_num = 0
        step_num = 0
        if os.path.exists('btrfs.img'):
            if config['state'].get('btrfs_mounted'):
                try:
                    action.run(config, 'unmount', 'btrfs')
                except:
                    pass
            os.remove('btrfs.img')
            config['state']['btrfs_mounted'] = False
            config['state']['btrfs_init'] = False
            save(config)

        action.run(config, 'make-btrfs', 'btrfs.img')

    try:
        if not config['state'].get('btrfs_mounted'):
            action.run(config, 'subvolume-mount', 'btrfs.img', 'btrfs', 0)
            config['state']['btrfs_mounted'] = True
            save(config)

        if diff_num < step_num:
            print(diff_num, step_num)
            revert(config, diff_num, step_num)
            step_num = diff_num

        if not config['state'].get('btrfs_init'):
            action.run(config, 'chown', 'btrfs', os.getuid(), os.getgid())
            action.run(config, 'subvolume-create', 'btrfs/rootfs')
            action.run(config, 'chown', 'btrfs/rootfs', 0, 0)
            os.mkdir('btrfs/snapshots')
            config['state']['btrfs_init'] = True
            save(config)

        if step_num == 0:
            print(('debootstrap',))
            step_num += 1
            snapshot(config, step_num)

        steps = get_steps(config)
        for step in steps[max(step_num - 1, 0):]:
            print(step)
            step_num += 1
            snapshot(config, step_num)

    except Exception as e:
        import traceback
        traceback.print_exc()

    finally:
        if config['state'].get('btrfs_mounted'):
            try:
                action.run(config, 'unmount', 'btrfs')
                config['state']['btrfs_mounted'] = False
                pass
            except:
                pass
        save(config)
