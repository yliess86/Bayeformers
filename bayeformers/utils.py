import torch
import torch.nn as nn

import inspect

from bayeformers.nn import AVAILABLE_LAYERS
from bayeformers.nn.model import Model

"""
    Look for the corresponding class type in the available layers
"""


def _get_bayesian_class_correspondance(module: type) -> type:
    for layer_class in AVAILABLE_LAYERS:
        if layer_class.__name__ == module.__name__:
            return layer_class
    return None


def has_candidate_replacement(module: type) -> bool:
    return _get_bayesian_class_correspondance(module) != None


"""
    Takes a toch module and return the corresponding, initialized, bayformers Model
"""


def get_bayesian_replacement_instance(module: nn.modules.Module) -> Model:
    bayesian_class: type = _get_bayesian_class_correspondance(type(module))
    if not bayesian_class:
        raise Exception(
            f"Layer {str(module)} has no Bayesian correspondance in Bayeformers"
        )

    constructor_args = {}  # what we will call bayesian_class.__init__ with

    args = inspect.getfullargspec(module.__init__)
    for arg in args.args[1:]:  # skip self
        try:
            constructor_args[arg] = getattr(module, arg)
        except AttributeError:
            raise Exception(f"Internal attribute {arg} nor found in {module}")

    # TODO Gaussian initalization method choice goes here
    bayesian_module = bayesian_class(**constructor_args)
    # TODO Parameters initalization goes here

    return bayesian_module


"""
    Recursively look for modules that can be replaced in the model and swap 
    them with the bayeformers corresponding bayesian module
"""


def replace_modules(net: nn.Module) -> None:
    for n, c in net.named_children():
        if has_candidate_replacement(type(c)):
            setattr(net, n, get_bayesian_replacement_instance(c))
        replace_modules(c)
