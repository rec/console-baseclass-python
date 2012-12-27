"""
.. module:: console
    :platform: Unix, Windows

.. moduleauthor:: Vegard Sandengen <vegardsandengen@gmail.com>

"""

import errno
import time
import threading

#Flag definitions for Display_Information
DI_IGNORE = 0
DI_STDOUT = 1
DI_LOG = 2
DI_STDOUT_LOG = 3

DI_CONSOLE_IGNORE = 0
DI_CONSOLE_INHERIT = 1

DI_MIN_FLAG_LEVEL = DI_IGNORE
DI_MAX_FLAG_LEVEL = DI_STDOUT_LOG


FLAG_INPUT_IGNORE = 0
FLAG_INPUT_STR = 1
FLAG_INPUT_INT = 2
FLAG_INPUT_FLOAT = 3

STR_FLAG_INPUT_IGNORE = "ignore"
STR_FLAG_INPUT_STR = "str"
STR_FLAG_INPUT_INT = "int"
STR_FLAG_INPUT_FLOAT = "float"

class Enum(set):
    """Implements a pythonic way to enumerate items to strings.
    Usage: ANIMAL = Enum(["DOG", "CAT"])
    results in a call to ANIMAL.DOG equals "DOG".
    """
    def __getattr__(self, name):
        if name in self:
            return name
        raise AttributeError

"""
All supported keyboard comparisons
"""
KEY = Enum(["ARROW_UP", "ARROW_DOWN", "ARROW_LEFT", "ARROW_RIGHT", "ENTER", "BACKSPACE",
        "END_OF_TEXT", "END_OF_TRANSMISSION"])


class InputError(Exception):
    """Exception raised when terminal input does not match expected input,
    eg. flag --example require an integer input(FLAG_INPUT_INT), but a string is supplied.
    """
    def __init__(self, message, *args):
        msg = message % args
        Exception.__init__(self, msg)

