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


FLAG_INPUT_IGNORE = 0
FLAG_INPUT_STR = 1
FLAG_INPUT_INT = 2
FLAG_INPUT_FLOAT = 3

class InputError(Exception):
    """Exception raised when terminal input does not match expected input,
    eg. flag --example require an integer input(FLAG_INPUT_INT), but a string is supplied.
    """
    def __init__(self, message, *args):
        msg = message % args
        Exception.__init__(self, msg)


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

class _Console_Parser(object):
    """Internal
    """
    def __init__(self):
        """
        Internal structure help parse either a list of strings or a string.
        The string will be broken into tokens. The list will remove the first element
        if it equals sys.argv[0] (the program name).

        Modules:
            sys
        """
        import sys
        self.program_name = sys.argv[0]    #sys.argv[0]
        self.active_flags = None
        self.additional_args = None

    def _precheck_input(self, input):
        """Sanity check input, always ordering it to a list of arguments without program name
        """
        if isinstance(input, list):
            if input[0] == self.program_name:
                return input[1:]
            else:
                return input
        if isinstance(input, str):
            return input.split()

        raise TypeError("Input is not of type 'str' or 'list'")

    def get_active_flags(self):
        """*getter* function to retrieve all active flags.
        Returns:
            - None if no command is parsed with :meth:`parse_line`
            - Empty list ([]) if no flags where present for last parsed line.
            - List filled with dictionaries, {'longf':(str), 'description':(str), 'input':(),
              'method':(callable method)}
        """
        return self.active_flags

    def get_additional_args(self):
        """*getter* function to retrieve all additional arguments.
        Returns:
            - None if no command is parsed with :meth:`parse_line`
            - Emptry list ([]) if no additional arguments where present last parsed line.
            - List filled with all unaccounted for arguments (eg, did not match any flags (and
              their required input) from :class:`Command` defined with :meth:`Command.add_flag`
              (which is used by :meth:`Console.add_flag`)).
        """
        return self.additional_args

    def parse_line(self, command, input, is_command=True):
        """input can be either string or a list
        """
        self.active_flags = []
        self.additional_args = []
        inputlist = self._precheck_input(input)

        if is_command:
            inputlist = inputlist[1:]

        index = 0
        list_length = len(inputlist)
        flag_name = None
        while index < len(inputlist):
            found_active_flag = False
            for map in command.available_flags:
                if inputlist[index] == map["longf"]:
                    found_active_flag = True
                    flag_name = inputlist[index]
                    break
                if inputlist[index] == map["shortf"]:
                    found_active_flag = True
                    flag_name = inputlist[index]
                    break

            if found_active_flag:
                input_value = None
                if map["input"] > FLAG_INPUT_IGNORE:
                    if (index + 1 >= list_length):
                        raise InputError("Missing input for flag '%s'", flag_name)

                    index += 1
                    if map["input"] == FLAG_INPUT_STR:
                        input_value = str(inputlist[index])
                    elif map["input"] == FLAG_INPUT_INT:
                        try:
                            input_value = int(inputlist[index])
                        except ValueError as e:
                            raise InputError("Invalid input '%s' for flag '%s'. Expected int",
                                    inputlist[index], flag_name)
                    elif map["input"] == FLAG_INPUT_FLOAT:
                        try:
                            input_value = float(inputlist[index])
                        except ValueError as e:
                            raise InputError("Invalid input '%s' for flag '%s'. Expected float",
                                    inputlist[index], flag_name)

                flag_dict = {'longf':map["longf"], 'description':map["description"],
                        'input':input_value, 'method':map["method"]}
                #Sanity check if we are to add this flag dict or not: May already be present
                for added_dict in self.active_flags:
                    if added_dict["longf"] == flag_dict["longf"]:
                        self.active_flags.remove(added_dict)
                        break
                self.active_flags.append(flag_dict)
            else:
                self.additional_args.append(inputlist[index])
            index += 1

class Command(object):
    """Class to hold all vital information about a spesific command,
    with its defined flags etc
    """

    def __init__(self, command_name, method, description):
        """
        Args:
            - command_name (str): Name used in console to call upon this method.
            - method (callable method): Called upon when 'command_name' is entered into the
              running console.
            - description (str): Description of what the command does.

        Attributes:
            - self.command_name (str): Name of command.
            - self.method (callable method): Method to be executed for current command.
            - self.description (str): Description of what the command does.
            - self.available_flags (list): All flags added to this command.

        The *available_flags* attribute dictionary is formated as follows:
        {'longf':{'shortf':(str), 'description:(str), 'input':(), 'method':(callable method)}}
        with respect to the attributes submitted in :meth:`add_flag`.

        Raises:
            TypeError
        """
        if hasattr(method, '__call__') == False:
            raise TypeError("'method' argument is not a callable")

        if isinstance(description, str) == False:
            raise TypeError("'description' argument is not of type string")

        self.command_name = command_name
        self.method = method
        self.description = description
        self.available_flags = []

        self.add_flag(longf="--help", shortf="-h", description="Display available flag options",
                method=self._command_help)


    def add_flag(self, longf, shortf=None, description=None, input=FLAG_INPUT_IGNORE, method=None):
        """
        See description of :meth:`Console.add_flag`
        """

        if method != None:
            if hasattr(method, '__call__') == False:
                raise TypeError("'method' argument is not a callable")
        if description != None:
            if isinstance(description, str) == False:
                raise TypeError("'name' argument is not a string")
        if shortf != None and not isinstance(shortf, str):
            raise TypeError("'shortf' argument is not a string")
        if isinstance(longf, str) == False:
            raise TypeError("'longf' argument is not a string")
        if input != None and not isinstance(input, int):
            raise TypeError("'input' argument is not a integer")

        flag_dict = {'longf':longf, 'shortf':shortf, 'description':description,
                'input':input,'method':method}
        self.available_flags.append(flag_dict)


    def _command_help(self):
        """
            Internal command called whenever the HELP flag is
            issued for a command
        """
        print_flags(self.available_flags)

