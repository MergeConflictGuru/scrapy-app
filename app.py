from flask import Flask
import pg8000
import os
import logging

app = Flask(__name__)


@app.route('/')
def index():
    try:
        conn = pg8000.connect(
            host='db',
            port=5432,
            user=os.environ['POSTGRES_USER'],
            password=os.environ['POSTGRES_PASSWORD'],
            database=os.environ['POSTGRES_DB']
        )
        cursor = conn.cursor()

        # Check if the table exists
        cursor.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'property_table')")
        table_exists = cursor.fetchone()[0]

        if table_exists:
            cursor.execute("SELECT title, image_url, url FROM property_table LIMIT 500")
            items = cursor.fetchall()
        else:
            items = []

        conn.close()

        if not items:
            return 'Please run the scraper first'

        html = ''
        for item in items:
            title, image_url, url = item
            html += f'<h2><a href="{url}">{title}</a></h2>'
            html += f'<img src="{image_url}" alt="{title}">'
            html += '<hr>'

        return html
    except pg8000.Error as e:
        logging.error('Error connecting to the database: %s', str(e))
        return 'Internal Server Error', 500
    except Exception as e:
        logging.error('Unhandled error occurred: %s', str(e))
        return 'Internal Server Error', 500


if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    app.run(host='0.0.0.0', port=8080)
