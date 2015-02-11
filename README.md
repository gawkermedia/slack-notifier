# slack-notifier



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