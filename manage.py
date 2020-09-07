#!/usr/bin/env python
import os
from app import create_app, db
from flask_script import Manager, Shell, Server
from flask_migrate import Migrate, MigrateCommand

cur_app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(cur_app)
migrate = Migrate(cur_app, db)


def make_shell_context():
    return dict(app=cur_app, db=db)


manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)
manager.add_command("runserver", Server(use_debugger=True))


@manager.command
def test():
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


if __name__ == '__main__':
    manager.run()
    # cur_app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
