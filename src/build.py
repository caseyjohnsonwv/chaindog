import argparse
import logging
import os
from pathlib import Path
import shutil
from subprocess import run
from time import time


parser = argparse.ArgumentParser()
parser.add_argument("-s", "--skip-dependencies", action=argparse.BooleanOptionalAction, help="Include this flag to skip building lambda layers.")
parser.add_argument("-t", "--target", action="append", help="Target directory, can be passed more than once. If ommitted, all directories are built.")
parser.set_defaults(target=[])
ARGS = parser.parse_args()


logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
)
logger = logging.getLogger()


def main():
    logger.info("Initiating build sequence")
    start = time()
    artifacts = Path(os.getcwd()).joinpath('artifacts')
    shutil.rmtree(artifacts, ignore_errors=True)
    os.mkdir(artifacts)
    c = 0
    for dir in Path(os.getcwd()).iterdir():
        # skip artifcats directory
        if dir.is_dir() and dir.name != 'artifacts':
            # enable target flag
            if len(ARGS.target) == 0 or dir.name in ARGS.target:
                c += build_dir(dir)
    tdelta = time() - start
    logger.info(f"Built {c} Lambdas in {tdelta:.1f} seconds")


def build_dir(dir:Path) -> int:
    logger.info(f"Building {dir.name}")
    start = time()
    # create temp dir structure
    temp_dir = Path(os.getcwd()).joinpath('artifacts').joinpath(f"{dir.name}_build")
    shutil.rmtree(temp_dir, ignore_errors=True)
    os.mkdir(temp_dir)
    # determine if source code or lambda layer
    req_file ='requirements-lambda.txt'
    reqs_target = "python/lib/python3.8/site-packages"
    if dir.joinpath(req_file).exists():
        if ARGS.skip_dependencies:
            logger.info(f"Skipping {dir.name} due to --skip-dependencies flag")
            shutil.rmtree(temp_dir, ignore_errors=True)
            return 0
        # building lambda layer
        placeholder = temp_dir
        for part in reqs_target.split('/'):
            placeholder = placeholder.joinpath(part)
            os.mkdir(placeholder)
        shutil.copyfile(f"{dir.joinpath(req_file)}", f"{temp_dir.joinpath(req_file)}")
        # install linux requirements
        logger.debug(f"Using Docker to install requirements from {dir.name}/{req_file}")
        command = [
            'docker', 'run', '--rm', '--name', 'build', '-v', f"{temp_dir.as_posix()}:/var/task", 'public.ecr.aws/sam/build-python3.8', '/bin/sh', '-c',
            f"python -m pip install -r {req_file} --target {reqs_target}; exit"
        ]
        res = exec(command)
        try:
            res.check_returncode()
        except:
            logger.error(f"Failed to build {dir.name} - is the Docker daemon running?")
            logger.error(res.stderr.decode('utf-8'))
            exit(1)
    else:
        # packaging source code
        files = ' '.join([f"{dir.name}/{f.name}" for f in dir.iterdir()])
        command = ['git', 'check-ignore', files]
        res = exec(command)
        excludes = set(p.split('/')[-1] for p in res.stdout.decode('utf-8').split('\n') if len(p) > 0)
        logger.debug(f"Excluding {len(excludes)} .gitignore'd files")
        if len(excludes) > 0:
            logger.debug(', '.join(excludes))
        for f in dir.iterdir():
            if f.name not in excludes:
                src = dir.joinpath(f.name)
                dest = temp_dir.joinpath(f.name)
                shutil.copyfile(src, dest)
    # zip and delete temp dir
    shutil.make_archive(f"artifacts/{dir.name}", 'zip', temp_dir.absolute())
    shutil.rmtree(temp_dir)
    tdelta = time() - start
    logger.info(f"Built {dir.name} in {tdelta:.1f} seconds")
    return 1


def exec(cmd:list=[]):
    return run(cmd, capture_output=True)


if __name__ == '__main__':
    main()