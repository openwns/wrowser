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

import Database as db
import wrowser.Configuration as conf


def getCampaignsDict():
    config = conf.Configuration()
    config.read()
    db.Database.connectConf(config)
    db.Database.showAllCampaigns()
    cursor = db.Database.getCursor()
    cursor.execute('SELECT user_name, full_name, campaigns.id, title, description, ' \
                   'pg_size_pretty(db_use), pg_size_pretty(db_quota), pg_size_pretty(db_size) ' \
                   'FROM users LEFT JOIN campaigns ON users.id = campaigns.user_id')
    campaignsList = cursor.fetchall()
    cursor.execute('SELECT DISTINCT campaign_id FROM administration.authorizations ' \
                   'WHERE authorized_id IN ' \
                   '(SELECT group_id FROM administration.group_members WHERE ' \
                   'user_id = (SELECT id FROM administration.users WHERE user_name = \'%s\')) ' \
                   'OR authorized_id = (SELECT id FROM administration.users WHERE user_name = \'%s\')' % (config.userName, config.userName))
    authorizedCampaignIdList = [e[0] for e in cursor.fetchall()]
    cursor.connection.commit()
    campaignsDict = {}
    for line in campaignsList:
        if not campaignsDict.has_key('%s (%s, db use: %s, quota: %s)' % (line[1], line[0], line[5], line[6])):
            campaignsDict['%s (%s, db use: %s, quota: %s)' % (line[1], line[0], line[5], line[6])] = dict()
        authorization = False
        if line[2] in authorizedCampaignIdList:
            authorization = True
        campaignsDict['%s (%s, db use: %s, quota: %s)' % (line[1], line[0], line[5], line[6])][line[2]] = (line[3], line[4], line[7], authorization)
    return campaignsDict


def setCampaign(campaign):
    if len(campaign) != 1:
        raise 'To many campaigns!'
    db.Database.viewCampaigns(campaign)
