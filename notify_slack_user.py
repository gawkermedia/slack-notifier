#!/usr/bin/env python

import sys
import os
import json
import re
import argparse
from slacker import Slacker
from github import Github
import requests
from jenkinsapi.jenkins import Jenkins
from jenkinsapi.utils.requester import Requester

requests.packages.urllib3.disable_warnings()


JENKINS_URL = os.environ['JENKINS_URL']
JENKINS_LOGIN = os.environ['JENKINS_LOGIN']
JENKINS_PASS = os.environ['JENKINS_PASS']
GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
SLACK_TOKEN = os.environ['SLACK_TOKEN']


def parse_github_url(url):
    ''' git@github.com:gawkermedia/kinja-mantle.git '''
    GITURL_REGEX = '((git|ssh|http(s)?)|(git@[\w\.]+))(:(//)?)([\w\.@\:/\-~]+)(\.git)(/)?'
    return re.split(GITURL_REGEX, url)[7].split('/')

def get_jenkins_job(job, build_number):
    ''' returns dict with repo info and commit shas '''
    j = Jenkins(
        JENKINS_URL,
        requester=Requester(
            JENKINS_LOGIN,
            JENKINS_PASS,
            baseurl=JENKINS_URL,
            ssl_verify=False
            )
        )

    repo = parse_github_url(j[job][build_number]._data['actions'][3]['remoteUrls'][0])

    changeset = j[job][build_number]._data['changeSet']['items']

    commit_ids = []
    for ch in changeset:
        commit_ids.append(ch['commitId'])

    return {
        'commit_ids': commit_ids,
        'repo': repo
    }

def get_github_users(repo, commit_ids):
    ''' get users from github for the give commit_ids in the repo '''
    g = Github(GITHUB_TOKEN)
    repo = g.get_user(repo[0]).get_repo(repo[1])

    users = []

    for sha in commit_ids:
        u = repo.get_commit(sha).author
        users.append({
            'login': u.login,
            'email': u.email,
            'name': u.name
        })

    return {u['login']:u for u in users}.values()

class Slack:
    def __init__(self):
        self.conn = Slacker(SLACK_TOKEN)


    def get_users(self, users):
        response = self.conn.users.list()
        user_list = response.body['members']

        matches = []
        for u in user_list:
            for gh_user in users:
                if u['profile']['real_name_normalized'].lower() == str(gh_user['name']).lower() or \
                    u['profile']['email'].lower() == str(gh_user['email']).lower() or \
                    u['name'].lower() == str(gh_user['login']).lower():
                    matches.append(u)

        return matches

    def send_message(self, users, msg):
        for u in users:
            self.conn.chat.post_message(u['id'], msg)
            print 'message (%s) sent to: %s' % (msg, u['name'])



def main():
    parser = argparse.ArgumentParser(description='sexy')
    parser.add_argument('--job', help='Jenkins job', required=True)
    parser.add_argument('--build', help='build number', required=True, type=int)
    parser.add_argument('--msg', help='message to send', required=True)
    args = parser.parse_args()

    print '************************'

    changeset = get_jenkins_job(args.job, args.build)
    print 'changeset: %s' % changeset
    gh_users = get_github_users(changeset['repo'], changeset['commit_ids'])
    print 'github users: %s' % gh_users

    s = Slack()

    slack_users = s.get_users(gh_users)

    if len(slack_users) is 0:
        print '%s not found in slack' % gh_users
        sys.exit(0)

    print 'slack matches: %s ' % slack_users
    s.send_message(slack_users, args.msg)

    print '************************'



if __name__ == '__main__':
  main()