class Console(Display_Information):
    """
    long ass rant
    """
    def __init__(self):
        """
            --log
        Modules:
            sys

        Raises:
            InputError
        """
        import sys

        self.available_commands
        self.terminal = []
        self.terminal_active_flags = []
        self.terminal_additional_args = []
        #Attributes available in flag/command supplied methods
        self.current_command_active_flags = []
        self.current_command_additional_args = []
        self.current_command_name
        #Attributes available only within a flag handler
        self.current_flag_name
        self.current_flag_input

        self.terminal = Command("Terminal", self._dummy, "Terminal - represents startup")


        self.console_init()

        #Parse input, divide into flags. Execute shit
        parser = _Console_Parser()
        parser.parse_line(self.terminal, sys.argv, False)
        self.terminal_active_flags = parser.get_active_flags()
        self.terminal_additional_args = parser.get_additional_args()

        do_exit = False
        log_level = DI_STDOUT
        DI_settings = {}
        #Detect if help was one of them
        for map in self.terminal_active_flags:
            flag = map["longf"]
            if flag == "--help":
                do_exit = True
            elif flag == "--log":
                log_level = DI_LOG
            elif flag == "--log-stdout"
                log_level = DI_STDOUT_LOG
            elif flag == "--verbose":
                DI_settings["verbose"] = DI_STDOUT
            elif flag == "--debug":
                DI_settings["debug"] = DI_STDOUT
            elif flag == "--verbose-debug":
                DI_settings["verbosedebug"] = DI_STDOUT

        if do_exit
            map["method"](self.terminal.available_flags)
            sys.exit()

        for (key, value) in DI_settings:
            DI_settings["key"] = log_level
        Display_Information.__init__(self, DI_settings)

        #Add default commands
        self.console_add_command("exit", self._dummy, "Exit the console.")
        self.console_add_command("help", self._console_help, "Print all available commands")

    def add_flag(self, longf, shortf=None, description=None, input=FLAG_INPUT_IGNORE, method=None):
        """
        Add a flag option to current command.

        args:
            - longf (str): *long* flag name with two leading dashes used to indicate
              the activation of this flag option.
        Kwargs:
            - shortf (str): *short* flag name with one leading dash and only one character,
              used to indicate the activation of this flag. This is a shortcut option of the
              required **longf** argument.
            - description (str): Short description of what this flag does. This information
              is available when the --help flag is present.
            - input (int): Indicate that this flag option requires additional input directly
              succeeding the flag option. The *int* value supplied is one of the following
              defined flags:
                0. **FLAG_INPUT_IGNORE** No input is expected. This is the default option.
                1. **FLAG_INPUT_STR** *string* input is expected.
                2. **FLAG_INPUT_INT** *integer* input is expected.
                3. **FLAG_INPUT_FLOAT** *float* input is expected.
            - method (callable method): If present, this method will be executed once the
              flag option is present.
        """
        self.terminal.add_flag(longf, shortf, description, input, method)

    def console_add_command(self, name, method, description)
        """
        """
        raise NotImplementedError

    def console_init(self):
        """Called before terminal args are parsed. This allows for custom flags to be
        added by overriding this method. Add flag options by calling :meth:`Console.add_flag`.
        """
        pass

    def _dummy(self):
        pass

def test(i):
    i.debug('shiiit')
    i.vdebug("omfg loog my arse!")
    i.verbose("hah!")

def parser_test():
    #create a command with flags
    command = Command("lol", test, "lol")
    command.add_flag("--test", input=FLAG_INPUT_INT)
    command.add_flag("--rofl", input=FLAG_INPUT_STR)
    command.add_flag("--kek", shortf="-f", input=FLAG_INPUT_FLOAT)


    mylist = ['console.py','first', 'second', 'third']
    mystring = "command --test 5 --rompe --kek 2 -f 20 --strict test my arse"
    parser = _Console_Parser()
    parser.parse_line(command, mystring, is_command=False)
    print parser.active_flags
    print parser.additional_args

if __name__ == '__main__':
    DI_settings = {'verbose':DI_STDOUT_LOG, 'debug':DI_STDOUT, 'verbosedebug':DI_STDOUT_LOG}
    i = Display_Information(DI_settings)

    parser_test()
