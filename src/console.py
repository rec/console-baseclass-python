"""
.. module:: console
    :platform: Unix, Windows

.. moduleauthor:: Vegard Sandengen <vegardsandengen@gmail.com>

"""

class Display_Information(object):
    """This class is utilized to relay information flow throughout the program.

    Can be routed through either logfile and/or stdout.
    """

    def __init__(self):
        """
        Args:
            SUBMODULE SHIIIIT
        Returns:
            Nothing
        """
        pass

    def verbose(self, format, *args):
        """Outputs message to appropriate channels if enabled at initialization.


        Args:
            - format (string): Message to submit, with associated identifiers for argument inputs.
            - *args (): Arguments will be supplied to identifiers in *format* in-order.
                No sanity check is performed on relation with identifier and supplied argument.
        """
        pass

class Command(object):
    """Holds all information about an action, its available flags and associated methods.
    """

    def __init__(self):
        """
        Args:
            lol

        Returns:
            Nothing

        Raises:
            Nothing
        """


