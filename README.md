# Drssed API

Backend REST API for **Drssed**, a personal wardrobe management app that digitizes clothing and outfits using automated image processing and categorization.

This repository contains the server-side implementation. The iOS frontend is maintained separately: [drssed-ios](https://github.com/davidriegel/drssed-ios)

---

## Features

- **User management** — registration, login, JWT-based authentication
- **Wardrobe management** — create, read, update and delete clothing items per user
- **Outfit management** — combine items into outfits, store and retrieve them
- **Image processing** — background removal and automated categorization of clothing images
- **Category system** — structured data model for clothing types, colors and tags

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3 |
| Framework | Flask |
| Database | MySQL |
| Auth | JWT |
| Server | Gunicorn |

---

## Setup Instructions

### Requirements
- Python == 3.12.*
- MySQL Server
- Redis Server (for rate limiting)


## Environment Variables

See `.env.example` for all required variables:

```env
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_NAME=DATABASE_NAME
DATABASE_USERNAME=DATABASE_USERNAME
DATABASE_PASSWORD=DATABASE_PASSWORD

SECRET_TOKEN_KEY=SECRET_KEY_VALUE_FOR_JWT_AUTHENTICATION

RATELIMITER_ENABLED=True
REDIS_URI=redis://localhost:6379

LOG_LEVEL=INFO
```

---

## Related

- **iOS App** → [davidriegel/drssed-ios](https://github.com/davidriegel/drssed-ios)
- **Portfolio** → [davidriegel.dev](https://davidriegel.dev)

---

## About the Project

Drssed started as a personal project to solve a real problem: losing track of what clothes you own. It grew into a full-stack application with a custom backend, a relational database, image processing features and a native iOS app.

---