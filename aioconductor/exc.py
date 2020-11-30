class ComponentError(Exception):
    """Base class for component errors"""


class CircularDependencyError(ComponentError):
    """
    Circular Dependency Error

    The exception is raised during components setup process,
    when circular dependency (that might deadlock the process) is found.

    Arguments tuple of the exception contains whole chain of interdependent components.

    """
