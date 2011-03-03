import os
import sys

import pkg_resources
import zc.buildout
import zc.recipe.egg

from trac.admin.console import TracAdmin
import trac.admin.console

try:
    import json
except:
    import simplejson as json

import warnings
warnings.filterwarnings('ignore', '.*', UserWarning, 'Cheetah.Compiler', 1508)
from Cheetah.Template import Template

wsgi_template = """
%%(relative_paths_setup)s
import sys
import os
sys.path[0:0] = [
  %%(path)s,
  ]
  
sys.stdin = sys.stderr
  
%%(initialization)s
import trac.web.main
os.environ['PYTHON_EGG_CACHE'] = '%(egg_cache)s'

def application(environ, start_response):
    environ['trac.env_path'] = '%(env_path)s'
    return trac.web.main.dispatch_request(environ, start_response)

"""

meta_wsgi_template = """
%%(relative_paths_setup)s
import sys
import os
sys.path[0:0] = [
  %%(path)s,
  ]
  
sys.stdin = sys.stderr
  
%%(initialization)s
import trac.web.main
os.environ['PYTHON_EGG_CACHE'] = '%(egg_cache)s'
os.environ['TRAC_ENV_PARENT_DIR'] = '%(env_path)s'

def application(environ, start_response):
    return trac.web.main.dispatch_request(environ, start_response)

"""

testrunner_template = """#!/usr/bin/env python
%%(relative_paths_setup)s
import sys
import os
sys.path[0:0] = [
  %%(path)s,
  ]
  
  
%%(initialization)s
# monkey patch to our generated python
sys.executable = '%(python_path)s'

#import the tests
from trac.test import suite
import unittest

# run the tests
unittest.main(defaultTest = 'suite')

"""

custom_trac_ini_template = """# DO NOT REMOVE THIS COMMENT - BUILDOUT
[inherit]
file = %s

"""

meta_trac_ini_template = """# DO NOT REMOVE THIS COMMENT - BUILDOUT
[inherit]
file = %(base_file_path)s

[project]
admin_trac_url = .
name = %(project_name)s

"""

