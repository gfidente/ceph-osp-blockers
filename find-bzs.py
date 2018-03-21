#!/usr/bin/env python
from bugzilla import Bugzilla
from bugzilla.bug import Bug
BZ_URL = 'bugzilla.redhat.com'

OSP_TRACKER = 1548353  # OSP 13 tracker
# OSP_TRACKER = 1553640  # OSP 14 tracker


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


def query_params():
    """ Return a dict of basic Bugzilla search parameters. """
    params = {
        'include_fields': ['id', 'summary', 'status'],
        'f1': 'blocked',
        'o1': 'equals',
        'v1': OSP_TRACKER,
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


if __name__ == '__main__':
    payload = query_params()
    bugs = search(payload)
    print('Found %d bugs blocking %s' % (len(bugs), OSP_TRACKER))

    sorted_bugs = sorted(bugs, key=sort_by_status)

    for bug in sorted_bugs:
        print('https://bugzilla.redhat.com/%d - %s - %s' % (bug.id, bug.status, bug.summary))
