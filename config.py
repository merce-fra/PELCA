import git

repo = git.Repo('.')
tags = repo.tags

last_commit = repo.head.commit

for tag in tags:
    if tag.commit == last_commit:
        latest_tag = tag
        break
        


LATEST_TAG = latest_tag

with open('version.txt', 'w') as f:
    f.write(str(LATEST_TAG))

print(f'Latest tag: {LATEST_TAG}')