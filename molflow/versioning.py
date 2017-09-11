from __future__ import print_function


from git import Repo, InvalidGitRepositoryError


import semver

# import collections
# import yaml
# import subprocess

from . import formatting



class WorkflowVersions(object):
    def __init__(self, path):
        self.git_dirty = False
        self.git_version_tags = []
        self.git_other_tags = []
        self.git_branches = []
        self.git_current_branch = None
        self.git_current_state = False
        self.git_repo = None

        try:
            self.git_repo = Repo(str(path))
        except InvalidGitRepositoryError:
            self.git_repo = None
            # No point in trying to figure out more versions if we have no git repo.
            return

        self._discover_tags()
        self._discover_branches()
        self._check_current_state()


    def default_version( self ):
        # returns the version string and version type for the default version
        # Priority:
        # non-git
        # git:dirty
        # git:latest-version-tag
        # git:current-branch-head
        # git:other-tags-single
        # git:current-state
        if self.git_repo is None:
            return ("Unversioned","non-git")
        if self.git_dirty and self.git_current_state == 'branch':
            return ("{}+dirty".format(self.git_current_branch),"git:dirty")
        elif self.git_dirty and self.git_current_state == 'detached':
            return ("{}+dirty".format(str(self.git_repo.commit())),"git:dirty")
        elif self.git_dirty:  # not sure how this would happen, but for
                              # completeness going to include it.
            return ("dirty","git:dirty")
        if len(self.git_version_tags) > 0:
            return (self.git_version_tags[-1][0], "git:latest-version-tag") 
                    # recall that we store both the name and the semver, and the list is 
                    # already sorted in ascending order. So we take just the name from the 
                    # highest version.
        if self.git_current_state == 'branch':
            return (self.git_current_branch, "git:current-branch-head")
        if len(self.git_other_tags) == 1:
            return (self.git_other_tags[0], "git:other-tags-single")
        
        return (str(self.git_repo.commit()), "git:current-state")

    def select_version( self, version_name ):
        if self.git_repo is None:
            formatting.fail("Can not select a version for a workflow that is not git versioned.")
        if self.git_dirty and version_name != self.default_version()[0]:
            formatting.fail("Can not select a version for a workflow that has a dirty git directory, unless it's the current state.")
        elif self.git_dirty:
            return

            
        # Would like to figure out a better way to do this; we've guaranteed
        # that it's not a dirty git repo (in which this would be destructive),
        # but it does leave the head in a weird state. We could use a specific
        # branch name and remove it / recreate as needed, but that might have
        # some issues. See
        # e.g. http://gitpython.readthedocs.io/en/stable/tutorial.html#switching-branches
        
        all_tag_names = list(zip(*self.git_version_tags)[0]) + self.git_other_tags
                        # This zip is the first item of each tag entry in git_version_tags, as a list and the concatenated with the other tags list.
        if version_name in all_tag_names:
            for tag in self.git_repo.tags:
                if tag.name == version_name:
                    self.git_repo.head.reference = tag.commit
                    self.git_repo.head.reset(index=True,working_tree=True)
                    return

        if version_name in self.git_branches:
            for branch in self.git_repo.branches:
                if version_name == branch.name:
                    branch.checkout()
                    return
            
        formatting.fail("Could not select version [{version}]: it did not match any tag or branch name in the git repository for this workflow.".format( version=version_name))

    def select_default_version( self ):
        dv = self.default_version()
        if dv[1] in ['git:current-state','git:dirty','non-git']:
            # we should not attempt to select any of these conditions, as they are 'fragile'
            return 
        if dv[1] == 'git:current-branch-head':
            # We don't need to switch anything around if the active branch is the correct default.
            return 

        # what we have as the default is either a version tag or a 'other' tag that is the only other tag.
        self.select_version( dv[0] )
        
    def format_versions( self, offset = 0):
        from termcolor import colored
        from textwrap import wrap
        result = ""
        prev_line = False

        if self.git_dirty:
            dirty_line = ' '*offset + colored('WARNING:','white','on_red') + ' '
            dirty_line += 'dirty repository on branch/commit: ('
            dirty_line += colored(self.default_version()[0], 'red')
            dirty_line += ')'
            result = dirty_line
            prev_line = True

        def format_line( initial_text, list_items, offset, prev_line ):
            lines=" " * offset + colored(initial_text,'blue')
            lines_raw = ", ".join([colored(i,'red') for i in list_items])
            lines_text= wrap(lines_raw, subsequent_indent = ' '*offset, width=135)
            for line in lines_text:
                lines += line + '\n'
        
            if prev_line:
                return '\n' + lines
            else:
                return lines
            
        if len(self.git_version_tags) > 0:
            result += format_line("Versions: ",list(reversed(zip(*self.git_version_tags)[0])),offset, prev_line)
            prev_line = False

        if len(self.git_other_tags) > 0:
            result += format_line("Tags: ",self.git_other_tags, offset, prev_line )
            prev_line = False

        if len(self.git_branches) > 0:
            result += format_line("Branches: ", self.git_branches, offset, prev_line )
            prev_line = False
        
        if len(result) == 0:
            result = " "*offset + colored("WARNING:","white","on_red") + " Unversioned\n"


        return result

    def _discover_tags( self ):
        tags = [i.name for i in self.git_repo.tags]
        for t in tags:
            try:
                if t.startswith('v'):
                    version_tag = semver.parse(t[1:])
                else:
                    version_tag = semver.parse(t)
            except ValueError:
                version_tag = None

            if version_tag is not None:
                self.git_version_tags.append( (t,version_tag) )
            else:
                self.git_other_tags.append( t )
        
        self.git_version_tags.sort(key = lambda x: x[1])  # sort by the semver tag info
        self.git_other_tags.sort()

    def _discover_branches( self ):
        self.git_branches = [i.name for i in self.git_repo.branches]
        try:
            self.git_current_branch = self.git_repo.active_branch.name
            self.git_current_state = 'branch'
        except TypeError:
            # happens when HEAD is in a detached state
            self.git_current_branch = [b.name for b in self.git_repo.branches if self.git_repo.is_ancestor( self.git_repo.commit(), b.commit)]
            self.git_current_state = 'detached'

    def _check_current_state( self ):
        self.git_dirty = self.git_repo.is_dirty()

            
