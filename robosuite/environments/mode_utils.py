from typing import List
from dataclasses import dataclass, field
from operator import attrgetter
import inspect


@dataclass(order=True)
class Mode:
    name: str = None
    priority: int = 0 # to allow mode activation not being mutually exclusive
    activated: bool = False

    sort_index: int = field(init=False, repr=False)

    @classmethod
    def from_dict(cls, **kwargs):
        return cls(**{
            k: v for k, v in kwargs.items()
            if k in inspect.signature(cls).parameters
        })

    def __post_init__(self):
        self._set_custom()
        self.sort_index = self.priority

    def _set_custom(self):
        raise NotImplementedError

    def __repr__(self):
        return (f'{self.__class__.__name__}(name={self.name}, priority={self.priority}, activated={self.activated})')


@dataclass(order=True)
class FreeMode(Mode):
    name: str = "free"

    def _set_custom(self):
        self.activated = True


@dataclass(order=True)
class SuccessMode(Mode):
    name: str = "success"
    priority: int = 1e10 # default to the highest priority for checking
    success: bool = False

    def _set_custom(self):
        self.activated = self.success


@dataclass(eq=True)
class Transition():
    inp: Mode
    out: Mode

    def __eq__(self, other):
        return (self.inp.name == other.inp.name) and (self.out.name == other.out.name)


class ModeTracker:
    def __init__(self, env):
        self.env = env
        assert hasattr(env, "POSSIBLE_TRANSITIONS"), "Require environment with definition of POSSIBLE_TRANSITIONS"

        self.reset()

    def reset(self):
        self.mode_seq = []

    def append_mode(self, mode=None):
        if mode is None:
            mode = self.env.get_current_mode()
        self.mode_seq.append(mode)

    def check_transitions(self, return_per_transition_valid=False):
        possible_transitions = self.env.POSSIBLE_TRANSITIONS

        is_valid = []
        for i in range(len(self.mode_seq) - 1):
            prev_mode = self.mode_seq[i - 1]
            curr_mode = self.mode_seq[i]
            transition = Transition(inp=prev_mode, out=curr_mode)
            is_valid.append(transition in possible_transitions)
        
        if return_per_transition_valid:
            return is_valid
        else:
            return all(is_valid)

    @property
    def latest_mode(self):
        return self.mode_seq[-1] if len(self.mode_seq) > 0 else None


def validify_possible_modes_cls(possible_mode_cls: List[Mode]):
    priority_list = [v.priority for v in possible_mode_cls]
    name_list = [v.name for v in possible_mode_cls]
    assert len(set(priority_list)) == len(priority_list), f"Priorities are not unique in {name_list}"


def get_single_mode(possible_modes: List[Mode]):
    activated_modes = [v for v in possible_modes if v.activated]
    return max(activated_modes, key=attrgetter('priority'))


def get_default_possible_transitions(ordered_possible_modes: List[Mode]):
    possible_transitions = []

    # self-transition
    for i in range(len(ordered_possible_modes)):
        possible_transitions.append(Transition(
            inp=ordered_possible_modes[i](),
            out=ordered_possible_modes[i](),
        ))

    # demonstration
    for i in range(len(ordered_possible_modes) - 1):
        possible_transitions.append(Transition(
            inp=ordered_possible_modes[i](),
            out=ordered_possible_modes[i + 1](),
        ))

    # reversability
    for i in range(len(ordered_possible_modes) - 1):
        possible_transitions.append(Transition(
            inp=ordered_possible_modes[i + 1](),
            out=ordered_possible_modes[i](),
        ))

    # restartability
    for i in range(len(ordered_possible_modes) - 2):
        possible_transitions.append(Transition(
            inp=ordered_possible_modes[i + 2](),
            out=ordered_possible_modes[0](),
        ))

    return possible_transitions
