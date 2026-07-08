# mini-rag-app

Implement a minimal implementation of the RAG model for question answering

## Requirements

- Python 3.8 or later

### Install Python using MiniConda


1) Download and install MiniConda from here (https://www.anaconda.com/docs/getting-started/miniconda/main#advanced-install-options)

2) Create a new virtual environment using the following command:

```bash
$ conda -n create [name your environment] python=3.8
```
3) Activate the environment

```bash
$ conda -activate [name your environment]
```

### (Optional) setup your command line interface for better readability

```bash
export PS1="\[\033[01;32m\]\u@\h:\w\n\[\033[00m\]\$"
```

## Installation

### Install the required packages

```bash
pip install -r requirements.txt
```

### Setup the environment variables

```bash
cp .env.example .env
```

- Set **your** environment variables in the '.env' file. Like `OPENAI_API_KEY` value.

### Run Docker Compose Services

'''bash
$ cd docker
$ cp .env.example .env
'''

- update `.env` with your credentials in **.env** file, found in docker directory

'''bash
$ cd docker
$ sudo docker compose up -d
'''

### Run the FastAPI server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 5000
```