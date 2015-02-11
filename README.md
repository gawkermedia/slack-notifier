# slack-notifier

1. gets the job details from jenkins
2. gets the users contributed to the build from github
3. try to resolve their slack id based on github login, name or email
4. sends them a private msg

## Install
```
virtualenv .venv
source bin/activate
pip install -r requirements.txt
```

## Usage
```
$ export JENKINS_URL='http://jenkins.default.com/'
$ export JENKINS_LOGIN='your_login'
$ export JENKINS_PASS='your_password'
$ export GITHUB_TOKEN='token'
$ export SLACK_TOKEN='token'

python notify_slack_user.py --job your_jenkins_job --build 1231 --msg "Your build just started"
```