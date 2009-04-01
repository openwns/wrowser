#! /usr/bin/python

###############################################################################
# This file is part of openWNS (open Wireless Network Simulator)
# _____________________________________________________________________________
#
# Copyright (C) 2004-2007
# Chair of Communication Networks (ComNets)
# Kopernikusstr. 16, D-52074 Aachen, Germany
# phone: ++49-241-80-27910,
# fax: ++49-241-80-22242
# email: info@openwns.org
# www: http://www.openwns.org
# _____________________________________________________________________________
#
# openWNS is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License version 2 as published by the
# Free Software Foundation;
#
# openWNS is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

import getpass
import pwd
import os
import sys

def searchPath(path, rootSign):
	while rootSign not in os.listdir(path):
		if path == os.sep:
			return None
		path, tail = os.path.split(path)
	path, tail = os.path.split(path)
	return os.path.abspath(path)

sys.path.append(searchPath(os.path.abspath(os.path.dirname(sys.argv[0])), 'Configuration.py'))

#import wrowser.Configuration as config
import wrowser.simdb.Database as db

hostname = 'localhost'
dbName = 'simdb'
fullName = pwd.getpwnam(userName)[4]
password = 'foobar'

postgresPassword = getpass.getpass('Please enter the password of the \'postgres\' super user: ')
db.Database.connect(dbName, hostname, 'postgres', postgresPassword)

userName = getpass.getuser()
curs = db.Database.getCursor()
curs.execute('SELECT * FROM administration.users WHERE user_name = \'%s\'' % userName)
if len(curs.fetchall()) != 0:
        print >>sys.stderr, 'User with user name \'%s\' already exists.' % userName
        sys.exit(1)

curs.execute('INSERT INTO administration.users (user_name, full_name, password, group_account) VALUES (\'%s\', \'%s\', \'%s\', \'%s\')' % (userName, fullName, password, False))
curs.connection.commit()

# configuration file is written by the wrowser!
#conf = config.Configuration()
#conf.dbHost = hostname
#conf.dbName = dbName
#conf.userName = userName
#conf.userPassword = password
#conf.writeDbAccessConf(home = os.path.join('/', 'home', userName), user = userName)

print 'User successfully created.'
