"""
Verify UI Mode Stack architecture on Pico 2W.
"""
import sys
import os
import time

# Tiny Test Runner
def assert_equal(a, b, msg=""):
    if a != b:
        print(f"FAIL: {msg} | Expected {b}, got {a}")
        raise AssertionError(f"{a} != {b}")

def assert_true(cond, msg=""):
    if not cond:
        print(f"FAIL: {msg}")
        raise AssertionError("Condition failed")

# Mock hardware if missing (for robust testing)
try:
    import machine
    import framebuf
    import ds323x
except ImportError:
    print("Running in simulated environment (host)")
    class Mock: pass
    sys.modules['machine'] = Mock()
    sys.modules['framebuf'] = Mock()
    sys.modules['ds323x'] = Mock()

# Mock other dependencies to avoid ImportErrors
sys.modules['propagate'] = MagicMock() if 'MagicMock' in globals() else type('Mock', (object,), {'MicroSGP4': None})
sys.modules['sgp4'] = MagicMock() if 'MagicMock' in globals() else type('Mock', (object,), {'SGP4': None})
sys.modules['satellite_catalog'] = MagicMock() if 'MagicMock' in globals() else type('Mock', (object,), {'get_satellite_count': lambda: 0})
sys.modules['networking'] = MagicMock() if 'MagicMock' in globals() else type('Mock', (object,), {})
sys.modules['tle_fetch'] = MagicMock() if 'MagicMock' in globals() else type('Mock', (object,), {})
sys.modules['input_utils'] = MagicMock() if 'MagicMock' in globals() else type('Mock', (object,), {'normalize_encoder_delta': lambda d: d, 'NudgeManager': lambda *a,**k: type('NM',(),{'get_delta':lambda s,d:d})()})

# Import System under Test
import orb_globals as g
import modes
import orb_utils

# Shim orb_utils to avoid hardware crashes during test
orb_utils.load_state = lambda: {}
# Keep real get_timestamp if possible, else mock
if not hasattr(orb_utils, 'get_timestamp'):
    orb_utils.get_timestamp = lambda: 1700000000

print("--- Starting Mode Stack Verification ---")

class MockMode(modes.Mode):
    def __init__(self, name="Mock"):
        super().__init__()
        self.name = name
        self.entered = False
        self.exited = False
        self.paused = False
        self.resumed = False
        self.updated = False
        self.rendered = False
        
    def enter(self): self.entered = True
    def exit(self): self.exited = True
    def on_pause(self): self.paused = True
    def on_resume(self): self.resumed = True
    def update(self, dt): self.updated = True
    def render(self, disp): self.rendered = True

class MockRootMode(MockMode):
    def __init__(self, name="Root"):
        super().__init__(name)
        self.bg_updated = False
        
    def update_background(self, dt):
        self.bg_updated = True
        
    def update(self, dt):
        self.update_background(dt)
        self.updated = True

def test_push_pop():
    print("Test: Push/Pop")
    stack = modes.ModeStack()
    g.ui = stack
    
    root = MockMode("Root")
    stack.push(root)
    
    assert_equal(len(stack.stack), 1, "Stack len 1")
    assert_true(root.entered, "Root entered")
    assert_equal(stack.current, root, "Current is root")
    
    # Push child
    child = MockMode("Child")
    stack.push(child)
    
    assert_equal(len(stack.stack), 2, "Stack len 2")
    assert_true(child.entered, "Child entered")
    assert_true(root.paused, "Root paused")
    assert_equal(stack.current, child, "Current is child")
    
    # Pop child
    stack.pop()
    
    assert_equal(len(stack.stack), 1, "Stack len 1 after pop")
    assert_true(child.exited, "Child exited")
    assert_true(root.resumed, "Root resumed")
    assert_equal(stack.current, root, "Current is root")
    
    # Try pop root (should fail)
    stack.pop()
    assert_equal(len(stack.stack), 1, "Root cannot be popped")
    print("PASS")

def test_set_root():
    print("Test: Set Root")
    stack = modes.ModeStack()
    m1 = MockMode("OldRoot")
    stack.push(m1)
    m2 = MockMode("NewRoot")
    
    stack.set_root(m2)
    
    assert_equal(len(stack.stack), 1, "Stack cleared")
    assert_true(m1.exited, "Old root exited")
    assert_true(m2.entered, "New root entered")
    assert_equal(stack.current, m2, "New root current")
    print("PASS")

def test_update_logic():
    print("Test: Update Logic")
    stack = modes.ModeStack()
    root = MockRootMode("Root")
    child = MockMode("Child")
    
    # Setup stack: [Root, Child]
    stack.stack = [root, child]
    
    # Update stack
    stack.update(100)
    
    # Root BG should update (because it has update_background)
    # ModeStack.update manual check:
    # if len > 1: stack[0].update_background()
    assert_true(root.bg_updated, "Root background updated")
    assert_false(root.updated, "Root main update skipped") # Helper needed
    
    # Child (active) should update
    assert_true(child.updated, "Child updated")
    print("PASS")

def assert_false(cond, msg=""):
    if cond:
        print(f"FAIL: {msg}")
        raise AssertionError("Condition failed (expected False)")

def test_handle_input():
    print("Test: Handle Input")
    stack = modes.ModeStack()
    root = MockMode("Root")
    stack.push(root)
    
    # Inject method
    root.on_confirm_called = False
    def confirm_cb(): root.on_confirm_called = True
    root.on_confirm = confirm_cb
    
    stack.handle_input("CONFIRM")
    assert_true(root.on_confirm_called, "Root confirm called")
    
    print("PASS")

def run_tests():
    try:
        test_push_pop()
        test_set_root()
        test_update_logic()
        test_handle_input()
        print("\nALL TESTS PASSED")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import sys
        sys.print_exception(e)

if __name__ == '__main__':
    run_tests()
