#!/usr/bin/env python
import datetime
import errno
from bugzilla import Bugzilla
from bugzilla.bug import Bug
import yaml
try:
    # Python 2 backwards compat
    from __builtin__ import raw_input as input
except ImportError:
    pass


BZ_URL = 'bugzilla.redhat.com'

OSP_TRACKERS = {
    '1548354': 'OSP12',
    '1548353': 'OSP13',
    '1553640': 'OSP14',
    }

bzapi = Bugzilla(BZ_URL)

if not bzapi.logged_in:
    raise SystemExit('Not logged in, see ~/.bugzillatoken.')


def search(payload):
    """
    Send a payload to the Bug.search RPC, and translate the result into
    bugzilla.bug.Bug results.
    """
    result = bzapi._proxy.Bug.search(payload)
    bugs = [Bug(bzapi, dict=r) for r in result['bugs']]
    return bugs


def query_params(tracker):
    """ Return a dict of basic Bugzilla search parameters. """
    params = {
        'include_fields': ['id', 'summary', 'status', 'last_change_time'],
        'f1': 'blocked',
        'o1': 'equals',
        'v1': tracker,
        'f2': 'bug_status',
        'o2': 'anywords',
        'v2': 'NEW ASSIGNED POST MODIFIED ON_DEV ON_QA'
    }
    return params.copy()


def sort_by_status(bug):
    if bug.status == 'NEW':
        return 0
    if bug.status == 'ASSIGNED':
        return 1
    if bug.status == 'POST':
        return 2
    if bug.status == 'ON_DEV':
        return 3
    if bug.status == 'MODIFIED':
        return 4
    if bug.status == 'ON_QA':
        return 5


def prompt_new_action(old_action):
    prompt = 'Enter an action for this bug: >'
    if old_action:
        print('Old action was:')
        print(old_action)
        prompt = 'Enter to keep this action, or type a new one: >'
    try:
        new_action = input(prompt)
    except KeyboardInterrupt:
        raise SystemExit("\nNot proceeding")
    if new_action:
        return new_action
    return old_action


def find_action(bug):
    status = load_status(bug)
    action = status.get('action')
    last_change_time = status.get('last_change_time')
    if not last_change_time:
        print('No last recorded date for %s' % bug.weburl)
        action = prompt_new_action(action)
        save_status(bug, action)
        return action
    if bug.last_change_time.value > last_change_time:
        print('%s has changed since last recorded action' % bug.weburl)
        action = prompt_new_action(action)
        save_status(bug, action)
    return action


def load_status(bug):
    """ Load a bug's status from disk. """
    filename = 'status/%d.yml' % bug.id
    try:
        with open(filename, 'r') as stream:
            return yaml.safe_load(stream)
    except IOError as e:
        if e.errno != errno.ENOENT:
            raise
        return {}


def save_status(bug, action):
    """ Persist a bug's action to disk. """
    filename = 'status/%d.yml' % bug.id
    data = {
        'action': action,
        'last_change_time': bug.last_change_time.value,
    }
    with open(filename, 'w') as stream:
        yaml.dump(data, stream, default_flow_style=False)


if __name__ == '__main__':
    for tracker, release in OSP_TRACKERS.items():
        payload = query_params(tracker)
        bugs = search(payload)
        print('Found %d bugs blocking %s' % (len(bugs), release))

        sorted_bugs = sorted(bugs, key=sort_by_status)

        for bug in sorted_bugs:
            print('https://bugzilla.redhat.com/%d - %s - %s'
                  % (bug.id, bug.status, bug.summary))
            # TODO: does this print the human-readable delta?
            # Would be nice to break this into business days too
            # time = bug.last_change_time.value
            # converted = datetime.datetime.strptime(time, "%Y%m%dT%H:%M:%S")
            # print('Last changed: %s' % converted)
            print('Action: %s' % find_action(bug))
            print('')
