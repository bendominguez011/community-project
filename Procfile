web: gunicorn app:app --log-file -
init: python db/db_dev_create.py
teardown: python db/db_teardown.py
