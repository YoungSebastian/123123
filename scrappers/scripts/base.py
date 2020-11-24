import os
import psycopg2

class Base:

    HOST     = os.environ.get('POSTGRES_HOST', 'localhost')
    PORT     = os.environ.get('POSTGRES_PORT', '5432')
    DBNAME   = os.environ.get('POSTGRES_DBNAME', 'postgres')
    USER     = os.environ.get('POSTGRES_USER', 'postgres')
    PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'Kutas123')

    HEADERS = {
        'Accept': '*/*', 'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36', 
        'Accept-Language': 'en-US;q=0.5,en;q=0.3', 'Cache-Control': 'max-age=0', 'Upgrade-Insecure-Requests': '1'
    }

    def __init__(self):
        self.conn = psycopg2.connect(
            dbname=self.DBNAME,
            user=self.USER,
            host=self.HOST,
            port=self.PORT,
            password=self.PASSWORD
        )
        self.c = self.conn.cursor()
        self.c.execute("""CREATE TABLE IF NOT EXISTS work(
            id SERIAL PRIMARY KEY,
            title TEXT,
            skills JSON,
            category TEXT,
            seniority JSON,
            url TEXT UNIQUE,
            working_places JSON,
            salary_from INTEGER,
            salary_to INTEGER,
            salary_type TEXT,
            salary_currency CHAR(3),
            online_interview BOOLEAN,
            company_name TEXT DEFAULT NULL,
            company_city TEXT DEFAULT NULL,
            company_street TEXT DEFAULT NULL, 
            company_latitude REAL DEFAULT NULL,
            company_longtitude REAL DEFAULT NULL,
            article_added DATE DEFAULT NULL,
            article_renewed DATE DEFAULT NULL,
            regions JSON DEFAULT NULL,
            description TEXT DEFAULT NULL,
            is_active BOOLEAN DEFAULT TRUE
        )""")