from decouple import config as config_decouple
from flask import Flask

#app = Flask(__name__)

#if __name__ == '__main__':
#    app.run()


def create_app(enviroment):
    app = Flask(__name__)

    app.config.from_object(enviroment)

    return app

enviroment = config['development']
if config_decouple('PRODUCTION', default=False):
    enviroment = config['production']

if __name__ == '__main__':
    app = create_app(enviroment)
    app.run()