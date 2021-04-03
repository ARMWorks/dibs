import os
import shlex
import subprocess
from glob import iglob
from textwrap import indent

file_dir = os.path.dirname(os.path.realpath(__file__))
configs_dir = os.path.abspath(os.path.join(file_dir, '..', 'configs'))

class ScriptException(Exception):
    def __init__(self, message, code):
        self.message = message
        self.code = code
        super().__init__(self.message)

    def __str__(self):
        return self.message + '\n' + indent(self.code, '>   ')

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
        raise ScriptException('Error running script', value)
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
        source_pattern, destination = shlex.split(line)
        source_pattern = os.path.join(configs_dir, env.files, source_pattern)
        destination = os.path.join(env.root, destination.lstrip('/'))
        for source in iglob(source_pattern):
            subprocess.run(['sudo', 'cp', '-r', source, destination],
                    check=True)
