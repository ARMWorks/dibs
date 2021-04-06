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
        return self.message + '\n' + indent(self.code, '> ')

actions = {}
def action(fn):
    name = fn.__name__
    actions[name] = fn
    return fn

def run_action(env, action):
    name, args = action
    name = name.translate({32: 95, 45: 95}) # change ' ' and '-' to '_'
    if not name in actions:
        raise Exception('Unknown action ' + name)
    actions[name](env, args)

@action
def install(env, args):
    packages = args.split()
    subprocess.run(['sudo', 'chroot', env.root, 'apt-get', '-y', 'install'] +
            packages, check=True)

@action
def target_script(env, args):
    code = b'set -e\n' + args.format(config=env).encode('utf8')
    script = os.path.join(env.root, '_script.sh')
    subprocess.run('sudo tee ' + script + ' > /dev/null', input=code,
            shell=True, check=True)

    try:
        subprocess.run(['sudo', 'chroot', env.root, '/bin/bash',
                '/_script.sh'], check=True)
    except:
        raise ScriptException('Error running script', args)
    finally:
        subprocess.run(['sudo', 'rm', os.path.join(env.root, '_script.sh')],
                check=True)

@action
def host_script(env, args):
    code = b'set -e\n' + args.format(config=env).encode('utf8')
    script = '/tmp/_script.sh'
    subprocess.run('sudo tee ' + script + ' > /dev/null', input=code,
            shell=True, check=True)

    try:
        subprocess.run(['sudo', '/bin/bash', script], check=True)
    except:
        raise ScriptException('Error running script', args)
    finally:
        subprocess.run(['sudo', 'rm', script], check=True)

@action
def script(env, args):
    target_script(env, args)

@action
def copy(env, args):
    for line in args.splitlines():
        source_pattern, destination = shlex.split(line)
        source_pattern = os.path.join(configs_dir, env.files, source_pattern)
        destination = os.path.join(env.root, destination.lstrip('/'))
        for source in iglob(source_pattern):
            subprocess.run(['sudo', 'cp', '-r', source, destination],
                    check=True)

@action
def download(env, args):
    download = os.path.join(env.downloads, args['file'])
    if not os.path.exists(download):
        subprocess.run(['mkdir', '-p', env.downloads], check=True)
        subprocess.run(['wget', args['url'], '-O', download], check=True)
