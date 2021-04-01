import os
import sys

import dibs.project as project
import dibs.util as util

if __name__ == '__main__':
    if not os.path.exists('config.yaml'):
        project.defconfig('mini210')
    project.build()
