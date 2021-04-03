from glob import iglob
import os
import subprocess

actions = {}
def action(fn):
    name = fn.__name__
    actions[name] = fn
    return fn

def run_action(env, action):
    name, args = action
    if isinstance(args, str):
        args = (args,)
    name = name.replace('-', '_')
    if not name in actions:
        raise Exception('Unknown action %s' % (name,))
    actions[name](env, *args)

@action
def install(env, value):
    packages = value.split()
    subprocess.run(['sudo', 'chroot', env.root, 'apt-get', '-y', 'install'] +
            packages, check=True)

@action
def script(env, value):
    code = b'set -e\n' + value.format(config=env).encode('utf8')
    script = os.path.join(env.root, '_script.sh')
    subprocess.run('sudo tee ' + script + ' > /dev/null', input=code,
            shell=True, check=True)

    try:
        subprocess.run(['sudo', 'chroot', env.root, '/bin/bash',
                '/_script.sh'], check=True)
    except:
        import traceback
        traceback.print_exc()
    finally:
        subprocess.run(['sudo', 'rm', os.path.join(env.root, '_script.sh')],
                check=True)

@action
def apt_update(env):
    subprocess.run(['sudo', 'chroot', env.root, 'apt-get', 'update'],
            check=True)

@action
def copy(env, value):
    for line in value.splitlines():
        source_pattern, destination = arg.split()
        for source in iglob(source_pattern):
            subprocess.run('sudo', 'cp', '-r', os.path.join(env.files, source),
                    os.path.join(env.root, destination), check=True)
