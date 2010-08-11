import os
import sys
import ConfigParser
import shutil

import pkg_resources
import zc.buildout
import zc.recipe.egg

from trac.admin.console import TracAdmin

wsgi_template = """
%%(relative_paths_setup)s
import sys
import os
sys.path[0:0] = [
  %%(path)s,
  ]
  
  
%%(initialization)s
import trac.web.main
os.environ['PYTHON_EGG_CACHE'] = '%(egg_cache)s'

import trac.db.postgres_backend
trac.db.postgres_backend.PostgreSQLConnection.poolable = False

def application(environ, start_response):
    environ['trac.env_path'] = '%(env_path)s'
    return trac.web.main.dispatch_request(environ, start_response)

"""

class Recipe(object):

    def __init__(self, buildout, name, options):
        self.buildout, self.name, self.options = buildout, name, options

        options['location'] = os.path.join(
            buildout['buildout']['parts-directory'],
            self.name
            )

        options['bin-directory'] = buildout['buildout']['bin-directory']
        options['executable'] = sys.executable
        
        # gather the eggs that we need
        eggs = options.get('eggs', '').strip().split()
        
        self.egg = zc.recipe.egg.Scripts(buildout, name, {
                    "eggs": "\n".join(["Trac", "isotoma.recipe.trac", ]  + eggs),
                    })

    def install(self):
        options = self.options

        # create our run scripts
        entry_points = [('trac-admin', 'trac.admin.console', 'run'),
                        ('tracd', 'trac.web.standalone', 'main')]

        zc.buildout.easy_install.scripts(
                entry_points, pkg_resources.working_set,
                options['executable'], options['bin-directory']
                )
    
        # create the trac instance
        location = options['location']
        project_name = options.get('project-name', 'trac-project')
        project_name = '"%s"' % project_name
        project_url = options.get('project-url', 'http://example.com')
        if not options.has_key('db-type') or options['db-type'] == 'sqlite':
            db = 'sqlite:%s' % os.path.join('db', 'trac.db')
        elif options['db-type'] == 'postgres':
            db_options = {  'user': options['db-username'], 
                            'pass': options['db-password'], 
                            'host': options.get('db-host', 'localhost'), 
                            'port': options.get('db-port', '5432')
                         }
            db = 'postgres://%(user)s:%(pass)s@%(host)s:%(port)s' % db_options

        repos_type = options.get('repos-type', "")
        repos_path = options.get('repos-path', "")

        if not os.path.exists(location):
            os.mkdir(location)

        trac = TracAdmin(location)
    
        if not trac.env_check():
            trac.do_initenv('%s %s %s %s' % (project_name, db, repos_type, repos_path))
        
        # install the eggs that we need
        self.egg.install()
        
        # move the generated config out of the way so we can inherit it
        trac_ini = os.path.join(location, 'conf', 'trac.ini')
        global_ini = os.path.join(location, 'conf', 'global.ini')

        # move the existing config
        if not os.path.exists(global_ini):
            shutil.move(trac_ini, global_ini)

        parser = ConfigParser.ConfigParser()
    
        parser.add_section('inherit')

        # get the config file we're setting from
        if options.has_key('config-file'):
            local_config = os.path.join(self.buildout['buildout']['directory'], options.get('config-file'))
            parser.set('inherit', 'file', ','.join([local_config, global_ini]))
        else:
            parser.set('inherit', 'file', global_ini)

        parser.write(open(trac_ini, 'w'))

        if options.has_key('wsgi') and options['wsgi'].lower() == 'true':
            self.install_wsgi()

        # buildout expects a tuple of paths, but we don't have any to add
        # just return an empty one for now.
        return tuple()

    def update(self):
        pass

    def install_wsgi(self):
        """ Instal the wsgi script for running from apache """
        _script_template = zc.buildout.easy_install.script_template
        
        zc.buildout.easy_install.script_template = wsgi_template % {'env_path': self.options['location'], 'egg_cache': self.buildout['buildout']['eggs-directory']}
        requirements, ws = self.egg.working_set(['isotoma.recipe.trac'])
        
        zc.buildout.easy_install.scripts(
                [(self.name + '.wsgi', 'isotoma.recipe.trac.wsgi', 'main')],
                ws,
                sys.executable,
                self.options['bin-directory']
                )
        zc.buildout.easy_install.script_template = _script_template
        
        return True

    update = install
