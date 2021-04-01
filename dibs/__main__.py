import os
import sys

import dibs.project as project
import dibs.util as util

if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == 'sudo':
        sys.exit(util.call(sys.argv[2]))

    if not os.path.exists('config.yaml'):
        project.defconfig('mini210')
    project.build()
