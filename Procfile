web: gunicorn app:app --log-file -
init: python db_changes/db_create.py
teardown: python db_changes/db_teardown.py
