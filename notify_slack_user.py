#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import re
import argparse
from slacker import Slacker
from github import Github
import requests
from jenkinsapi.jenkins import Jenkins
from jenkinsapi.utils.requester import Requester
from unidecode import unidecode
import logging

requests.packages.urllib3.disable_warnings()


JENKINS_URL = os.environ['JENKINS_URL']
JENKINS_LOGIN = os.environ['JENKINS_LOGIN']
JENKINS_PASS = os.environ['JENKINS_PASS']
GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
SLACK_TOKEN = os.environ['SLACK_TOKEN']


def parse_github_url(url):
    ''' git@github.com:user/repo.git '''
    GITURL_REGEX = '((git|ssh|http(s)?)|(git@[\w\.]+))(:(//)?)([\w\.@\:/\-~]+)(\.git)(/)?'
    return re.split(GITURL_REGEX, url)[7].split('/')


def get_jenkins_job(job, build_number):
    ''' returns dict with repo info and commit shas '''
    j = Jenkins(
        JENKINS_URL,
        requester=Requester(
            JENKINS_LOGIN,
            JENKINS_PASS,
            ssl_verify=False
            )
        )

    try:
        repo = parse_github_url(j[job][build_number]._data['actions'][3]['remoteUrls'][0])
    except KeyError:
        repo = ""

    try:
        if repo == "":
            repo = parse_github_url(j[job][build_number]._data['actions'][4]['remoteUrls'][0])

        changeset = j[job][build_number]._data['changeSet']['items']
    except KeyError:
        return None

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
        out = {}
        out['github_id'] = u.id
        out['login'] = u.login
        out['email'] = u.email
        out['name'] = unidecode(unicode(u.name)) 
        users.append(dict((k, str(v).lower()) for k, v in out.items() if v and v is not None))

    return dict((u['login'], u) for u in users).values()


class Slack:
    def __init__(self):
        self.conn = Slacker(SLACK_TOKEN)
        self.users = self.get_users()

    def get_users(self):
        response = self.conn.users.list()
        user_list = response.body['members']

        users = []
        for u in user_list:
            out = {}
            out['slack_id'] = u.get('id')
            out['login'] = unidecode(unicode(u.get('name')))
            out['email'] = u.get('profile').get('email')
            out['name'] = unidecode(unicode(u.get('profile').get('real_name_normalized')))
            users.append(dict((k, str(v).lower()) for k, v in out.items() if v))

        return users

    def send_message(self, users, msg):
        for u in users:
            self.conn.chat.post_message(u['slack_id'].upper(), msg)
            print 'message (%s) sent to: %s' % (msg, u['name'])

    def search(self, gh_users):
        matches = []
        for u in self.users:
            for uu in gh_users:
                shared_items = set(u.items()) & set(uu.items())
                if shared_items:
                    matches.append(u)

        return matches


def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    logging.getLogger("requests").setLevel(logging.WARNING)
    parser = argparse.ArgumentParser(description='sexy')
    parser.add_argument('--job', help='Jenkins job', required=True)
    parser.add_argument('--build', help='build number', required=True, type=int)
    parser.add_argument('--msg', help='message to send', required=True)
    parser.add_argument('--dry-run', help='dry run', dest='dryrun', action='store_true')
    args = parser.parse_args()

    logging.info('args %s' % args)

    changeset = get_jenkins_job(args.job, args.build)
    if changeset is None:
        logging.info('empty changeset')
        sys.exit(0)
    logging.info('changeset: %s' % changeset)
    gh_users = get_github_users(changeset['repo'], changeset['commit_ids'])
    logging.info('github users: %s' % gh_users)

    s = Slack()

    results = s.search(gh_users)

    if len(results) is 0:
        logging.info('no match: %s' % gh_users)
        sys.exit(0)

    logging.info('slack matches: %s ' % [u['name'] for u in results])
    if args.dryrun is False:
        s.send_message(results, args.msg)


if __name__ == '__main__':
    main()
