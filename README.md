#Email Parser
##Setup
1. First clone the repo `git clone https://github.com/amelehy/email_parse.git`
2. Navigate to the project directory `cd email_parse`
3. Create a new virtual environment `virtualenv env` (if you don't have virtualenv on your machine you can install it globally with `sudo pip install virtualenv`)
4. If changes haven't been merged and you want to see the development branch, run this: `git checkout -b development` and then `git pull origin development`
5. Now to install the necessary libraries run `env/bin/pip install -r requirements.txt`
6. You're all set! Just run `env/bin/python main.py <your choice of domain>` and you'll see all emails that were parsed from the domain you passed as well as pages linked to from the home page

*Note* 
There is a `MAX_URLS_TO_VISIT` value that you can adjust in `main.py` that will determine how many secondary urls are visited (the recursive nature of this use case can cause an endless number of urls to be visited if `MAX_URLS_TO_VISIT` is too large)

###Example
``` bash
env/bin/python main.py mit.edu
```