class CallError(Exception):
    """Exception raised when a programming mistake has happend: If for instance a method
    that should only be executed once is called twise, this exception will be raised.
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
    def __init__(self, DI_settings=None):
        """
        Kwargs:
            - DI_settings (dict): Holds all settings available for this class.
              The settings can be viewed as two parts, one which determine where to route
              information relayed to respective calls.
              Expected keys for the relay of information are *'verbose'*, *'debug'* and
              *'verbosedebug'*. Expected values are the DI flags
                0. **DI_IGNORE** Call has no effect.
                1. **DI_STDOUT** Message will be sent to STDOUT.
                2. **DI_LOG** Message will be sent to logfile.
                3. **DI_STDOUT_LOG** Message will be sent to both STDOUT and logfile
              Default behaviour is to **DI_IGNORE** everything.
              Expected keys for additional settigs are *'log_fd'* and *'log_filename'*.
              Expected values for keys are
                - *'log_fd'*: **file** descriptor that will be used to append log messages.
                  If no file descriptor is supplied, one will be created at initialization.
                - *'log_filename'*: **str** prefix in log filename. Has no effect if log_fd
                  is supplied. Default name is 'CONSOLE'.
              If additional keys are present, they will be ignored.

        Attribute:
            - self.fd (file): Holds filedescriptor to logfile
            - self.display_information_settings (dict): Holds the current settings for all modes.
              Identical to the expected structure of supplied argument DI_settings.

        Expected DI_settings would look something like:
        {'v':DI_STDOUT, 'd':DI_LOG, 'vd':DI_STDOUT_LOG, 'log_fd':(file), 'log_filename':(str)}

        Raises:
            OSError, TypeError, AttributeError

        Modules:
            os
        """
        """
        Internal Attributes:
            - self._init_completed (bool): Is utilized to sanity check calls to the
              information relay functions. This variable is initialized upon class init.
              If the information relay functions are called before initialization a CallError
              exception is raised. (May/will be convient in derived classes where this class
              has yet to be initialized)
        """
        import os

        self.display_information_settings = {}
        log_fd = None
        log_filename = None
        try:
            os.makedirs('logs')
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise


        if "log_fd" in DI_settings:
            log_fd = DI_settings["log_fd"]
        if "log_filename" in DI_settings:
            log_filename = DI_settings["log_filename"]
        if log_fd:
            if not isinstance(log_fd, file):
                raise TypeError("Invalid argument 'log_fd'. Must be of type 'file'")
            self.fd = log_fd
        else:
            if log_filename == None:
                self.filename = "CONSOLE"
            else:
                self.filename = log_filename
            self.display_information_settings['log_filename'] = self.filename

            self.filename += "["+str(time.asctime())+"]"
            self.fd = None  #Open it at runtime
        self.display_information_settings['log_fd'] = self.fd

        #Create delimiters for all supported settings, initializing them to false
        supported_settings = ['verbose', 'debug', 'verbosedebug']
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

        self._init_completed = True

    def clean(self):
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
        self._assistant_is_initialized()
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
        self._assistant_is_initialized()
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
        self._assistant_is_initialized()
        display = self._assistant_debug(format, *args)
        self._assistant_information_relay(display,
                self.display_information_settings['verbosedebug'])

    def _assistant_is_initialized(self):
        """Hack? to check if class is initialized. A CallError exception is raised if
        initialization is not completed.
        """
        if hasattr(self, '_init_completed'):
            return
        raise CallError("Display_Information not initialized. Programming Error.")

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
            if self.fd == None:
                try:
                    self.fd = open('./logs/'+self.filename, 'w')
                except:
                    print "ERROR: [Display_Information: __init__] Failed to open logfile: "+filename
                    raise
                self.display_information_settings['log_fd'] = self.fd
            self.fd.write(msg)

class Command(object):
    """Class to hold all vital information about a spesific command,
    with its defined flags etc
    """

    def __init__(self, command_name, method, description, usage=""):
        """
        Args:
            - command_name (str): Name used in console to call upon this method.
            - method (callable method): Called upon when 'command_name' is entered into the
              running console.
            - description (str): Description of what the command does.
            - usage (str): Description of expected (additional non-flag) arguments. Appended
              after *'Usage: self.command_name [--flag] '*.

        Attributes:
            - self.command_name (str): Name of command.
            - self.method (callable method): Method to be executed for current command.
            - self.description (str): Description of what the command does.
            - self.available_flags (list): All flags added to this command.
            - self.usage (str): Description of expected (additional) arguments custom for
              this particular command. Eg. *"path_to_dir(str) max_open_files(int)"*. This will
              be appended after *'Usage: self.command_name [--flags] '*
            - self.PHC (_Print_Help_Command object): Assistant class to print all help options.

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
        self.usage = ""
        self.PHC = _Print_Help_Command(self)

        self.add_flag(longf="help", shortf="h", description="Display available flag options",
                method=self._command_help)


    def add_flag(self, longf, shortf=None, description="", input=FLAG_INPUT_IGNORE, method=None):
        """Add a flag to the current command.
        See description of :meth:`Console.terminal_add_flag`
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

        if longf[:2] != "--":
            longf = "--"+longf
        if shortf != None and shortf[0] != '-':
            shortf = '-'+shortf
        if shortf != None and len(shortf) != 2:
            raise TypeError("'shortf' argument must be in form 'x' or '-x'")

        flag_dict = {'longf':longf, 'shortf':shortf, 'description':description,
                'input':input,'method':method}
        self.available_flags.append(flag_dict)


    def _command_help(self):
        """
            Internal command called whenever the HELP flag is
            issued for a command
        """
        self.PHC.print_flags()

class Console(Display_Information):
    """
    long ass rant
    """
    def __init__(self, DI_settings={}, disable_default_flags=False, disable_auto_process_flags=False):
        """
        Kwargs:
            - DI_settings (dict): May contain any of the key-value pairs parsed by
              :class:`Display_Information`. These values are overridden by terminal flags.
              This option can be utilized in the event that several *Display_Information* instances
              would like to log to the same file/outputlevel etc. These settings is stored
              in the (inheritted) attribute *self.display_information_settings* dictionary
              that contain information output level, log file descriptor and file prefix name.

            - disable_default_flags (bool): Determines whether or not all the default flags should
              be added to the terminal. If enabled (by default) the :class:`Display_Information`
              information methods will be fully available. If not, they will be disabled(Will
              be initialized to DI_IGNORE) and flags removed from terminal flag list.

            - disable_auto_process_flags (bool): Determines whether or not the Console
              initialization should parse terminal flags.
              If disabled, :class:`Display_Information` is left uninitialized
              and :meth:`terminal_process_flags` must be called manually. This option is
              convient if one wishes to utilize :meth:`terminal_quickadd_flags` without overriding
              :meth:`terminal_init` or does not require the full features of
              :meth:`terminal_add_flag`.

        Attributes (public):
            - self.terminal (Command object): Special case :class:`Command` object to represent
              the *terminal*.
            - self.terminal_active_flags (list): List of all flags matching available flags
              present on the *terminal* at program launch. Each list item is a dictionary on the
              form:
              {'longf':(str), 'description':(str), 'input':(int), 'method':(callable)}
              where *longf* is the unique flag identifier.
            - self.terminal_additional_args (list): List of all unaccounted for arguments on
              the *terminal* line at program launch.

        Attributes available in :class:`Command` activation handler method and
        :meth:`default_flag_handler`/supplied flag activation handler method:
            - self.current_command_active_flags (list): List of all flags matching available flags
              present at the *console* command launch. Each list item is a dictionary on the form:
              {'longf':(str), 'description':(str), 'input':(int), 'method':(callable)} where
              longf is the unique flag identifier.
            - self.current_command_additional_args (list): List of all unaccounted for arguments
              on the *console* command line.
            - self.current_command_name (str): Name of the command that activated this method.

        Attributes available in :meth:`default_flag_handler`/supplied flag activation handler
        method:
            - self.current_flag_name (str): Name of the flag (*longf*) that activated this method.
            - self.current_flag_input (): If flag option required input, this variable will hold
              that object converted to its intended object type (eg. *int* or *float*). If no
              option is expected, this attribute will be None.


        Modules:
            sys

        Raises:
            InputError, TypeError, OSError, AttributeError
        """
        """This docstring is not parsed by Sphinx.

        Private Attributes:
            - self._available_commands (list): List of all Command objects that is added to the
              *console*.
            - self._processed_flag_options (bool): Indicates whether or not the
              self._terminal_process_flags() function has been called. In other words, whether or
              not the terminal flags has been parsed and Display_Information has been initialized.
            - self._DI_settings (dict): Internal variable to pass initialized Display_Information
              settings through internal class methods. Holds the value of Console initialization
              parameter DI_settings.
        """

        import sys

        if not isinstance(DI_settings, dict):
            raise AttributeError("DI_settings not of type 'dict'")
        if not isinstance(disable_default_flags, bool):
            raise AttributeError("disable_default_flags not of type 'bool'")
        if not isinstance(disable_auto_process_flags, bool):
            raise AttributeError("disable_auto_process_flags not of type 'bool'")

        self._available_commands = []
        self.terminal = None
        self.terminal_active_flags = []
        self.terminal_additional_args = []
        self._processed_flag_options = False
        self._DI_settings = DI_settings
        #Attributes available in flag/command supplied methods
        self.current_command_active_flags = []
        self.current_command_additional_args = []
        self.current_command_name = None
        #Attributes available only within a flag handler
        self.current_flag_name = None
        self.current_flag_input = None

        self.terminal = Command(sys.argv[0], self._dummy, "Terminal - represents startup.")
        if not disable_default_flags:
            self._add_default_flags()
        self.terminal_init()

        if not disable_auto_process_flags:
            self._terminal_process_flags()

                #Add default commands
        self.console_add_command("exit", self._dummy, "Exit the console.")
        self.console_add_command("help", self._console_help, "Print all available commands.")

    def default_flag_handler(self):
        """Default flag handler invoked when no method is supplied to the flag option.
        This method functions for both the terminal and the console.
        Override this function if you want to handle all flags in one method.

        Available attributes:
            - self.current_command_active_flags (list): List of dictionaries holding all present
              flags when invoking this command.
            - self.current_command_additional_args (list): List of string objects, all unaccounted
              for tokens invoking this command.
            - self.current_command_name (str): *Command.command_name* that was invoked with
              the flag that called this method. For the terminal, this value is 'TERMINAL'.
            - self.current_flag_name (str): *longf* that called this method.
            - self.current_flag_input (): None if flag require no input. Object is converted to
              its expected object.
        """
        flag = self.current_flag_name
        self.debug("Executing flag '%s' default method handler. Input is '%s'", flag,
                str(self.current_flag_input))

    def console_cleanup(self):
        """Method is called when the in-program console initiated by :meth:`console_start`
        is terminating. Override this method to cleanup anything you may require.
        """
        pass

    def console_start(self, threaded=True, daemon=True):
        """Start the in-program console. This will run in the terminal where the program
        was initiated.

        Kwargs:
            - threaded (bool): Determine whether or not to start the console in a seperate thread.
              Doing so will continiue execution after this method is called.
            - daemon (bool): Determine whether or not the console running in a thread should
              behave like a daemon. A daemon operates just like a normal thread, but when the
              MainThread seizes execution, this thread will to. This option has no effect if
              the *threaded* argument is False.
        """

        program_console = Console_Program(self, self.console_cleanup,
                self.display_information_settings, threaded)
        if threaded:
            program_console.daemon = daemon
            program_console.start()
        else:
            program_console.run()

    def console_add_command(self, name, method, description, usage=""):
        """Creates a new in-console command.

        In order to add flag options to this newly created command, use :meth:`Command.add_flag`
        method on the returned object.

        Returns:
            :class:`Command`
        """

        command = Command(name, method, description, usage)
        self._available_commands.append(command)
        return command

    def terminal_init(self):
        """Called before terminal args are parsed. This allows for custom flags to be
        added by overriding this method. Add flag options by calling
        :meth:`Console.terminal_add_flag`.

        If Console is initialized with disable_auto_process_flags, you can add the flags
        after initialization and manually call :meth:`terminal_process_flags`. Be warned:
        :class:`Display_Information` is not initialized until flags are processed.
        """
        self.terminal.add_flag("--test", input=FLAG_INPUT_FLOAT)

    def terminal_add_flag(self, longf, shortf=None, description="", input=FLAG_INPUT_IGNORE, method=None):
        """
        Add a flag option to the terminal.

        Args:
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

        Raises:
            CallError
        """
        if self._processed_flag_options:
            raise CallError("Programming Error: Attempting to add a terminal flag after terminal "
                    "flags have been parsed. Adding terminal flags must be done within overidden "
                    "method terminal_init or Console must be initialized with "
                    "disable_auto_process_flags set to True. See documentation.")

        self.terminal.add_flag(longf, shortf, description, input, method)

    def terminal_quickadd_flags(self, longf_list, shortf_str=None):
        """
        Quick and dirty way to add terminal flags. Utilizeable in two cases:
            1. :meth:`terminal_init`
            2. If :meth:`Console` is initialized with *disable_auto_process_flags*, than this
               method can be called upon the :class:`Console` object and followed by a call to
               the parsing function :meth:`terminal_process_flags` when all flag options are
               added.

        Args:
            - longf_list (list): All list items must be of type 'string'. Each item correponds
              to one flag entry. The list item takes the form *"longflag=option"*, where
              *'longflag'* is the flag name and *'option'* is the input type.
                * *"ignore"* for **FLAG_INPUT_IGNORE**. This option *'=ignore'* may be left out of
                  string, as it is the default option. Eg. string only needs to be *"longflag"*.
                * *"float"* for **FLAG_INPUT_FLOAT**
                * *"str"* for **FLAG_INPUT_STR**
                * *"int"* for **FLAG_INPUT_INT**
        Kwargs:
            - shortf_str (str): a string of characters, at most *n* characters long where *n*
              is the number of list items in *'longf_list'*. Each characters represents
              the correponding longf **in-order** of apperance. If no short flag is desired, a
              questionmark (?) will place no short flag for the associated flag.
              Eg. "rs?o" would correspond to atleast 4 flags, but only 3 of them are assigned
              a short flag.

        No description will be given for the flag, and the :meth:`default_flag_handler` will
        be assigned as its activation method.

        Example:
            self.terminal_quickadd_opts(["radius=float", "show", "circles=int", "file"], "r?c")
        would produce the flags:
            - -r --radius [float]
            - --show
            - -c --circles [int]
            - --file

        .. note::
            This method should **ONLY** be utilized in the above mentioned cases. Failure to do
            so will result in an **CallError** exception.

        Raises:
            AttributeError, CallError
        """
        if not isinstance(longf_list, list):
            raise AttributeError("Argument 'longf_list' is not of type 'list'")
        if shortf_str and not isinstance(shortf_str, str):
            raise AttributeError("Argument 'shortf_str' is not of type 'string'")

        shortf_list = [None for x in xrange(len(longf_list))]
        if shortf_str != None:
            for i in xrange(len(shortf_str)):
                if shortf_str[i] != '?':
                    shortf_list[i] = shortf_str[i]
        i = 0
        for flag_string in longf_list:
            if not isinstance(flag_string, str):
                err_str = "List item in argument 'longf_list' is not of type 'string'"
                raise AttributeError(err_str)

            flag_list = flag_string.split("=")
            input_type = FLAG_INPUT_IGNORE
            if len(flag_list) == 2:
                option = flag_list[1].lower()
                if option == STR_FLAG_INPUT_STR:
                    input_type = FLAG_INPUT_STR
                elif option == STR_FLAG_INPUT_INT:
                    input_type = FLAG_INPUT_INT
                elif option == STR_FLAG_INPUT_FLOAT:
                    input_type = FLAG_INPUT_FLOAT

            self.terminal_add_flag(flag_list[0], shortf_list[i], input=input_type)
            i += 1

    def terminal_process_flags(self):
        """Attempts to process terminal flag options and initialize :class:`Display_Information`.
        This will fail if terminal flags have already been processed. This method is
        automatically called internally if :class:`Console` initialization parameter
        *disable_auto_process_flags* is not set.

        .. note::
            This method should **ONLY** be called when :class:`Console` is initialized with
            *disable_auto_process_flags*. If called after terminal flags have been processed,
            a **CallError** will be raised. Simailary if called twise.


        Raises:
            CallError
        """
        if self._processed_flag_options:
            raise CallError("Programming Error: Terminal has already parsed flag inputs. "
                "If you ment to call this method you probably need to initialize Console with "
                "disable_auto_process_flags")
        self._terminal_process_flags()

    def _terminal_process_flags(self):
        """
        Process the terminal input line and execute the methods associated with present flags

        Modules:
            sys
        """
        import sys
        self._processed_flag_options = True

        parser = _Console_Parser()
        parser.parse_line(self.terminal, sys.argv, False)
        self.terminal_active_flags = parser.get_active_flags()
        self.terminal_additional_args = parser.get_additional_args()


        def _update_active_DI(level):
            for map in self.terminal_active_flags:
                flag = map["longf"]
                if flag == "--verbose":
                    self._DI_settings["verbose"] = level
                elif flag == "--debug":
                    self._DI_settings["debug"] = level
                elif flag == "--verbose-debug":
                    self._DI_settings["verbosedebug"] = level

        do_exit = False
        exit_map = None
        log_level = DI_STDOUT
        for map in self.terminal_active_flags:
            flag = map["longf"]
            if flag == "--help":
                exit_map = map
                do_exit = True
            elif flag == "--log":
                _update_active_DI(DI_LOG)
            elif flag == "--log-stdout":
                _update_active_DI(DI_STDOUT_LOG)
            elif flag == "--verbose":
                self._DI_settings["verbose"] = DI_STDOUT
            elif flag == "--debug":
                self._DI_settings["debug"] = DI_STDOUT
            elif flag == "--verbose-debug":
                self._DI_settings["debug"] = DI_STDOUT
                self._DI_settings["verbosedebug"] = DI_STDOUT

        if do_exit:
            exit_map["method"]()
            sys.exit()

        Display_Information.__init__(self, self._DI_settings)

        #Call flags in order of apperance in string
        self.current_command_name = "TERMINAL"
        self.current_command_active_flags = self.terminal_active_flags
        self.current_command_additional_args = self.terminal_additional_args
        for map in self.terminal_active_flags:
            self.current_flag_name = map["longf"]
            self.current_flag_input = map["input"]
            if map["method"] == None:
                self.default_flag_handler()
            else:
                map["method"]()

    def _add_default_flags(self):
        """Assist function to add all default flags
        """
        self.terminal.add_flag("--log", "-l",
                "Route all -v, -d & -D print to logfile instead of STDOUT.")
        self.terminal.add_flag("--log-stdout", "-L",
                "Route all -v, -d & -D print to both logfile and STDOUT.")
        self.terminal.add_flag("--verbose", "-v", "Print detailed program flow to STDOUT.")
        self.terminal.add_flag("--debug", "-d",
                "Print debug information in program flow to STDOUT.")
        self.terminal.add_flag("--verbose-debug", "-D",
                "Print detailed debug information in program flow to STDOUT.")

    def _console_help(self):
        """Print all available commands from the console
        """
        print "IN CONSOLE HELP"

    def _dummy(self):
        pass

class Console_Program(threading.Thread, Display_Information):
    """
        Implements the in-program console loop.

        Parameters
        ----------
        @console_object             REQUIRED:
                                        OBJECT of class @Console. Pass along
                                            the instance of the console
        @cleanup                    OPTIONAL: default=None
                                        METHOD callable called when console
                                            terminates console activity.
        @settings                   OPTIONAL: Default=None
                                        DICTIONARY @_INFORMATION_SETTINGS
        @is_thread                  OPTIONAL: Default=True
                                        BOOL telling wheter or not this console
                                        is running as a thread or mainthread.

        Attributes
        ----------
        @self.console               OBJECT instance of @Console class.
                                        Equals @console_object.
        @self.cleanup               METHOD callable. Equals @cleanup.
    """

    def __init__(self, console_object, cleanup=None, DI_console_settings=DI_CONSOLE_IGNORE, is_thread=True):
        """
            Initialize the in-program console
            DI_CONSOLE_IGNORE
            DI_CONSOLE_INHERIT

        Raises:
            TypeError, AttributeError
        """

        if is_thread:
            threading.Thread.__init__(self)

        if isinstance(console_object, Console) == False:
            raise TypeError("Input object is not instance of class Console")
        if hasattr(cleanup, '__call__'):
            self.cleanup = cleanup
        else:
            self.cleanup = None
        self.console = console_object

        DI_init = None
        if isinstance(DI_console_settings, int):
            if DI_console_settings == DI_CONSOLE_IGNORE:
                DI_init = None
            elif DI_console_settings == DI_CONSOLE_INHERIT:
                DI_init = self.console.display_information_settings
            else:
                raise AttributeError("Argument 'DI_console_settings' integer flag values are "
                        "out of bounds. No valid flag.")
        elif isinstance(DI_console_settings, dict):
            DI_init = DI_console_settings
        else:
            raise TypeError("Argument 'DI_console_settings' is not of supported input types: "
                    "'int'(flags) or 'dict'")

        Display_Information.__init__(self, DI_init)

    def run(self):
        """thread
        """
        import sys

        do_loop = True
        parser = _Console_Parser()

        while do_loop:
            try:
                CI = Console_Input(self.console.display_information_settings)
                input_string = CI.get_input(" # ")
                input_list = input_string.split()
                if len(input_list) <= 0:

                    continue

                command_found = False
                for command in self.console._available_commands:
                    if command.command_name == input_list[0]:
                        command_found = True
                        parser.parse_line(command, input_string)
                        break

                if command_found:
                    self.console.command_active_flags = parser.get_active_flags()
                    self.console.command_additional_args = parser.get_additional_args()
                    self.console.command_name = command.command_name

                    do_exit = False
                    for map in self.console.command_active_flags:
                        if map["longf"] == "--help":
                            do_exit = True
                            break
                    if do_exit:
                        map["method"]()
                        continue

                    for map in self.console.command_active_flags:
                        self.console.current_flag_input = map['input']
                        self.console.current_flag_name = map['longf']
                        map['method']()

                    command.method()
                    if input_list[0] == "exit":
                        do_loop = False

                else:
                    string = "\nUnknown command '%s'. Type 'help' for available "\
                            "commands." % input_list[0]
                    sys.stdout.write(string)

            except (KeyboardInterrupt, SystemExit):
                if hasattr(self.cleanup, '__call__'):
                    self.cleanup()
                self.verbose("Terminating console due to system exception.")
                raise SystemExit
            except:
                self.console.clean() # TMP CODE: FIX
                raise

            if hasattr(self.cleanup, '__call__'):
                self.cleanup()

class Console_Input(Display_Information):
    """
        en.wikipedia.org/wiki/ANSI_escape_code
    """
    def __init__(self, DI_settings=None):
        Display_Information.__init__(self, DI_settings)
        self.history = []
        self.input_buffer = []
        self.input_index = 0
        self.TM = Terminal_Manipulator()
        self.TS = Terminal_Size()
        self.input_spanning_rows = 0
        self.last_column = 0

        self.start_column = None
        self.start_row = None
        self.start_height = None

    def erase_terminal_print(self):
        import sys

        if self.TS.refresh():
            #Terminal size is changed. All perviosuly stored start variables
            #may now be corrupted. Recalculate
            pass

        (curr_r, curr_c) = self.TM.get_cursor()
        height_diff = curr_r - (self.start_row + (self.TS.height - self.start_height))
        self.debug("Curr_r : %d. sr: %d. sh: %d. height: %d", curr_r, self.start_row,
                self.start_height, self.TS.height)
        self.debug("Height diff: %d", height_diff)
        i = 0
        while i < height_diff:
            self.TM.clear_line()
            i += 1
            self.TM.move_cursor_up()
            print "lol"
            self.debug("Cleared one line and moved up")
        return

        #Restore to old cursor pos
        esc_string = "\033["+str(self.start_row + height_diff)+";"+str(self.start_column)+"H"
        sys.stdout.write(esc_string)
        sys.stdout.write("\033[1K")     #Erase from start of line to cursor


        """Taught process. cases:

        - Cursor is at bottom of terminal: Unchanged size. No height difference.

        - Cursor in middle of terminal.Unchanged size. Height difference

        - Cursor in middle of termina. Changed size. Height difference and invalidating
          spanning_rows
        """

    def get_input(self, prompt=""):
        """TODO
        """
        import sys
        import tty, termios

        self.TS.refresh()
        self.start_height = self.TS.height
        (r, c) = self.TM.get_cursor()
        self.start_row = r
        self.start_column = c

        sys.stdout.write(prompt)
        self.last_column = 0
        self.spanning_rows = 0
        while True:
            while True:
                if self.TM.key_pressed():
                    char = self.TM.getch()
                    print "got ", [char]
                    break
            continue

            if self.TM.is_key(char, KEY.ARROW_UP):
                (r, c) = self.TM.get_cursor()
                self.debug("Row: %d", r)
                continue
            elif self.TM.is_key(char, KEY.ARROW_DOWN):
                sys.stdout.write("\r")
                print self.spanning_rows
                break
            elif self.TM.is_key(char, KEY.ARROW_LEFT):
                raise NotImplementedError
            elif self.TM.is_key(char, KEY.ARROW_RIGHT):
                raise NotImplementedError
            elif self.TM.is_key(char, KEY.END_OF_TEXT):
                raise NotImplementedError
            elif self.TM.is_key(char, KEY.END_OF_TRANSMISSION):
                raise NotImplementedError
            elif self.TM.is_key(char, KEY.BACKSPACE):
                self.erase_terminal_print()
             #   sys.stdout.write(prompt)
              #  sys.stdout.write("".join(self.input_buffer))
                continue
            elif self.TM.is_key(char, KEY.ENTER):
                return "".join(self.input_buffer)
            else:
                self.input_buffer.insert(self.input_index, char)
                self.input_index += 1

            sys.stdout.write(char)
            (curr_r, curr_c) = self.TM.get_cursor()
            if curr_c < self.last_column:
                self.spanning_rows += 1
            self.last_column = curr_c


class Terminal_Manipulator(object):
    """

    """
    def __init__(self):
        """todo
        """
        self._getch = None
        self.key_pressed = None
        self._getch_init()

    def _getch_init(self):
        try:
            #Is Windows
            import msvcrt
            self._getch = self._getch_windows
            self.key_pressed = self._key_pressed_windows
        except ImportError:
            pass

        try:
            import Carbon
            Carbon.Evt  #If attribute is present, its a mac
            self._getch = self._getch_mac
            self.key_pressed = self._key_pressed_linux #UNTESTED - MUST TEST
        except ImportError, AttributeError:
            pass

        self._getch = self._getch_linux
        self.key_pressed = self._key_pressed_linux

    def is_key(self, key, compare):
        """Compare the string input key (typically fetched raw from the keyboard stdin) if it
        is a match to intended compare keyboard key. The compare string is a defined string like
        "ARROW_UP" whilst the raw key input counterpart is ANSI escaped sequence.
        The comparison is done with both hex and octal string value for the ASCII *ESC* value.

        Args:
            - key (str): A string object holding to key input we wish to compare.
            - compare (str): Item in the **KEY** :meth:`Enum` set. Eg. KEY.KEY_TO_COMPARE.
              See all available **KEY** members.

        Returns:
            - **True** if raw input key equals the **KEY** literal
            - **False** if it doesnt.
        """

        if compare == KEY.ARROW_UP:
            if key == '\x1b[A' or key == '\033[A':
                return True
        elif compare == KEY.ARROW_DOWN:
            if key == '\x1b[B' or key == '\033[B':
                return True
        elif compare == KEY.ARROW_LEFT:
            if key == '\x1b[D' or key == '\033[D':
                return True
        elif compare == KEY.ARROW_RIGHT:
            if key == '\x1b[C' or key == '\033[D':
                return True
        elif compare == KEY.BACKSPACE:
            if key == '\x7f' or key == '\0177':
                return True
        elif compare == KEY.ENTER:
            if key == '\r':
                return True
        elif compare == KEY.END_OF_TEXT:
            if key == '\x03' or key == '\003':
                return True
        elif compare == KEY.END_OF_TRANSMISSION:
            if key == '\x04' or key == '\004':
                return True
        else:
            return False
    def _key_pressed_linux(self):
        """NOT A VIABLE WAY! TOO LAGGY INPUT. INPUT LOST
        """
        import select, sys, termios, tty

        #save old settings
        old_settings = termios.tcgetattr(sys.stdin)
        #set terminal in raw
        tty.setcbreak(sys.stdin.fileno())
        input = select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        return input

    def _key_pressed_windows(self):
        import msvcrt
        return msvcrt.kbhit()

    def scroll_up(self, n='1'):
        """Scroll current terminal line up n lines. Using a sys stdout ANSI escape sequence write
        """
        import sys
        string = "\033["+n+"S"
        sys.stdout.write(string)

    def scroll_down(self, n='1'):
        """Scroll current terminal line down n lines. Using a sys stdout ANSI escape sequence write
        """
        import sys
        string = "\033["+n+"T"
        sys.stdout.write(string)

    def clear_line(self):
        """Clear current terminal line with a sys stdout ANSI escape sequence write
        """
        import sys
        sys.stdout.write('\033[2K')

    def clear_terminal(self):
        """Clear the terminal with a sys stdout ANSI escape sequence write
        """
        import sys
        sys.stdout.write("\033[2J")
        sys.stdout.write("\033[1;1H")

    def move_cursor_back(self, n):
        """Move the cursor back n characters by writing a ANSI escape sequence to stdout
        """
        import sys
        ch = n
        if isinstance(n, int):
            ch = str(n)
        string = "\033["+ch+"D"
        sys.stdout.write(string)

    def move_cursor_forward(self, n):
        """Move the cursor forward n characters by writing a ANSI escape sequence to stdout
        """
        import sys
        ch = n
        if isinstance(n, int):
            ch = str(n)
        string = "\033["+ch+"C"
        sys.stdout.write(string)

    def move_cursor_up(self, n):
        """Move the cursor up n lines by writing a ANSI escape sequence to stdout.
        """
        import sys
        ch = n
        if isinstance(n, int):
            ch = str(n)
        string = "\033["+ch+"A"
        sys.stdout.write(string)

    def get_cursor(self):
        """Perform device status report to retrieve cursor pos
        Return:
            - (row, column) tuple
        """
        import sys
        sys.stdout.write("\033[6n")
        while True:
            ch = self.getch()
            if len(ch) == 0:
                raise ValueError("Failed to retrieve device status report. Returning ESC "\
                        "sequence was lost.")
            if ch[0] == "\x1b" or ch[0] == "\033":
                if ch[-1] == 'R':
                    #Identifier for return call from the Device Status Report
                    break

        row_string = ""
        column_string = ""
        index = 2
        while True:
            if ch[index] == ';':
                index += 1
                break
            row_string += ch[index]
            index += 1
        while True:
            if ch[index] == 'R':
                break
            column_string += ch[index]
            index += 1

        return (int(row_string), int(column_string))



    def getch(self):
        """
        """
        sequence = self._getch()
        if ord(sequence) == 27:   #decimal value for the ASCII ESC value
            sequence += self._getch()
            while True:
                ch = self._getch()
                sequence += ch
                if ord(ch) < 0x7e and ord(ch) > 0x40:
                    #Range of valid final byte in the escape sequence. Indicates the last byte
                    break
        return sequence

    def _getch_windows(self):
        import msvcrt
        print "WINDOWS GETCH EVENT HANDLER"
        raise NotImplementedError

    def _getch_linux(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    def _getch_mac(self):
        print "MAC GETCH EVENT HANDLER"
        raise NotImplementedError

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

        Raises:
            TypeError
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
                        type = "string"
                        if map["input"] == FLAG_INPUT_STR:
                            type = "str"
                        elif map["input"] == FLAG_INPUT_INT:
                            type = "int"
                        elif map["input"] == FLAG_INPUT_FLOAT:
                            type = "float"
                        raise InputError("Missing input for flag '%s'. Expecting %s ",
                                flag_name, type)

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


class _Print_Help_Command:
    """Assist class to pretty print command flags to the terminal
    """
    def __init__(self, command):
        self.command = command
        self.TS = Terminal_Size()
        self.lineoffset_desc = 0
        self.MIN_DESC_WIDTH = 20

    def _calculate_bounds(self):
        """Calculate the line offset at which description begins
        """
        self.lineoffset_desc = 0

        for flag in self.command.available_flags:
            line = self._get_flags_string(flag)
            if len(line) > self.lineoffset_desc:
                self.lineoffset_desc = len(line)

    def _get_flags_string(self, flag):
        """Assist function to get flag and input string,
        eg. -t --test  [float]
        """

        line = "  "
        if flag["shortf"] != None:
            line += flag["shortf"] + ", "
        line += flag["longf"] + "  "

        input = flag["input"]
        if input == FLAG_INPUT_STR:
            line += "[str]"
        elif input == FLAG_INPUT_INT:
            line += "[int]"
        elif input == FLAG_INPUT_FLOAT:
            line += "[float]"

        return line


    def print_flags(self):
        """Print all flags for this command to the terminal in the format:

        Usage: program_name [--flags] command.usage

        -f --flag [optiontype]      description
        """
        self._calculate_bounds()
        self.TS.refresh()
        self.lineoffset_desc += 7
        if (self.TS.width -self.lineoffset_desc) < self.MIN_DESC_WIDTH:
            print "Unable to write help options due to narrow terminal. Please expand it."
            tmp = self.lineoffset_desc + self.MIN_DESC_WIDTH
            print "Current width: %d. Minimum required width: %d" % (self.TS.width, tmp)
            return

        print "Usage: " + self.command.command_name + " [--flags] " +self.command.usage + "\n"
        for flag in self.command.available_flags:
            line = self._get_flags_string(flag)
            num_padd_chars = self.lineoffset_desc - len(line)

            line += ''.join([' ' for x in xrange(num_padd_chars)])
            token_list = flag['description'].split()
            line_length = len(line)
            for token in token_list:
                token_length = len(token)
                if line_length + token_length >= self.TS.width:
                    print line
                    line = ''.join([' ' for x in xrange(self.lineoffset_desc)])
                    line_length = self.lineoffset_desc
                line += token + " "
                line_length += token_length + 1
            print line


class Terminal_Size(object):
    """Return the terminal size. Works on Windows, Linux, OS X, Cygwin
    """
    def __init__(self):
        """
        Modules:
            platform
        """
        import platform

        self.width = 0
        self.height = 0
        self.current_os = platform.system()

        self.refresh()

    def refresh(self):
        """Perform a check for terminal size. Updates attributes self.width and self.height with
        new values.

        Returns:
            - **True** if terminal size has changed.
            - **False** if terminal size is unchanged.
        """
        is_changed = False
        (w, h) = self.get_terminal_size()
        if w != self.width:
            is_changed = True
            self.width = w
        if h != self.height:
            is_changed = True
            self.height = h

        return is_changed

    def get_terminal_size(self):
        """Return the terminal size in a tuple

        Returns:
            Tuple (width, height)
        """
        tuple_xy = None
        if self.current_os == 'Windows':
           tuple_xy = self._getTS_Windows()
           if tuple_xy is None:
              tuple_xy = self._getTS_tput()
              # needed for window's python in cygwin's xterm!
        if self.current_os == 'Linux' or self.current_os == 'Darwin' or  self.current_os.startswith('CYGWIN'):
           tuple_xy = self._getTS_Linux()

        if tuple_xy is None:
            tuple_xy = (80, 25)      # default value
        return tuple_xy


    def _getTS_Windows(self):
        """Return terminal size on Windows. Shamelessly stolen from the internet. Source: Unknown

        Modules:
            ctype.windll, ctype.create_string_buffer, struct
        """
        res = None
        try:
            from ctypes import windll, create_string_buffer

            # stdin handle is -10
            # stdout handle is -11
            # stderr handle is -12

            h = windll.kernel32.GetStdHandle(-12)
            csbi = create_string_buffer(22)
            res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
        except:
            return None
        if res:
            import struct
            (bufx, bufy, curx, cury, wattr,
             left, top, right, bottom, maxx, maxy) = struct.unpack("hhhhHhhhhhh", csbi.raw)
            sizex = right - left + 1
            sizey = bottom - top + 1
            return sizex, sizey
        else:
            return None

    def _getTS_tput(self):
        """Get terminal size from xterm. Shamelessly stolen from the internet. Source: Unknown

        Modules:
            subprocess
        """
        # get terminal width
        # src: http://stackoverflow.com/questions/263890/how-do-i-find-the-width-height-of-a-terminal-window
        try:
           import subprocess
           proc=subprocess.Popen(["tput", "cols"],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
           output=proc.communicate(input=None)
           cols=int(output[0])
           proc=subprocess.Popen(["tput", "lines"],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
           output=proc.communicate(input=None)
           rows=int(output[0])
           return (cols,rows)
        except:
           return None

    def _getTS_Linux(self):
        """Get terminal size from linux. Shamelessly stolen from the internet. Source: Unknown

        Modules:
            fcntl, termios, struct, os
        """
        def ioctl_GWINSZ(fd):
            try:
                import fcntl, termios, struct, os
                cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ,'1234'))
            except:
                return None
            return cr
        cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
        if not cr:
            try:
                fd = os.open(os.ctermid(), os.O_RDONLY)
                cr = ioctl_GWINSZ(fd)
                os.close(fd)
            except:
                pass
        if not cr:
            try:
                cr = (env['LINES'], env['COLUMNS'])
            except:
                return None
        return int(cr[1]), int(cr[0])

if __name__ == '__main__':
    c = Console({'debug':DI_LOG}, False, False)
    c.console_start(True, False)