# class Versions(object):
#     def __init__(self):
#         self.sources = {}

#     def read_version_hashes(self, parentdir):
#         if parentdir in self.sources:
#             raise ValueError('Already read version hashes for file "%s"' % parentdir)
#         self.sources[parentdir.absolute()] = self.get_version_hashes(parentdir)

#     def get_last_version(self, source, workflowname):
#         if source not in self.sources:
#             raise ValueError('No version information for workflows in source')

#         versions = self.sources[source]
#         if workflowname not in versions:
#             return 'unversioned'

#         return versions[workflowname]

#     def get_version_string(self, source, workflowname):
#         version_id = self.get_last_version(source, workflowname)
#         if version_id == 'unversioned':
#             return version_id

#         dir = source / workflowname
#         sha1 = self.get_directory_sha1(dir)
#         if sha1 != version_id.sha1 or self.get_directory_dirty(dir):
#             return 'mod'+version_id.version
#         else:
#             return version_id.version

#     def update_version(self, source, workflowname, newversion):
#         newsha = self.get_directory_sha1(source / workflowname)
#         self.sources[source.absolute()][workflowname] = VersionId(version=newversion, sha1=newsha)
#         data = {key: {'sha1': val.sha1, 'version': val.version}
#                 for key, val in
#                 sorted(self.sources[source.absolute()].items())}

#         with (source/".versions.yml").open('w') as verfile:
#             yaml.dump(data, verfile, default_flow_style=False)

#     @staticmethod
#     def get_version_hashes(parentdir):
#         """ Parse the .versions.yml file, if it exists

#         Args:
#             parentdir (pathlib.Path): directory containing the workflows and the .versions.yml file

#         Returns:
#             Dict[str, VersionId]: stored version numbers and SHA-1 hashes.
#                If .versions.yml does not exists, returns an empty dict
#         """
#         path = parentdir/".versions.yml"
#         if not path.exists():
#             print('Warning: No version information for workflows in directory %s' % parentdir)
#             return {}
#         with path.open('r') as verfile:
#             versions = yaml.load(verfile)
#         if versions is None:
#             return {}  # the file is empty
#         for key, value in versions.items():
#             versions[key] = VersionId(**value)

#         return versions

#     @staticmethod
#     def get_directory_sha1(dir):
#         """ Return SHA-1 of a git directory

#         Note:
#             This returns the SHA-1 of the HEAD only. Use `get_directory_dirty` as well to check
#             if there are local changes.

#         Args:
#             dir (pathlib.Path): path within this git repo

#         Returns:
#             str: the directory's sha-1
#         """
#         dir = dir.absolute()
#         oput = subprocess.check_output(['git', 'ls-tree', '-d', 'HEAD', dir.name],
#                                        cwd=dir.parents[0].as_posix())
#         lines = oput.splitlines()
#         if len(lines) != 1:
#             raise IOError('Error examining directory %s' % dir)

#         return lines[0].split()[2]

#     @staticmethod
#     def get_directory_dirty(dir):
#         """ Return True if directory has changes (staged or not) relative to its HEAD

#         Args:
#             dir (pathlib.Path): path within this git repo

#         Returns:
#             bool: True if directory has changes or untracked files relative to HEAD

#         References:
#             http://stackoverflow.com/a/2658301/1958900
#         """
#         oput = subprocess.check_output('git status --porcelain .'.split(),
#                                        cwd=dir.absolute().as_posix())
#         return bool(oput.strip())
