# Calibre Cron Job

This document provides a step-by-step guide on how to set up and use the project. It covers environment setup, dependencies, Docker usage, and other relevant instructions.

---

## Prerequisites

Before setting up the project, ensure you have the following installed on your system:

1. **Python 3.9 or later**
2. **Docker**
3. **Poetry** (for dependency management)
4. **AWS CLI**
5. **Git**

---

## Project Structure

- `calibre_cron_job/`: Contains the main application code.
- `cdk/`: AWS CDK infrastructure-as-code definitions.
- `Dockerfile`: Instructions to build the Docker image.
- `Makefile`: Contains common project commands.
- `poetry.lock`: Locked dependencies for Poetry.
- `pyproject.toml`: Project and dependency configuration for Poetry.
- `requirements.txt`: List of dependencies for Dockerfile (generated from Poetry).

---

## Project Setup

### 1. Clone the Repository

```bash
git clone git@github.com:alperozaydin/calibre-cron-job.git
cd calibre-cron-job
```

### 2. Set Up Environment Variables

The project uses a `.env` file to manage environment variables. Create a `.env` file in the root directory with the required variables:

```env
SENDER_EMAIL=<your-email>
SENDER_PASSWORD=<your-password>
RECIPIENT_EMAIL=<recipient-email>
AWS_ACCOUNT_ID=<your-aws-account-id>
```

> Replace placeholders with actual values. This file includes sensitive information.

### 3. Install Dependencies

The project uses Poetry for dependency management. Install the dependencies:

```bash
make init
```

This command will create `requirements.txt` file as well for `Dockerfile`.

---

## Running the Project


To run the container on local

```bash
make run
```

Build the Docker Container for AWS ECR

```bash
make build
```

Push Docker Container to AWS ECR
```bash
make push
```


---

## AWS CDK Deployment

Install AWS CDK

### 1. Install AWS CDK

Ensure AWS CDK is installed:

```bash
npm install -g aws-cdk
```

Deploy the CDK stack:

```bash
make deploy
```

---

## Notes

- Assumes that there is already ECR Repo named `calibre-cron-job`
- Ensure the `.env` file is not committed to version control. Add it to `.gitignore` or encrypt it
- Use `git-crypt` to encrypt sensitive files if working in a collaborative environment.
- Feel free to change recipe with any other built-in recipe in Calibre 

---

