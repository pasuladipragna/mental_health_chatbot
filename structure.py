import os

def print_structure(start_path='.', prefix=''):
    for item in os.listdir(start_path):
        path = os.path.join(start_path, item)
        print(prefix + '|-- ' + item)
        if os.path.isdir(path):
            print_structure(path, prefix + '   ')

print_structure('.')
