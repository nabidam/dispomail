from dispomail import Dispomail

tempmail = Dispomail()

accounts = tempmail.create(1)

print(accounts)

watcher = tempmail.watch_for_mails()

for data in watcher:
    print(data)
