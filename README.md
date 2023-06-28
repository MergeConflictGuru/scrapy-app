# scrapy-app

Scrapy Web Scraper and HTTP Server with Docker Compose

## Description

This project uses Scrapy framework to scrape the first 500 items (title, image URL) from sreality.cz (flats, sell) and saves it in a PostgreSQL database. It also implements a simple HTTP server in Python to display these items on a web page. The application is containerized using Docker Compose for easy deployment.

## Installation

1. Clone the GitHub repository.
2. Install Docker and Docker Compose.
3. Build and start the Docker containers using `docker-compose up`.
4. Access the web page at `http://127.0.0.1:8080`.

## Technologies Used

- Scrapy
- Selenium
- PostgreSQL
- Python
- Docker Compose

## License

This project is licensed under the MIT License.