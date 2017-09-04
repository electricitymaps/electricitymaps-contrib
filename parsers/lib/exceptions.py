

class ParserException(Exception):

    def __init__(self, parser, message):

        # Call the base class constructor with the parameters it needs
        super(ParserException, self).__init__(message)

        # Now for your custom code...
        self.parser = parser

    def __str__(self):
        return "{0} Parser: {1}".format(self.parser, self.message)
