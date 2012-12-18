"""
.. module:: console
    :platform: Unix, Windows

.. moduleauthor:: Vegard Sandengen <vegardsandengen@gmail.com>

"""

import os
import errno
import time

#Flag definitions for Display_Information
DI_IGNORE = 0
DI_STDOUT = 1
DI_LOG = 2
DI_STDOUT_LOG = 3

DI_MIN_FLAG_LEVEL = DI_IGNORE
DI_MAX_FLAG_LEVEL = DI_STDOUT_LOG

class Display_Information(object):
    """This class is utilized to relay information flow throughout the program.

    There are three calls that support their own induvidual settings, they are:
        - :meth:`verbose` used to notify user of program flow.
        - :meth:`debug` used to notify user about debug information.
        - :meth:`vdebug` used to notify user with detailed debug information.
    When a call is made to one of these methods, they will determine where to relay the message
    based on their settings. The message can be routed to STDOUT, logfile or be ignored.
    """
    def __init__(self, DI_settings=None, log_fd=None, log_filename=None):
        """
        Kwargs:
            - DI_settings (dict): Determine where to route information relayed to respective
              calls. Expected keys are *'verbose'*, *'debug'* and *'verbosedebug'*. If additional
              keys are present, they will be ignored.
              Expected values are the DI flags
                0. **DI_IGNORE** Call has no effect.
                1. **DI_STDOUT** Message will be sent to STDOUT.
                2. **DI_LOG** Message will be sent to logfile.
                3. **DI_STDOUT_LOG** Message will be sent to both STDOUT and logfile
              Default behaviour is to **DI_IGNORE** everything.
            - log_fd (file): File descriptor that will be used to append log messages.
              If no file descriptor is supplied, one will be created at initialization.
            - log_filename (string): Prefix in log filename. Has no effect if log_fd is supplied.
              Default name is 'CONSOLE'.

        Attribute:
            - self.fd (file): Holds filedescriptor to logfile
            - self.display_information_settings (dict): Holds the current settings for all modes.
              Identical to the expected structure of supplied argument DI_settings.

        Expected DI_settings would look something like:
        {'v':DI_STDOUT, 'd':DI_LOG, 'vd':DI_STDOUT_LOG}

        Raises:
            OSError, TypeError, AttributeError
        """

        try:
            os.makedirs('logs')
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

        if log_fd:
            if not isinstance(log_fd, file):
                raise TypeError("Invalid argument 'log_fd'. Must be of type 'file'")
            self.fd = log_fd
        else:
            if log_filename == None:
                filename = "CONSOLE"
            else:
                filename = log_filename

            filename += "["+str(time.asctime())+"]"
            try:
                self.fd = open('./logs/'+filename, 'w')
            except:
                print "ERROR: [Display_Information: __init__] Failed to open logfile: "+filename
                raise

        #Create delimiters for all supported settings, initializing them to false
        supported_settings = ['verbose', 'debug', 'verbosedebug']
        self.display_information_settings = {}
        for setting in supported_settings:
            self.display_information_settings[setting] = DI_IGNORE

        if DI_settings == None:
            return
        if not isinstance(DI_settings, dict):
            raise TypeError("Invalid argument 'DI_settings'. Must be of type 'dict'")

        for (setting, DI_level) in DI_settings.items():
            if setting in supported_settings:
                if not isinstance(DI_level, int):
                    raise TypeError("Invalid value argument to dict key '"+setting+
                        "'. Value received is '"+DI_level+"', expected type 'int'."+
                        " Use associated DI_ flags to assign value.")
                if DI_level < DI_MIN_FLAG_LEVEL or DI_level > DI_MAX_FLAG_LEVEL:
                    raise AttributeError("Invalid value range. Unknown flag value '"+
                        str(DI_level)+ "' for key '"+setting+"'.")

                self.display_information_settings[setting] = DI_level

    def __clean__(self):
        """Cleanup resources allocated within this object.
        """
        if self.fd:
            if isinstance(self.fd, file):
                self.fd.close()

    def verbose(self, format, *args):
        """Outputs the supplied message to the appropriate channel spesified at initialization.
        The **'verbose'** setting determines actions of this call.

        Args:
            - format (string): Message to submit, with associated identifiers for argument inputs.
            - *args (): Arguments will be supplied to identifiers in *format* in-order.
        No sanity check is performed on relation between identifier and supplied argument.
        """
        tmp = format % args
        display = "%s\n" % tmp
        self._assistant_information_relay(display, self.display_information_settings['verbose'])

    def debug(self, format, *args):
        """Outputs the supplied message to the appropriate channel spesified at initialization.
        The **'debug'** setting determines actions of this call

        Args:
            - format (string): Message to submit, with associated identifiers for argument inputs.
            - *args (): Arguments will be supplied to identifiers in *format* in-order.
        No sanity check is performed on relation between identifier and supplied argument.
        """
        display = self._assistant_debug(format, *args)
        self._assistant_information_relay(display, self.display_information_settings['debug'])

    def vdebug(self, format, *args):
        """Outputs the supplied message to the appropriate channe spesified at initialization.
        The **'verbosedebug'** setting determines actions of this call.

        Args:
            - format (string): Message to submit, with associated identifiers for argument inputs.
            - *args (): Arguments will be supplied to identifiers in *format* in-order.
        No sanity check is performed on relation between identifier and supplied argument.
        """
        display = self._assistant_debug(format, *args)
        self._assistant_information_relay(display,
                self.display_information_settings['verbosedebug'])

    def _assistant_debug(self, format, *args):
        """Perform the formating of our message for the debug calls (debug / vdebug).
        """
        import inspect
        import threading

        msg = format % args
        display = "[%s: (%s)]: %s\n"% (threading.current_thread().name, inspect.stack()[2][3],msg)
        return display

    def _assistant_information_relay(self, msg, DI_level):
        """Write the message to the output levels determined by the DI_level
        """
        import sys

        if DI_level == DI_IGNORE:
            return

        if DI_level == DI_STDOUT or DI_level == DI_STDOUT_LOG:
            sys.stdout.write(msg)

        if DI_level == DI_LOG or DI_level == DI_STDOUT_LOG:
            self.fd.write(msg)



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

def test(i):
    i.debug('shiiit')
    i.vdebug("omfg loog my arse!")
    i.verbose("hah!")

if __name__ == '__main__':
    DI_settings = {'verbose':DI_STDOUT_LOG, 'debug':DI_STDOUT, 'verbosedebug':DI_STDOUT_LOG}
    i = Display_Information(DI_settings)
    i.verbose("i testing verbose")
