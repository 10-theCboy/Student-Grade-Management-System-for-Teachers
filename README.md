# Student Grade Management System

A web-based grade management system for teachers built with Python Flask and SQLite.

## Setup Instructions

1. Install dependencies: pip install -r requirements.txt
2. Run the application: py app.py
3. Open browser at http://127.0.0.1:5000
4. Default admin login: username=admin, password=admin123

## Running Tests

py -m pytest tests/ -v

## Repository Structure

- blueprints/ — Flask route handlers (auth, admin, teacher, student)
- models/ — Database model classes
- services/ — Business logic (grade calculation, CSV export, statistics)
- templates/ — Jinja2 HTML templates
- static/ — CSS, JavaScript, images
- tests/ — PyTest test suite
