import os
import sys
import pwd
import ConfigParser


class Configuration(object):

    def __init__(self):
        self.parser = ConfigParser.SafeConfigParser()
        self.dbAccessConfFile = os.path.join(os.environ['HOME'], '.wns', 'dbAccess.conf')


    def read(self, filename = ''):
        if os.stat(self.dbAccessConfFile)[0] & 1023 != 384:
            print >>sys.stderr, 'Wrong file access permissions to \'%s\'. ' \
                  'Due to security reasons only the owner of the file must have read/write access. ' \
                  'Consider changing the database password if unauthorized people might have become aware of it.'
            sys.exit(1)
        self.parser.read([self.dbAccessConfFile, filename])

        if 'DB' in self.parser.sections():
            if 'host' in self.parser.options('DB'):
                setattr(self, 'dbHost', self.parser.get('DB', 'host'))
            else:
                print >>sys.stderr, 'Host name is missing in config file!'
                sys.exit(1)
            if 'name' in self.parser.options('DB'):
                setattr(self, 'dbName', self.parser.get('DB', 'name'))
            else:
                print >>sys.stderr, 'Database name is missing in config file!'
                sys.exit(1)
        else:
            print >>sys.stderr, 'Section \'DB\' is missing in config file!'
            sys.exit(1)

        if 'User' in self.parser.sections():
            if 'name' in self.parser.options('User'):
                setattr(self, 'userName', self.parser.get('User', 'name'))
            else:
                print >>sys.stderr, 'User name is missing in config file!'
                sys.exit(1)
            if 'password' in self.parser.options('User'):
                setattr(self, 'userPassword', self.parser.get('User', 'password'))
            else:
                print >>sys.stderr, 'Password is missing in config file!'
                sys.exit(1)
        else:
            print >>sys.stderr, 'Section \'User\' is missing in config file!'
            sys.exit(1)

        if 'Campaign' in self.parser.sections():
            if 'id' in self.parser.options('Campaign'):
                setattr(self, 'campaignId', int(self.parser.get('Campaign', 'id')))
            else:
                print >>sys.stderr, 'Campaign id is missing in config file!'
                sys.exit(1)


    def writeDbAccessConf(self, home, user):
        dbAccessConfFile = os.path.join(home, '.wns', 'dbAccess.conf')
        if 'DB' not in self.parser.sections():
            self.parser.add_section('DB')

        self.parser.set('DB', 'host', getattr(self, 'dbHost'))
        self.parser.set('DB', 'name', getattr(self, 'dbName'))

        if 'User' not in self.parser.sections():
            self.parser.add_section('User')

        self.parser.set('User', 'name', getattr(self, 'userName'))
        self.parser.set('User', 'password', getattr(self, 'userPassword'))

        config = file(dbAccessConfFile, 'w')
        config.write('# Keep this file private. Do NOT change file access permissions. Security hazard!\n\n')
        self.parser.write(config)
        config.close()
        os.chown(dbAccessConfFile, pwd.getpwnam(user)[2], pwd.getpwnam(user)[3])
        os.chmod(dbAccessConfFile, 0600)


    def writeCampaignConf(self, filename):
        if 'Campaign' not in self.parser.sections():
            self.parser.add_section('Campaign')

        self.parser.set('Campaign', 'id', str(getattr(self, 'campaignId')))

        config = file(filename, 'w')
        config.write('# Do NOT edit this file manually!\n\n')
        self.parser.write(config)
        config.close()
        os.chmod(filename, 0644)
