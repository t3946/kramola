## Run command

You can run all services by
```docker-compose up```

or you can start server and run redis the way as you wish.
```python -m flask run --host=127.0.0.1 --port=5000```

## Admin panel (MySQL, users, roles)

1. Install dependencies: `pip install -r requirements.txt`
2. Create MySQL database and set `.env`: `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`
3. Create tables: `flask db init` (once), `flask db migrate -m "initial"`, `flask db upgrade`
4. Create first admin: `flask create-admin --username admin --password <password> --email admin@example.com`
5. Open `/admin/`, log in with that user. Only users with role **admin** can access the panel.
