from TempMail import TempMail

tempmail = TempMail()

accounts = tempmail.create(1)

print(accounts)

watcher = tempmail.watch_for_mails()

for data in watcher:
    print(data)
