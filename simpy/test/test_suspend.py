"""
Tests for suspend/resume.

"""
import pytest


def test_suspend_resume(sim):
    """If a process passivates itself, it will no longer get active by
    itself but needs to be reactivated by another process (in contrast
    to interrupts, where the interrupt may or may not occur).

    """
    def sleeper(context):
        yield context.suspend()
        assert context.now == 10

    def alarm(context, sleeper):
        yield context.hold(10)
        sleeper.resume()

    sleeper = sim.start(sleeper)
    sim.start(alarm, sleeper)
    sim.simulate()


def test_illegal_suspend(sim):
    """Deny suspension if a process forgot to yield a "hold()"."""
    def pem(context):
        context.hold(1)
        yield context.suspend()

    sim.start(pem)
    pytest.raises(RuntimeError, sim.simulate)


def test_resume_before_start(sim):
    """A process must be started before any there can be any interaction.

    As a consequence you can't resume or interrupt a just started
    process as shown in this test. See :func:`test_immediate_resume` for
    the correct way to immediately resume a started process.

    """
    def child(ctx):
        yield ctx.hold(1)

    def root(ctx):
        c = ctx.start(child)
        c.resume()
        yield ctx.hold(1)

    try:
        sim.start(root)
        sim.simulate()
        pytest.fail()
    except RuntimeError as exc:
        assert exc.args[0] == 'Process(1, child) is not suspended.'


def test_immediate_resume(sim, log):
    """Check if a process can immediately be resumed."""
    def sleeper(context, log):
        yield context.suspend()
        log.append(context.now)

    def waker(context, sleeper_proc):
        sleeper_proc.resume()
        yield context.hold()

    sleeper_proc = sim.start(sleeper, log)
    sim.start(waker, sleeper_proc)
    sim.simulate()

    assert log == [0]


def test_resume_value(sim):
    """You can pass an additional *value* to *resume* which will be
    yielded back into the PEM of the resumed process. This is useful to
    implement some kinds of resources or other additions.

    See :class:`simpy.resources.Store` for an example.

    """
    def child(context, expected):
        value = yield context.suspend()
        assert value == expected

    def parent(context, value):
        child_proc = context.start(child, value)
        yield context.hold(1)
        child_proc.resume(value)

    sim.start(parent, 'ohai')
    sim.simulate()
