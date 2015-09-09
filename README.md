# Introduction

Designate is an OpenStack inspired DNSaaS.

Docs: http://docs.openstack.org/developer/designate and some below for now.
Bugs / Blueprints: http://launchpad.net/designate

IRC: #openstack-dns

Installation: http://docs.openstack.org/developer/designate/getting-started.html

# Development
Designate follows the [OpenStack Gerrit Workflow](http://docs.openstack.org/infra/manual/developers.html#development-workflow)

## Setup
Setup a working environment:

````
git clone https://github.com/openstack/designate.git
cd designate
virtualenv .venv
. .venv/bin/activate
pip install -r requirements.txt -r test-requirements.txt
python setup.py develop
````

## Building the documentation
To build the documentation from the restructured text source, do the following:
````
cd doc
pip install -r requirements.txt
sphinx-build  source/ build/html/
````
now point your browser at html/index.html
(the official documentation is published to [docs.openstack.org](http://docs.openstack.org/developer/designate) by the
maintainers.


## Contributing
Install the git-review package to make life easier

````
pip install git-review
````

Branch, work, & submit:

````
# cut a new branch, tracking master
git checkout --track -b bug/id origin/master
# work work work
git add stuff
git commit
# rebase/squash to a single commit before submitting
git rebase -i
# submit
git-review
````

## Testing

Execute a single test using py27 (test is CentralServiceTest.test_count_domains)
````
tox -e py27 -- designate/tests/test_central/test_service.py:CentralServiceTest.test_count_domains
````
