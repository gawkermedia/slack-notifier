#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pytest
import notify_slack_user as n

jenkins_testdata = [
    {
        'name': 'empty changeset',
        'job': 'kinja-core',
        'build': 5921,
        'commit_num': 0,
        'author_num': 0
        'authors': [],
        'slack_users': [],
        'expected_matches': 0
    },
    {
        'name': 'multiple sha one author',
        'job': 'kinja-mantle',
        'build': 14671,
        'commit_num': 3,
        'author_num': 1,
        'authors': ['chrisneveu'],
        'slack_users': ['chrisneveu'],
        'expected_matches': 1
    },
    {
        'name': 'single sha',
        'job': 'puppet',
        'build': 3239,
        'commit_num': 1,
        'author_num': 1,
        'authors': ['dominis'],
        'slack_users': ['dominis'],
        'expected_matches': 1
    },
    {
        'name': 'empty fileds no matches overflow',
        'job': 'kinja-mantle',
        'build': 14675,
        'commit_num': 1,
        'author_num': 1,
        'authors': ['tiborbotos'],
        'slack_users': ['tiborbotos'],
        'expected_matches': 1
    },
    {
        'name': 'single sha utf8 name',
        'job': 'kinja-profile',
        'build': 959,
        'commit_num': 1,
        'author_num': 1,
        'authors': ['balagez'],
        'slack_users': ['zoli'],
        'expected_matches': 1
    },
    {
        'name': 'multiple sha multiple author',
        'job': 'kinja-mantle',
        'build': 14487,
        'commit_num': 22,
        'author_num': 2,
        'authors': ['dataface', 'eteleilles'],
        'slack_users': ['eteleilles', 'kellymonson'],
        'expected_matches': 2
    },
]

@pytest.mark.parametrize("input", jenkins_testdata)
def test_responses(input):
    j = jenkins_result(input['job'], input['build'])
    if input['commit_num'] == 0:
        assert(j) == None
    else:
        assert len(j['commit_ids']) == input['commit_num']
        input['jenkins_response'] = j
        github_reponse(input)


def github_reponse(input):
    g = n.get_github_users(input['jenkins_response']['repo'], input['jenkins_response']['commit_ids'])
    assert len(g) == input['author_num']
    for commit in g:
        assert commit['login'] in input['authors']

    input['gh_response'] = g
    slack_response(input)

def slack_response(input):
    s = n.Slack()
    matches = s.search(input['gh_response'])
    assert len(matches) == input['expected_matches']

    for match in matches:
        assert match['login'] in input['slack_users']


def jenkins_result(job, build):
    return n.get_jenkins_job(job, build)

def test_parse_github_url():
    assert n.parse_github_url('git@github.com:user/repo.git') == ['user', 'repo']


