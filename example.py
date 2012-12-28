from src import console

class MyProgram(console.Console):

    def __init__(self):
        console.Console.__init__(self)

    def terminal_init(self):
        """Must override in order to add custom flags
        """
        self.terminal_add_flag("--example", "-e", "Awkwardly long terminal flag, i mean\
                common. How come you need this long description for a simple flag?",
                input=console.FLAG_INPUT_INT)
        #Works with and without the leading dashes for the long and shot flag markers.
        self.terminal_add_flag("custom", "c", "This flag supplies its own custom method!",
                method=self.custom_method)

        #Method will be default flag handler, description empty
        self.terminal_quickadd_flags(["test", "more"], "?m")

    def default_flag_handler(self):
        """Must override in order to handle all flags defiend with None method handler
        """
        print "Default flag handler for flag '%s', with input: %s" % (self.current_flag_name, \
                self.current_flag_input)

    def custom_method(self):
        """Custom method handler
        """
        print "Custom method flag handler for flag '%s'" % self.current_flag_name


    def custom_command_method(self):
        """Custom command method handler
        """
        print "Custom command handler for command '%s'" % self.current_command_name

if __name__ == '__main__':
    import time
    c = MyProgram()
    #At this point, the program has parsed all flags present at terminal line and executed their
    #flag handler.

    #Add custom commands for the in-program console
    command = c.console_add_command("example", c.custom_command_method, "My in-program command",
            "<input_file> <output_file>")
    command.add_flag("example-flag", "f")

    #Start the in-program console
    shutdown = c.console_start(threaded=True, daemon=False)
    try:
        while 1:
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown.set()

