from __future__ import print_function

import collections
import yaml
import subprocess

from . import formatting

VersionId = collections.namedtuple('VersionId', 'version sha1')


def tag_workflow(args):
    from . import config
    import semver
    wflowdata = config.get_metadata_by_name(args.workflow_name)

    if wflowdata.is_dirty():
        err = (('ERROR: Workflow in {p} has local changes and/or untracked files. They must be '
                'commited before this workflow can be tagged with a new version. For instance, '
                'you could run:'
                '\n  $ cd {p}\n  $ git add .\n  $ git commit -m "COMMIT MESSAGE HERE"'
                ).format(p=formatting.pretty_path(wflowdata.workflowdir)))
        formatting.fail(err)

    elif not wflowdata.is_updated():
        err = (("ERROR: can't update. Workflow in {p} is up to date with version {v}"
                ).format(p=formatting.pretty_path(wflowdata.workflowdir),
                         v=wflowdata.version))
        formatting.fail(err)

    else:
        try:
            version = semver.parse_version_info(args.newversion)
        except ValueError:
            formatting.fail("ERROR: '%s' is not a valid Semantic Version; see http://semver.org"
                 % args.newversion)

        last_version = wflowdata.last_version
        if (last_version != 'unversioned'
            and version <= semver.parse_version_info(last_version.version)):
            formatting.fail("Requested version (%s) must be GREATER than previous tag (%s).")

        wflowdata.update_version(args.newversion)

        print("Incremented version of workflow '{w[name]}': {last_version} -> {newversion}"
              .format(w=wflowdata.metadata,
                      last_version=last_version,
                      newversion=args.newversion))
        print("Make sure to git commit %s." %
              (wflowdata.sourcedir / '.versions.yml').as_posix())


class Versions(object):
    def __init__(self):
        self.sources = {}

    def read_version_hashes(self, parentdir):
        if parentdir in self.sources:
            raise ValueError('Already read version hashes for file "%s"' % parentdir)
        self.sources[parentdir.absolute()] = self.get_version_hashes(parentdir)

    def get_last_version(self, source, workflowname):
        if source not in self.sources:
            raise ValueError('No version information for workflows in source')

        versions = self.sources[source]
        if workflowname not in versions:
            return 'unversioned'

        return versions[workflowname]

    def get_version_string(self, source, workflowname):
        version_id = self.get_last_version(source, workflowname)
        if version_id == 'unversioned':
            return version_id

        dir = source / workflowname
        sha1 = self.get_directory_sha1(dir)
        if sha1 != version_id.sha1 or self.get_directory_dirty(dir):
            return 'mod'+version_id.version
        else:
            return version_id.version

    def update_version(self, source, workflowname, newversion):
        newsha = self.get_directory_sha1(source / workflowname)
        self.sources[source.absolute()][workflowname] = VersionId(version=newversion, sha1=newsha)
        data = {key: {'sha1': val.sha1, 'version': val.version}
                for key, val in
                sorted(self.sources[source.absolute()].items())}

        with (source/".versions.yml").open('w') as verfile:
            yaml.dump(data, verfile, default_flow_style=False)

    @staticmethod
    def get_version_hashes(parentdir):
        """ Parse the .versions.yml file, if it exists

        Args:
            parentdir (pathlib.Path): directory containing the workflows and the .versions.yml file

        Returns:
            Dict[str, VersionId]: stored version numbers and SHA-1 hashes.
               If .versions.yml does not exists, returns an empty dict
        """
        path = parentdir/".versions.yml"
        if not path.exists():
            print('Warning: No version information for workflows in directory %s' % parentdir)
            return {}
        with path.open('r') as verfile:
            versions = yaml.load(verfile)
        if versions is None:
            return {}  # the file is empty
        for key, value in versions.items():
            versions[key] = VersionId(**value)

        return versions

    @staticmethod
    def get_directory_sha1(dir):
        """ Return SHA-1 of a git directory

        Note:
            This returns the SHA-1 of the HEAD only. Use `get_directory_dirty` as well to check
            if there are local changes.

        Args:
            dir (pathlib.Path): path within this git repo

        Returns:
            str: the directory's sha-1
        """
        dir = dir.absolute()
        oput = subprocess.check_output(['git', 'ls-tree', '-d', 'HEAD', dir.name],
                                       cwd=dir.parents[0].as_posix())
        lines = oput.splitlines()
        if len(lines) != 1:
            raise IOError('Error examining directory %s' % dir)

        return lines[0].split()[2]

    @staticmethod
    def get_directory_dirty(dir):
        """ Return True if directory has changes (staged or not) relative to its HEAD

        Args:
            dir (pathlib.Path): path within this git repo

        Returns:
            bool: True if directory has changes or untracked files relative to HEAD

        References:
            http://stackoverflow.com/a/2658301/1958900
        """
        oput = subprocess.check_output('git status --porcelain .'.split(),
                                       cwd=dir.absolute().as_posix())
        return bool(oput.strip())
