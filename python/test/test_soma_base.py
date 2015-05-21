from load_pilots import load_pilots
import soma

error_message = """

##################################
#           GAME OVER            #
##################################

              +---+
              |   |
              O   |
             /|\  |
             / \  |
                  |
            =========
"""

valid_message = """

##################################
#        MODULE TEST PASSED      #
##################################

              +---+
              |   |
                  |
                  | \O/
                  |  |
                  | / \\
           ==============
            """


def run_all_tests():
    """ Execute all the unitests.

    Returns
    -------
    is_valid : bool
        True if all the tests are passed successfully,
        False otherwise.
    """
    module_path = soma.__path__[0]
    tests = load_pilots(module_path, module_path)

    is_valid = True
    for module, ltest in tests.items():
        for test in ltest:
            is_valid = is_valid and test()

    return is_valid


def is_valid_module():
    is_valid = run_all_tests()
    if is_valid:
        print valid_message
    else:
        print error_message


if __name__ == "__main__":
    is_valid_module()