class Recipe(object):

    def write_config(self, config_file_name, template_file_name, opt):
        template = open(template_file_name).read()
        c = Template(template, searchList = opt)
        open(config_file_name, "w").write(str(c))

    def write_custom_config(self, config_file_name, base_file_path, meta = False, meta_vars = None):
        
        # don't overwrite it, we only want to create it once
        existing = open(config_file_name, 'r').read()
        if existing.split()[0] != "# DO NOT REMOVE THIS COMMENT - BUILDOUT":
            newini = open(config_file_name, 'w')
            if meta:
                data = {'base_file_path': base_file_path}
                data.update(meta_vars)
                newini.write(meta_trac_ini_template % data)
            else:
                newini.write(custom_trac_ini_template % base_file_path)
            newini.close()


    def __init__(self, buildout, name, options):
        self.buildout, self.name, self.options = buildout, name, options

        options['location'] = os.path.join(
            buildout['buildout']['directory'],
            os.path.join('var',self.name)
            )

        options['bin-directory'] = buildout['buildout']['bin-directory']
        options['executable'] = sys.executable
        
        # gather the eggs that we need
        eggs = options.get('eggs', '').strip().split()
        
        self.egg = zc.recipe.egg.Scripts(buildout, name, {
                    "eggs": "\n".join(["Trac", "isotoma.recipe.trac", ]  + eggs),
                    })
        
        if options.get('metamode', "") and options['metamode'].lower() == 'true':
            self.metamode = True
        else:
            self.metamode = False

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
                            'db': options.get('db-name', 'trac'), 
                            'port': options.get('db-port', '5432')
                         }
            db = 'postgres://%(user)s:%(pass)s@%(host)s:%(port)s/%(db)s' % db_options

        repos_type = options.get('repos-type', "")
        repos_path = options.get('repos-path', "")

        if not os.path.exists(location):
            os.makedirs(location)

        print "Creating Trac Instance in: " + location

        
        
        # install the eggs that we need
        self.egg.install()
        
        if self.metamode:
            # put the config file somewhere so we can inherit it
            self._write_ini(os.path.join(location, 'base_trac.ini'), db, {'location': location})
            
            instances = self._get_instances()
            for instance, data in instances.iteritems():
                # we need a new location for each project
                meta_location = os.path.join(self.buildout['buildout']['directory'], 'var', self.name, instance)
                trac = TracAdmin(meta_location)
                if not trac.env_check():
                    trac.do_initenv('%s %s %s %s' % (instance, db, repos_type, repos_path))
                    data.update({'project_name': instance})
                    self.write_custom_config(os.path.join(meta_location, 'conf', 'trac.ini'), 
                                             os.path.join(location, 'base_trac.ini'),
                                             meta = True,
                                             meta_vars = data)
            
        else:
            trac = TracAdmin(location)
            
            if not trac.env_check():
                trac.do_initenv('%s %s %s %s' % (project_name, db, repos_type, repos_path))
        
            self._write_ini(os.path.join(location, 'conf', 'base_trac.ini'), db, self.options)
            self.write_custom_config(os.path.join(location, 'conf', 'trac.ini'), os.path.join(location, 'conf', 'base_trac.ini'))

        if options.has_key('wsgi') and options['wsgi'].lower() == 'true':
            self.install_wsgi(options['location'])
            
        if options.has_key('testrunner') and options['testrunner'].lower() == 'true':
            self.install_testrunner()

        self.install_htpasswd()

        # buildout expects a tuple of paths, but we don't have any to add
        # just return an empty one for now.
        return tuple()
    
    def _write_ini(self, location, db, options):
        # move the generated config out of the way so we can inherit it
        trac_ini = location

        # parse the options to pass into our template
        template_options = self.options['config-template-options']
        template_options = json.loads(template_options)
        
        template_options['site_url'] = options.get('site-url', "")
        template_options['log_directory'] = options.get('log-directory', "")
        template_options['trac_location'] = options['location']

        template_options['database_dsn'] = db

        self.write_config(trac_ini, self.options['base-config'], template_options)
        
    def _get_instances(self):
        """ Get the instances and their options from buildout """
        instance_list = [instance.strip() for instance in self.options['instances'].split(',')]
        
        data = {}
        
        for instance in instance_list:
            data[instance] = self.buildout[instance]
            
        return data
        

    def update(self):
        pass

    def install_wsgi(self, location):
        """ Instal the wsgi script for running from apache """
        _script_template = zc.buildout.easy_install.script_template
        
        if self.metamode:
            zc.buildout.easy_install.script_template = meta_wsgi_template % {'env_path': location, 'egg_cache': self.buildout['buildout']['eggs-directory']}
        else:
            zc.buildout.easy_install.script_template = wsgi_template % {'env_path': location, 'egg_cache': self.buildout['buildout']['eggs-directory']}
        requirements, ws = self.egg.working_set(['isotoma.recipe.trac'])
        
        zc.buildout.easy_install.scripts(
                [(self.name + '.wsgi', 'isotoma.recipe.trac.wsgi', 'main')],
                ws,
                sys.executable,
                self.options['bin-directory']
                )
        zc.buildout.easy_install.script_template = _script_template
        
        return True

    def install_testrunner(self):
        """ This will install a test runner that will run the default trac tests. It relies on the zc.recipe.egg interpreter being present at bin-directory/python """
        """ Instal the wsgi script for running from apache """
        _script_template = zc.buildout.easy_install.script_template
        
        zc.buildout.easy_install.script_template = testrunner_template % {'python_path': self.buildout['buildout']['bin-directory'] + '/python'}
        requirements, ws = self.egg.working_set(['isotoma.recipe.trac'])
        
        zc.buildout.easy_install.scripts(
                [('testrunner', 'isotoma.recipe.trac.testrunner', 'main')],
                ws,
                sys.executable,
                self.options['bin-directory']
                )
        zc.buildout.easy_install.script_template = _script_template
        
        return True

    def install_htpasswd(self):
        """ Install a default htpasswd file if one doesn't already exist """
        if os.path.exists(os.path.join(self.options['location'], 'passwords.db')):
            return
        
        if not self.options.has_key('initial_username'):
            return

        passwords = open(os.path.join(self.options['location'], 'passwords.db'), 'w')
        passwords.write(self.options['initial_username'] + ':' + self.options['initial_user_password'])
        passwords.close()

        # grant admin permissions to the new user
        args = [self.options['location'], 'permission', 'add', self.options['initial_username'], 'TRAC_ADMIN']
        trac.admin.console.run(args)
    
    update = install
