"""
Author: Matt Christie, 2014-2016

Tools for output from programs.
"""

from sys import stdout, stderr
import datetime as dt
import time

_std_man = lambda data: True
_std_state = lambda data, state: {'data': data}

class OutputManager(object):
    """Manage a stream of output."""
    
    def __init__(self, out=stdout,
                 manager={'write': _std_man, 'flush': _std_man},
                 state={'write': {}, 'flush': {}},
                 assign_state={'write': _std_state, 'flush': _std_state}):
        self.out = out
        self.manager = manager
        self.state = state
        self.assign_state = assign_state
    
    def update_state(self, action, data):
        """Update the manager's info on an action."""
        self.state[action] = self.assign_state[action](data, self.state[action])
    
    def approves(self, action):
        """Determine if the manager approves of an action."""
        return self.manager[action](**self.state[action])

    def write(self, data):
        """Write data to the manager."""
        self.update_state('write', data)
        if self.approves('write'):
            self.out.write(data)
        self.update_state('flush', data)
        if self.approves('flush'):
            self.out.flush()


class ProgressCounter(object):
    """Count the progress of a task, displaying it with a simple load bar."""
    
    def __init__(self, terminal_width, out=OutputManager()):
        self.terminal_width = float(terminal_width)
        self.out = out
    
    def start_task(self, task_len):
        """Begin a task."""
        self.i = 0
        self.dot_goal = 1
        self.task_len = float(task_len)
    
    def count(self):
        """Count/register an accomplishment."""
        self.i += 1
        if self.i / self.task_len > self.dot_goal / self.terminal_width:
            self.out.write('.')
            self.dot_goal += 1
    
    def end(self):
        """Register that the task has completed."""
        self.out.write('\n')


class ProgressReporter(object):
    """Report progress made in a program."""
    
    def __init__(self, interval, content_seed, reporter, updater,
                 out=OutputManager(out=stderr)):
        self.interval = interval
        self.content = content_seed
        self.reporter = reporter
        self.updater = updater
        self.out = out
        self.marktime = time.time()
    
    def update(self, content):
        """Update progress."""
        self.content = self.updater(self.content, content)
    
    def report(self, content):
        """Report progress."""
        self.update(content)
        curtime = time.time()
        if curtime - self.marktime > self.interval:
            self.out.write(self.reporter(self.content))
            self.marktime = time.time()

    def end(self):
        self.out.write('\n')


class ProgressTallier(ProgressReporter):
    """Keep a running count of items handled in a program."""
    
    def __init__(self, interval, content_seed, out=OutputManager(out=stderr)):
    
        def reporter(count):
            now = dt.datetime.now()
            date = now.date().isoformat()
            time_ = now.time().isoformat()
            return "%s %s Handled: %s\n" % (date, time_, count)
        
        def updater(total, count):
            return total + count
        
        ProgressReporter.__init__(self, interval, content_seed, reporter, updater, out=out)


def notify_now(msg):
    """Send message with current timestamp to stderr."""
    now = dt.datetime.now()
    stderr.write("%s %s\n" % (now, msg))
    stderr.flush()







