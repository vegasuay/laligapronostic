from decouple import config as config_decouple
from flask import Flask

def create_app(enviroment):
    app = Flask(__name__)

    app.config.from_object(enviroment)

    return app

enviroment = config_decouple['development']
if config_decouple('PRODUCTION', default=False):
    enviroment = config_decouple['production']

if __name__ == '__main__':
    app = create_app(enviroment)
    app.run()