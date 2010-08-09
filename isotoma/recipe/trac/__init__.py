import os
import sys
import ConfigParser
import shutil

import pkg_resources
import zc.buildout
import zc.recipe.egg

from trac.admin.console import TracAdmin

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
        shutil.move(trac_ini, global_ini)

        parser = ConfigParser.ConfigParser()
        
        # Enable the components we want
        components_to_enable = options.get('components_enabled', "").strip().split()
        components_to_disable = options.get('components_disabled', "").strip().split()
        # if we don't already have this section, add it
        if (components_to_enable or components_to_disable) and 'components' not in parser.sections():
                parser.add_section('components')
                
        # add the compone
        for component in components_to_enable:
            parser.set('components', component, 'enabled')
        for component in components_to_disable:
            parser.set('components', component, 'disabled')
    
        # add the inheritance line
        parser.add_section('inherit')
        parser.set('inherit', 'file', global_ini)

        parser.write(open(trac_ini, 'w'))

    def update(self):
        pass
