import re

 #checks if password has at least one capital and at least one number, and is of length 7   
class FormNotValidError(Exception):
    pass

capital_re = re.compile('[A-Z]+')
number_re = re.compile('[0-9]+')
space_re = re.compile('[\s]+')
special_re = re.compile('[\W]+')

def check_password(password):
    try:
        assert len(password) > 7
        assert capital_re.search(password) is not None
        assert number_re.search(password) is not None
        assert space_re.search(password) is None
        assert special_re.search(password) is None
    except AssertionError:
        raise FormNotValidError("Your password must be greater than 7 characters, must contain one capital letter, must have at least one number, and cannot have any special characters except '_'")

def check_special_and_spaces(name):
    try:
        assert space_re.search(name) is None
        assert special_re.search(name) is None
    except AssertionError:
        raise FormNotValidError("No spaces or special characters except '_' allowed")

"""special_characters = ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '-', '_', '=', '+', '[]', '{}', '<>', '?', '/', '.', '\\', '|', ':', ';']
for special_character in special_characters:
    print special_re.search('pspaspa%s' % special_character), special_character"""
    
    
    